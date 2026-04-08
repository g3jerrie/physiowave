"""PhysioWave — PDF Parser.

Extracts text from clinical PDFs and splits into overlapping chunks
for the RAG embedding pipeline.

Uses PyMuPDF (fitz) — the fastest Python PDF library, with robust support
for complex layouts, tables, and multi-column text common in medical textbooks.
"""

import os
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

PDF_ASSETS = [
    {
        "filename": "Physiotherapy_Combi_5in1_Machine_User_Manual.pdf",
        "document_type": "equipment_manual",
        "display_name": "Combi 5-in-1 User Manual",
    },
    {
        "filename": "Lakshmi-NarayananTextbook-of-THERAPEUTIC-EXERCISES.pdf",
        "document_type": "clinical_guide",
        "display_name": "Therapeutic Exercises Textbook",
    },
    {
        "filename": "The_Anatomy_of_Stretching,_Second_Edition_Your_Illustrated_Guide.pdf",
        "document_type": "clinical_guide",
        "display_name": "Anatomy of Stretching",
    },
    {
        "filename": "Therapeutic-exercise.-Foundations-and-techniques-by-Colby-Lynn-Allen-Kisner-Carolyn-z-lib.org_.pdf",
        "document_type": "clinical_guide",
        "display_name": "Therapeutic Exercise: Foundations",
    },
    {
        "filename": "textbook of electrotherapy.pdf",
        "document_type": "equipment_manual",
        "display_name": "Textbook of Electrotherapy",
    },
]


def extract_and_chunk(
    file_path: str,
    document_type: str = "clinical_guide",
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
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

    chunks: list[DocumentChunk] = []
    chunk_index = 0

    for page_num in range(len(doc)):
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

    doc.close()

    logger.info(f"Chunked {filename} into {len(chunks)} chunks ({len(doc)} pages)")
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
        start = end - overlap

        if start <= 0 and len(chunks) > 1:
            break

    return chunks


def get_all_pdf_paths() -> list[dict]:
    """Return full paths for all PDF assets."""
    assets_dir = settings.assets_dir
    result = []
    for asset in PDF_ASSETS:
        path = os.path.join(assets_dir, asset["filename"])
        if os.path.exists(path):
            result.append({**asset, "path": path})
        else:
            logger.warning(f"PDF asset not found: {path}")
    return result
