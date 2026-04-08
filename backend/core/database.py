"""PhysioWave — SQLite Database.

HIPAA Compliance Note: Patient PII fields are encrypted before storage
via the security module. Non-PII fields (age, gender, risk factors) are
stored in plaintext for efficient querying.

All data is stored locally — no external database connections.
"""

import aiosqlite
import os
from pathlib import Path

DATABASE_PATH = "./data/physiowave.db"

# ─── Schema ────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS patients (
    id TEXT PRIMARY KEY,
    age INTEGER,
    gender TEXT,
    risk_factors TEXT,  -- JSON array of risk factor strings
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS patient_pii (
    patient_id TEXT PRIMARY KEY,
    encrypted_name TEXT,        -- AES-256 encrypted
    encrypted_dob TEXT,         -- AES-256 encrypted
    encrypted_phone TEXT,       -- AES-256 encrypted
    encrypted_email TEXT,       -- AES-256 encrypted
    encrypted_address TEXT,     -- AES-256 encrypted
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    symptoms TEXT,
    vitals TEXT,                -- JSON object
    diagnosis TEXT,
    therapy_used TEXT,
    machine_settings TEXT,      -- JSON object
    duration_minutes INTEGER,
    pain_score_before INTEGER,  -- VAS 0-10
    pain_score_after INTEGER,   -- VAS 0-10
    ai_suggestion_id TEXT,
    applied_protocols TEXT,     -- JSON array
    notes TEXT,
    status TEXT DEFAULT 'active',  -- active, completed, cancelled
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ai_suggestions (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    query TEXT NOT NULL,
    suggestion TEXT NOT NULL,
    source_chunks TEXT,         -- JSON array of source references
    is_safe INTEGER NOT NULL DEFAULT 1,
    warning_message TEXT,
    blocked_protocols TEXT,     -- JSON array
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,       -- e.g., 'patient_created', 'suggestion_generated'
    entity_type TEXT,           -- e.g., 'patient', 'session'
    entity_id TEXT,
    details TEXT,               -- Non-PII details only
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ingestion_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    chunks_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, processing, complete, failed
    error_message TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT
);
"""


async def get_db() -> aiosqlite.Connection:
    """Get an async database connection."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    db = await aiosqlite.connect(DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db():
    """Initialize the database schema."""
    db = await get_db()
    try:
        await db.executescript(SCHEMA)
        await db.commit()
    finally:
        await db.close()
