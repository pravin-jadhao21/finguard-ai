import os
import json
from typing import List, Dict, Any, Optional
from app.schemas.rag import RAGDocument, RAGDocumentMetadata, DocumentClassification


class RAGDocumentStore:
    """
    Local Synthetic RAG Document Repository & Retrieval Store.
    Loads approved versioned synthetic document corpus and performs keyword candidate search.
    """

    DEFAULT_CORPUS_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "synthetic_rag_corpus.json")
    )

    def __init__(self, corpus_path: Optional[str] = None):
        self.corpus_path = corpus_path or self.DEFAULT_CORPUS_PATH
        self.documents: List[RAGDocument] = []
        self.load_corpus()

    def load_corpus(self):
        """Loads and parses document corpus JSON file."""
        if not os.path.exists(self.corpus_path):
            raise FileNotFoundError(f"Synthetic RAG document corpus file not found at '{self.corpus_path}'")

        with open(self.corpus_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        self.documents = []
        for raw_doc in raw_data.get("documents", []):
            classification_str = raw_doc.get("classification")
            classification_enum = None
            if classification_str:
                try:
                    classification_enum = DocumentClassification(classification_str)
                except ValueError:
                    classification_enum = None

            metadata = RAGDocumentMetadata(
                doc_id=raw_doc.get("doc_id", "UNKNOWN"),
                title=raw_doc.get("title", "Untitled"),
                classification=classification_enum,
                owner_id=raw_doc.get("owner_id"),
                permitted_roles=raw_doc.get("permitted_roles", []),
                version=raw_doc.get("version", "1.0.0")
            )

            self.documents.append(
                RAGDocument(
                    metadata=metadata,
                    content=raw_doc.get("content", "")
                )
            )

    def search_candidates(self, query: str, top_k: int = 5) -> List[RAGDocument]:
        """
        Performs candidate document retrieval matching query terms against titles and contents.
        Returns up to top_k candidate documents.
        """
        query_terms = [t.lower() for t in query.split() if len(t) > 2]
        if not query_terms:
            return self.documents[:top_k]

        scored_docs = []
        for doc in self.documents:
            text_to_search = f"{doc.metadata.title} {doc.content}".lower()
            score = 0
            for term in query_terms:
                if term in text_to_search:
                    score += text_to_search.count(term)
            if score > 0 or len(query_terms) == 0:
                scored_docs.append((score, doc))

        # Sort by match score descending
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored_docs[:top_k]]
