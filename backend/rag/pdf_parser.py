"""PhysioWave — PDF Parser.

Extracts text from clinical PDFs and splits into overlapping chunks
for the RAG embedding pipeline.

Uses PyMuPDF (fitz) — the fastest Python PDF library, with robust support
for complex layouts, tables, and multi-column text common in medical textbooks.
"""

import os
import base64
from dataclasses import dataclass

import fitz  # PyMuPDF

from backend.core.config import settings
from backend.core.logger import logger


@dataclass
class DocumentChunk:
    """A parsed and chunked segment of a clinical document."""
    text: str
    source_file: str
    page_number: int
    chunk_index: int
    document_type: str  # 'clinical_guide' or 'equipment_manual'


# ─── PDF Asset Definitions ──────────────────────────────────────────
# Uploaded PDFs will be managed via the /api/rag/upload endpoint.


def extract_and_chunk(
    file_path: str,
    document_type: str = "clinical_guide",
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    extract_images: bool = True,
    on_progress: typing.Callable[[int, int], None] | None = None,
    check_cancelled: typing.Callable[[], bool] | None = None,
    start_page: int = 0,
    existing_chunks: list["DocumentChunk"] | None = None,
    on_page_complete: typing.Callable[[int, list["DocumentChunk"]], None] | None = None,
) -> list[DocumentChunk]:
    """Extract text from a PDF and split into overlapping chunks.

    Args:
        file_path: Absolute path to the PDF file.
        document_type: Classification ('clinical_guide' or 'equipment_manual').
        chunk_size: Characters per chunk (default from settings).
        chunk_overlap: Overlap between chunks (default from settings).

    Returns:
        List of DocumentChunk objects.
    """
    cs = chunk_size or settings.chunk_size
    co = chunk_overlap or settings.chunk_overlap
    filename = os.path.basename(file_path)

    logger.info(f"Starting PDF extraction: {filename}")

    try:
        doc = fitz.open(file_path)
    except Exception as e:
        logger.error(f"Failed to open PDF {filename}: {e}")
        raise ValueError(f"Cannot open PDF: {e}") from e

    chunks: list[DocumentChunk] = list(existing_chunks) if existing_chunks else []
    chunk_index = len(chunks)  # Continue numbering from where we left off

    if start_page > 0:
        logger.info(f"Resuming parsing from page {start_page + 1}/{len(doc)} (skipping {start_page} cached pages)")

    for page_num in range(len(doc)):
        current_page = page_num + 1
        total_pages = len(doc)
        
        # Skip pages already parsed in a previous run
        if page_num < start_page:
            continue
        
        # Check for cancellation/shutdown before each page
        if check_cancelled and check_cancelled():
            logger.warning(f"Parsing cancelled at page {current_page}/{total_pages}. Saving progress.")
            # Save progress before exiting so we can resume
            if on_page_complete:
                on_page_complete(page_num, chunks)
            doc.close()
            return []  # Return empty to signal cancellation (chunks are saved to cache)
        
        # Log every page to terminal for "alive" confirmation
        logger.info(f"  [PDF Parser] Analyzing Page {current_page}/{total_pages}...")
        
        # Throttle DB updates to every 5 pages to reduce SQLite contention
        if on_progress and (current_page % 5 == 0 or current_page == total_pages):
            on_progress(current_page, total_pages)
            
        page = doc[page_num]
        text = page.get_text("text").strip()

        if not text or len(text) < 50:
            continue

        # Split page text into overlapping chunks
        page_chunks = _chunk_text(text, cs, co)

        for chunk_text in page_chunks:
            if len(chunk_text.strip()) < 50:
                continue

            chunks.append(
                DocumentChunk(
                    text=chunk_text.strip(),
                    source_file=filename,
                    page_number=page_num + 1,
                    chunk_index=chunk_index,
                    document_type=document_type,
                )
            )
            chunk_index += 1

        # Extract and describe images
        if extract_images:
            for img_index, img_data in enumerate(page.get_images(full=True)):
                xref = img_data[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Skip tiny artifacts/icons
                if len(image_bytes) < 2048:
                    continue
                    
                # Resize image to prevent Ollama resource crash (Status 500)
                try:
                    from io import BytesIO
                    from PIL import Image
                    with Image.open(BytesIO(image_bytes)) as img:
                        if img.mode != "RGB":
                            img = img.convert("RGB")
                        img.thumbnail((800, 800), Image.Resampling.LANCZOS)
                        buffer = BytesIO()
                        img.save(buffer, format="JPEG", quality=85)
                        image_bytes = buffer.getvalue()
                        base_image["ext"] = "jpg"
                except Exception as e:
                    logger.warning(f"Failed to resize image, continuing with original: {e}")
                    
                # Read vision model desc
                b64_image = base64.b64encode(image_bytes).decode("utf-8")
                from backend.rag.embeddings import extract_image_description
                description = extract_image_description(b64_image)
                
                if description and len(description.strip()) > 30:
                    # Store local copy for debug/records
                    img_filename = f"{filename}_page{page_num+1}_img{img_index}.{base_image['ext']}"
                    img_path = os.path.join("./backend/data/extracted_images", img_filename)
                    with open(img_path, "wb") as fh:
                        fh.write(image_bytes)
                    
                    chunks.append(
                        DocumentChunk(
                            text=f"[Diagram/Image Info]: {description}",
                            source_file=filename,
                            page_number=page_num + 1,
                            chunk_index=chunk_index,
                            document_type=document_type,
                        )
                    )
                    chunk_index += 1

        # Save parsing checkpoint every 5 pages for crash recovery
        if on_page_complete and (current_page % 5 == 0 or current_page == total_pages):
            on_page_complete(current_page, chunks)

    page_count = len(doc)
    doc.close()

    logger.info(f"Chunked {filename} into {len(chunks)} chunks ({page_count} pages)")
    return chunks


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into overlapping chunks, breaking at sentence boundaries."""
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        if end > len(text):
            end = len(text)

        # Try to break at sentence boundary
        if end < len(text):
            last_period = text.rfind(".", start + chunk_size // 2, end)
            if last_period > start:
                end = last_period + 1

        chunks.append(text[start:end])
        
        new_start = end - overlap
        
        # Prevent infinite loop if overlap is too large relative to the chunk segment
        if new_start <= start:
            start += max(1, chunk_size // 4)  # Step forward forcefully
        else:
            start = new_start

    return chunks



