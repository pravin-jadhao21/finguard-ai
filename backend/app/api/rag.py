from fastapi import APIRouter
from app.schemas.rag import RAGRequest, RAGResponse
from app.core.rag_guard import SecureRAGGuard

router = APIRouter()
_rag_guard = SecureRAGGuard()


@router.post(
    "/rag/retrieve",
    response_model=RAGResponse,
    summary="Secure Pre-Context RAG Document Retrieval & Access Control"
)
async def secure_rag_retrieve(request: RAGRequest):
    """
    Retrieves candidate RAG documents and enforces pre-context access control:
    - Filters unauthorized public vs restricted customer documents
    - Denies access safely if permission metadata is missing/invalid
    - Prevents cross-customer document leakage
    - Scans for indirect prompt injection/poisoning in retrieved text
    - Returns XML-encapsulated safe context block and zero-data-leakage audit log
    """
    return _rag_guard.process_rag_request(request)
