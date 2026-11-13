from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DocumentClassification(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    RESTRICTED_CUSTOMER = "RESTRICTED_CUSTOMER"
    CONFIDENTIAL = "CONFIDENTIAL"


class AccessDecision(str, Enum):
    ALLOWED = "ALLOWED"
    DENIED_ROLE = "DENIED_ROLE"
    DENIED_OWNER = "DENIED_OWNER"
    DENIED_INVALID_METADATA = "DENIED_INVALID_METADATA"
    POISONING_BLOCKED = "POISONING_BLOCKED"


class RAGDocumentMetadata(BaseModel):
    doc_id: str = Field(...)
    title: str = Field(...)
    classification: Optional[DocumentClassification] = Field(default=None)
    owner_id: Optional[str] = Field(default=None)
    permitted_roles: List[str] = Field(default_factory=list)
    version: Optional[str] = Field(default="1.0.0")


class RAGDocument(BaseModel):
    metadata: RAGDocumentMetadata = Field(...)
    content: str = Field(...)


class RAGUserContext(BaseModel):
    user_id: str = Field(..., description="Authenticated requester user ID (e.g. USR-1001)")
    user_role: str = Field(default="RetailCustomer", description="Requester role (e.g. RetailCustomer, ComplianceOfficer)")


class RAGRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User search query or topic")
    user_context: RAGUserContext = Field(..., description="Requester identity and role context")
    top_k: int = Field(default=5, ge=1, le=20, description="Max candidate documents to evaluate")


class DocumentAccessAuditLog(BaseModel):
    doc_id: str = Field(...)
    title: str = Field(...)
    classification: Optional[str] = Field(default=None)
    access_decision: AccessDecision = Field(...)
    reason_code: str = Field(...)


class RAGResponse(BaseModel):
    request_id: str = Field(...)
    query: str = Field(...)
    retrieved_count: int = Field(default=0, description="Total candidate documents found")
    authorized_count: int = Field(default=0, description="Documents authorized and safe for context inclusion")
    sanitized_context_block: str = Field(default="", description="Safe XML-encapsulated RAG context for LLM prompt")
    audit_trace: List[DocumentAccessAuditLog] = Field(default_factory=list, description="Zero-data-leakage access audit logs")
    latency_ms: float = Field(...)
