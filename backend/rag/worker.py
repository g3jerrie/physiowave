"""PhysioWave — RAG Background Worker Pipeline.

This module replaces uncontrolled FastApi BackgroundTasks with a robust, sequential, 
crash-recoverable background queue.
"""

import asyncio
import traceback
from datetime import datetime, timezone
import anyio

from backend.core.config import settings
from backend.core.logger import logger
from backend.core.database import get_db
from backend.rag.pipeline import ingest_document

class RAGWorker:
    def __init__(self):
        self.is_running = False
        self._task = None

    async def start(self):
        """Start the background worker loop."""
        self.is_running = True
        logger.info("RAG Worker queue started...")
        
        # Cleanup "zombie" jobs from previous crash
        await self._cleanup_zombie_jobs()
        
        while self.is_running:
            try:
                await self._process_next()
            except Exception as e:
                logger.error(f"RAG Worker unexpected fault: {e}")
            
            # Poll every 3 seconds for new jobs
            await asyncio.sleep(3)

    async def _cleanup_zombie_jobs(self):
        """Find jobs hung in 'processing' and reset them to 'pending' for retry."""
        db = await get_db()
        try:
            cursor = await db.execute("SELECT id FROM ingestion_status WHERE status IN ('processing', 'parsing')")
            zombies = await cursor.fetchall()
            if zombies:
                logger.info(f"Found {len(zombies)} hung jobs. Resetting to pending...")
                for z in zombies:
                    await db.execute("UPDATE ingestion_status SET status = 'pending' WHERE id = ?", (z["id"],))
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to cleanup zombie jobs: {e}")
        finally:
            await db.close()

    async def stop(self):
        """Gracefully shutdown the worker."""
        self.is_running = False
        if self._task:
            self._task.cancel()
        logger.info("RAG Worker queue stopped.")

    async def _process_next(self):
        """Check for pending or interrupted uploads and process one."""
        db = await get_db()
        try:
            # Look for pending files (sequential FIFO)
            cursor = await db.execute("SELECT * FROM ingestion_status WHERE status = 'pending' ORDER BY id ASC LIMIT 1")
            row = await cursor.fetchone()
            
            if not row:
                return
            
            # Convert Row to dict for safe .get() access
            job = dict(row)
            job_id = job["id"]
            file_path = f"{settings.upload_dir}/{job['filename']}"
            extract_images = bool(job["extract_images"])
            safe_mode = bool(job.get("safe_mode", 0))
            
            logger.info(f"Worker picked up Job {job_id} ({job['filename']}). Status: {job['status']} (SafeMode: {safe_mode})")
            
            # We let the pipeline.py handle the status update to 'parsing' internally.
            # No status update here to avoid pre-emptively marking 'processing' before parsing starts.


            # The ingestion pipeline now supports seeking if ingested_chunks > 0, handled internally by pipeline.py
            def check_cancelled():
                from backend.main import is_shutting_down
                if is_shutting_down: 
                    return True
                # Actually query sync connection to check if user deleted it
                import sqlite3
                conn = sqlite3.connect(settings.database_url.replace("sqlite:///", ""))
                try:
                    cur = conn.cursor()
                    cur.execute("SELECT status FROM ingestion_status WHERE id = ?", (job_id,))
                    row = cur.fetchone()
                    return row is None or row[0] == "cancelled"
                finally:
                    conn.close()

            # Execute Heavy Lifting
            try:
                chunks_ingested = await anyio.to_thread.run_sync(
                    ingest_document, 
                    file_path, 
                    "clinical_guide", 
                    job_id,  # Passed for DB progress callbacks
                    check_cancelled,
                    extract_images,
                    safe_mode
                )
                
                # Verify if it was cancelled during processing
                cursor = await db.execute("SELECT status FROM ingestion_status WHERE id = ?", (job_id,))
                row = await cursor.fetchone()
                if row and row[0] == "cancelled":
                    return # Natural abort
                
                completed_at = datetime.now(timezone.utc).isoformat()
                await db.execute(
                    "UPDATE ingestion_status SET status = 'complete', completed_at = ? WHERE id = ?",
                    (completed_at, job_id),
                )
                await db.commit()
                logger.info(f"Worker finished Job {job_id}")
                
            except asyncio.CancelledError:
                logger.info(f"Ingestion {job_id} cancelled (Shutdown).")
                await db.execute(
                    "UPDATE ingestion_status SET status = 'cancelled', completed_at = ? WHERE id = ?",
                    (datetime.now(timezone.utc).isoformat(), job_id),
                )
                await db.commit()
                # Do NOT raise here, we want the worker loop to shutdown gracefully naturally
            
            except Exception as e:
                error_tb = traceback.format_exc()
                logger.error(f"Worker failed on Job {job_id}:\n{error_tb}")
                await db.execute(
                    "UPDATE ingestion_status SET status = 'failed', error_message = ?, completed_at = ? WHERE id = ?",
                    (str(e), datetime.now(timezone.utc).isoformat(), job_id),
                )
                await db.commit()
                
        finally:
            await db.close()

worker_instance = RAGWorker()
