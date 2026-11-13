import re
import time
import uuid
from typing import List, Tuple, Optional
from app.core.rag_store import RAGDocumentStore
from app.schemas.rag import (
    RAGRequest,
    RAGResponse,
    RAGDocument,
    DocumentClassification,
    AccessDecision,
    DocumentAccessAuditLog
)


class SecureRAGGuard:
    """
    Deterministic Pre-Context Secure RAG Pipeline & Access Control Gateway.
    Filters unauthorized documents before LLM context construction,
    validates metadata, enforces cross-customer isolation, and scans
    retrieved text for indirect prompt injection/poisoning.
    """

    # Malicious Indirect Prompt Injection / Poisoning Regex
    POISONED_INSTRUCTION_RE = re.compile(
        r'(?i)(?:system\s+override|ignore\s+(?:all\s+)?previous\s+instructions|print\s+out\s+all|exfiltrate|send\s+.*?\s+to\s+http|assistant:\s*you\s+must|bypass\s+security\s+policy)\b'
    )

    def __init__(self, document_store: Optional[RAGDocumentStore] = None):
        self.doc_store = document_store or RAGDocumentStore()

    def process_rag_request(self, request: RAGRequest) -> RAGResponse:
        """
        Executes pre-context security pipeline on candidate documents.
        Returns typed RAGResponse containing sanitized context block and audit logs.
        """
        start_time = time.perf_counter()
        req_id = f"rag-{uuid.uuid4().hex[:12]}"
        query = request.query
        user_context = request.user_context

        # Fetch top-k candidate documents from store
        candidates = self.doc_store.search_candidates(query, top_k=request.top_k)

        authorized_docs: List[RAGDocument] = []
        audit_logs: List[DocumentAccessAuditLog] = []

        for doc in candidates:
            meta = doc.metadata

            # --- STEP 1: Metadata Validation & Completeness Check ---
            if not meta.classification or not meta.permitted_roles:
                audit_logs.append(
                    DocumentAccessAuditLog(
                        doc_id=meta.doc_id,
                        title=meta.title,
                        classification=str(meta.classification) if meta.classification else None,
                        access_decision=AccessDecision.DENIED_INVALID_METADATA,
                        reason_code="RAG_ACCESS_DENIED_MISSING_OR_INVALID_METADATA"
                    )
                )
                continue

            # --- STEP 2: Role Authorization Check ---
            is_admin = (user_context.user_role == "Admin")
            if user_context.user_role not in meta.permitted_roles and not is_admin:
                audit_logs.append(
                    DocumentAccessAuditLog(
                        doc_id=meta.doc_id,
                        title=meta.title,
                        classification=meta.classification.value,
                        access_decision=AccessDecision.DENIED_ROLE,
                        reason_code=f"RAG_ACCESS_DENIED_ROLE_NOT_PERMITTED: Role '{user_context.user_role}' not allowed"
                    )
                )
                continue

            # --- STEP 3: Customer Ownership & Cross-Customer Isolation ---
            if meta.classification == DocumentClassification.RESTRICTED_CUSTOMER:
                is_compliance = (user_context.user_role == "ComplianceOfficer")
                # Must match owner_id unless requester is Admin or ComplianceOfficer
                if meta.owner_id and meta.owner_id != user_context.user_id and not (is_admin or is_compliance):
                    audit_logs.append(
                        DocumentAccessAuditLog(
                            doc_id=meta.doc_id,
                            title=meta.title,
                            classification=meta.classification.value,
                            access_decision=AccessDecision.DENIED_OWNER,
                            reason_code=f"RAG_ACCESS_DENIED_CROSS_CUSTOMER_ISOLATION: Requested doc owner '{meta.owner_id}' does not match user '{user_context.user_id}'"
                        )
                    )
                    continue

            # --- STEP 4: Untrusted Text Indirect Injection & Poisoning Scan ---
            if self.POISONED_INSTRUCTION_RE.search(doc.content):
                audit_logs.append(
                    DocumentAccessAuditLog(
                        doc_id=meta.doc_id,
                        title=meta.title,
                        classification=meta.classification.value,
                        access_decision=AccessDecision.POISONING_BLOCKED,
                        reason_code="RAG_INDIRECT_PROMPT_INJECTION_POISONING_BLOCKED: Malicious embedded instructions detected"
                    )
                )
                continue

            # --- STEP 5: Document Access Granted ---
            audit_logs.append(
                DocumentAccessAuditLog(
                    doc_id=meta.doc_id,
                    title=meta.title,
                    classification=meta.classification.value,
                    access_decision=AccessDecision.ALLOWED,
                    reason_code="RAG_ACCESS_GRANTED"
                )
            )
            authorized_docs.append(doc)

        # --- STEP 6: Construct Safe Encapsulated Context Block ---
        context_block = self._build_encapsulated_context(authorized_docs)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)

        return RAGResponse(
            request_id=req_id,
            query=query,
            retrieved_count=len(candidates),
            authorized_count=len(authorized_docs),
            sanitized_context_block=context_block,
            audit_trace=audit_logs,
            latency_ms=elapsed_ms
        )

    def _build_encapsulated_context(self, documents: List[RAGDocument]) -> str:
        """Encapsulates authorized documents in safe XML tags for LLM prompt context."""
        if not documents:
            return ""

        parts = ["<retrieved_reference_documents>"]
        for doc in documents:
            parts.append(
                f'  <document doc_id="{doc.metadata.doc_id}" classification="{doc.metadata.classification.value}">\n'
                f'    <title>{doc.metadata.title}</title>\n'
                f'    <untrusted_reference_text>\n{doc.content}\n    </untrusted_reference_text>\n'
                f'  </document>'
            )
        parts.append("</retrieved_reference_documents>")
        return "\n".join(parts)
