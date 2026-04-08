"""PhysioWave — RAG Management Router."""

from fastapi import APIRouter, BackgroundTasks

from backend.models.schemas import SearchRequest, SearchResultItem
from backend.rag.pipeline import ingest_all_documents, semantic_search
from backend.rag.vector_store import get_document_count

router = APIRouter(prefix="/rag", tags=["RAG Pipeline"])


@router.post("/ingest")
async def ingest_documents(background_tasks: BackgroundTasks):
    """Trigger PDF ingestion pipeline (runs in background).

    Extracts text from all PDF assets, generates embeddings,
    and stores in the ChromaDB vector store.
    """
    background_tasks.add_task(ingest_all_documents)
    return {
        "status": "ingestion_started",
        "message": "PDF ingestion is running in the background.",
    }


@router.post("/ingest/sync")
async def ingest_documents_sync():
    """Trigger PDF ingestion pipeline (synchronous — waits for completion)."""
    result = ingest_all_documents()
    return {
        "status": "complete",
        **result,
    }


@router.post("/search", response_model=list[SearchResultItem])
async def search_knowledge_base(request: SearchRequest):
    """Perform semantic search against the clinical knowledge base."""
    results = semantic_search(
        query=request.query,
        top_k=request.top_k,
        document_type=request.document_type,
    )

    return [
        SearchResultItem(
            content=r["content"],
            score=r["score"],
            source_file=r["source_file"],
            page_number=r.get("page_number"),
            document_type=r.get("document_type"),
        )
        for r in results
    ]


@router.get("/status")
async def rag_status():
    """Get RAG pipeline status."""
    count = get_document_count()
    return {
        "total_chunks": count,
        "is_ingested": count > 0,
    }
