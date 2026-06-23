#!/usr/bin/env python3
"""
rag_with_supermemory.py -- Full RAG pipeline using Supermemory as the knowledge store

Demonstrates:
  - Document ingestion (text + URLs)
  - Hybrid semantic search retrieval with metadata filtering
  - Context-aware answer generation via LLM
  - Document management (list, delete)

Usage:
    python rag_with_supermemory.py

Requirements:
    pip install supermemory openai
    export SUPERMEMORY_API_KEY="sm_..."
    export OPENAI_API_KEY="sk-..."
"""

import os
import sys
from supermemory import Supermemory, APIError


class SupermemoryRAG:
    """RAG (Retrieval-Augmented Generation) pipeline backed by Supermemory."""

    def __init__(self, knowledge_base_name: str = "default_kb"):
        self.sm = Supermemory()
        self.kb_tag = f"kb_{knowledge_base_name}"

    # ── Ingestion ─────────────────────────────────────

    def ingest_text(
        self,
        content: str,
        metadata: dict | None = None,
        title: str = "",
    ) -> str:
        """Ingest a text document into the knowledge base."""
        try:
            response = self.sm.add(
                content=f"{title}\n{content}" if title else content,
                container_tag=self.kb_tag,
                metadata=metadata or {},
            )
            print(f"[INGEST] Added document: {response.id}")
            return response.id
        except APIError as e:
            print(f"[ERROR] Ingestion failed: {e}", file=sys.stderr)
            raise

    def ingest_url(self, url: str, metadata: dict | None = None) -> str:
        """Ingest a web page (Supermemory auto-extracts content)."""
        try:
            response = self.sm.add(
                content=url,
                container_tag=self.kb_tag,
                metadata={"source": "url", "url": url, **(metadata or {})},
            )
            print(f"[INGEST] Queued URL: {response.id} ({url[:60]}...)")
            return response.id
        except APIError as e:
            print(f"[ERROR] URL ingestion failed: {e}", file=sys.stderr)
            raise

    def ingest_bulk(self, documents: list[tuple[str, dict]]) -> list[str]:
        """Ingest multiple documents at once."""
        ids = []
        for content, metadata in documents:
            try:
                doc_id = self.ingest_text(content, metadata)
                ids.append(doc_id)
            except APIError:
                continue
        print(f"[INGEST] Bulk: {len(ids)}/{len(documents)} documents ingested")
        return ids

    # ── Retrieval ─────────────────────────────────────

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.5,
        filters: dict | None = None,
    ) -> list[dict]:
        """Retrieve the most relevant documents for a query."""
        try:
            results = self.sm.search.documents(
                q=query,
                container_tags=[self.kb_tag],
                limit=top_k,
                document_threshold=threshold,
                filters=filters,
            )
            return [
                {
                    "content": r.get("memory", str(r)),
                    "score": r.get("score", 0.0),
                    "id": r.get("id", ""),
                }
                for r in results.results
            ]
        except APIError as e:
            print(f"[ERROR] Retrieval failed: {e}", file=sys.stderr)
            return []

    # ── Generation ────────────────────────────────────

    def generate_answer(
        self,
        question: str,
        top_k: int = 5,
        include_sources: bool = True,
    ) -> str:
        """Generate an answer using retrieved context + LLM."""
        # Step 1: Retrieve relevant context
        chunks = self.retrieve(question, top_k=top_k)
        if not chunks:
            return "I couldn't find any relevant information to answer your question."

        # Step 2: Build context from retrieved chunks
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"[Document {i}] (score: {chunk['score']:.2f})")
            context_parts.append(chunk["content"])
        context = "\n\n".join(context_parts)

        # Step 3: Generate answer with LLM
        prompt = f"""You are a helpful assistant. Answer the question based ONLY on the
provided context. If the context doesn't contain the answer, say so.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

        try:
            from openai import OpenAI
            llm = OpenAI()
            response = llm.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500,
            )
            answer = response.choices[0].message.content
        except ImportError:
            answer = (
                f"[DEMO MODE -- install OpenAI for full generation]\n"
                f"Retrieved {len(chunks)} relevant chunks for question."
            )

        # Step 4: Optionally append sources
        if include_sources and chunks:
            sources = "\n\n---\n**Sources:**\n" + "\n".join(
                f"- [{c['score']:.2f}] {c['content'][:100]}..."
                for c in chunks
            )
            answer += sources

        return answer

    # ── Management ────────────────────────────────────

    def list_documents(self, limit: int = 20) -> list[dict]:
        """List documents in the knowledge base."""
        try:
            docs = self.sm.documents.list(
                container_tags=[self.kb_tag],
                limit=limit,
            )
            return [
                {"id": d.get("id"), "metadata": d.get("metadata", {})}
                for d in (docs.documents if hasattr(docs, "documents") else [])
            ]
        except APIError as e:
            print(f"[ERROR] List failed: {e}", file=sys.stderr)
            return []

    def delete_document(self, doc_id: str):
        """Delete a document from the knowledge base."""
        try:
            self.sm.documents.delete(doc_id=doc_id)
            print(f"[DELETE] Removed document: {doc_id}")
        except APIError as e:
            print(f"[ERROR] Delete failed: {e}", file=sys.stderr)

    def search_by_metadata(
        self,
        query: str,
        metadata_filter: dict,
        top_k: int = 5,
    ) -> list[dict]:
        """Search with metadata filtering."""
        filters = {
            "AND": [{"key": k, "value": v} for k, v in metadata_filter.items()]
        }
        return self.retrieve(query, top_k=top_k, filters=filters)


def demo():
    """Demonstrate the RAG pipeline."""
    rag = SupermemoryRAG(knowledge_base_name="company_wiki")

    print("=" * 60)
    print("RAG Pipeline Demo -- Company Knowledge Base")
    print("=" * 60)

    # 1. Ingest documents
    print("\n--- Ingesting Documents ---")
    rag.ingest_text(
        title="Company Overview",
        content="Acme Corp was founded in 2020 by Jane Smith and John Doe. "
                "We build AI-powered developer productivity tools. "
                "Our headquarters is in San Francisco, CA.",
        metadata={"category": "company", "type": "overview"},
    )
    rag.ingest_text(
        title="Product: CodeAssist",
        content="CodeAssist is our flagship product -- an AI coding companion "
                "that integrates with VS Code, JetBrains, and Neovim. "
                "It supports 50+ programming languages and has 100K+ users. "
                "Key features: code completion, bug detection, refactoring, "
                "and natural language code generation.",
        metadata={"category": "product", "type": "documentation"},
    )
    rag.ingest_text(
        title="Pricing Tiers",
        content="Free: 100 completions/day, community support. "
                "Pro ($20/mo): unlimited completions, priority support. "
                "Enterprise ($50/user/mo): on-premise deployment, SSO, audit logs, SLA. "
                "Annual billing gives 20% discount on all tiers.",
        metadata={"category": "pricing", "type": "documentation"},
    )
    rag.ingest_text(
        title="Engineering Culture",
        content="We follow an engineering-driven culture. Teams have full autonomy. "
                "We use Rust for our core engine, TypeScript/React for the frontend, "
                "and Python for ML pipelines. CI/CD via GitHub Actions. "
                "Infrastructure on AWS with Kubernetes.",
        metadata={"category": "engineering", "type": "culture"},
    )

    # 2. Answer questions
    questions = [
        "Who founded the company and when?",
        "What are the pricing tiers for CodeAssist?",
        "What programming languages does the engineering team use?",
        "What is the main product and how many users does it have?",
    ]

    print("\n--- Answering Questions ---\n")
    for q in questions:
        print(f"Q: {q}")
        answer = rag.generate_answer(q, top_k=3)
        print(f"A: {answer[:300]}...\n")

    # 3. Metadata-filtered search
    print("--- Filtered Search (category=engineering) ---")
    results = rag.search_by_metadata(
        query="engineering",
        metadata_filter={"category": "engineering"},
        top_k=3,
    )
    for r in results:
        print(f"  [{r['score']:.2f}] {r['content'][:80]}...")

    print("\n" + "=" * 60)
    print("RAG pipeline demo complete!")
    print("All documents are persistently stored in Supermemory.")
    print("Run again with different questions -- the knowledge base persists.")


if __name__ == "__main__":
    demo()
