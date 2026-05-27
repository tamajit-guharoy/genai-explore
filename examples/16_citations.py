#!/usr/bin/env python3
"""
Example 16: Citations API with Claude.

Demonstrates the Citations API, which allows Claude to cite specific
passages from provided source documents.

Features shown:
  1. Two text documents with document content blocks and citations enabled
  2. A comparative question requiring citations from both documents
  3. Citation blocks in the response (citation type, document_title,
     referenced_text, start/end offsets)
  4. Displaying cited text alongside the response
  5. Both non-streaming and streaming citation display

The Citations API enables verifiable, grounded responses from Claude.
"""

import json
import os
import sys
from typing import Any

from dotenv import load_dotenv

load_dotenv()

import anthropic

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 1024

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def print_header(label: str) -> None:
    print(f"\n{'=' * 72}")
    print(f"  {label}")
    print(f"{'=' * 72}")


def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


# ---------------------------------------------------------------------------
# Source documents
# ---------------------------------------------------------------------------

DOCUMENT_1_TITLE = "Quantum Computing Overview"
DOCUMENT_1_CONTENT = """
Quantum Computing Overview
=========================

Quantum computing is a rapidly emerging technology that harnesses the laws of
quantum mechanics to solve problems too complex for classical computers.

Key Concepts:
- Qubits: Unlike classical bits which are either 0 or 1, qubits can exist in
  multiple states simultaneously through superposition.
- Entanglement: When qubits become entangled, the state of one instantly
  correlates with the state of another, regardless of distance.
- Quantum gates: Operations that manipulate qubits, analogous to logic gates
  in classical computing.

Current State (2026):
- IBM has deployed quantum processors with over 1,000 qubits.
- Google demonstrated quantum supremacy in 2019 with a 53-qubit processor.
- Error correction remains the biggest challenge for practical quantum computers.
- Quantum volume, a metric for overall quantum computing capability, has been
  doubling approximately every year.

Applications:
- Cryptography: Shor's algorithm could break RSA encryption.
- Drug discovery: Simulating molecular interactions for pharmaceutical research.
- Optimization: Solving complex logistical problems in transportation and finance.
- Machine learning: Quantum algorithms for faster training of AI models.

Limitations:
- Extreme cooling requirements (near absolute zero)
- Decoherence limits computation time
- Error rates are still too high for most practical applications
- Limited qubit connectivity in current architectures
"""

DOCUMENT_2_TITLE = "Classical Computing Fundamentals"
DOCUMENT_2_CONTENT = """
Classical Computing Fundamentals
================================

Classical computing, based on the von Neumann architecture, has been the
foundation of digital technology since the 1940s.

Key Concepts:
- Bits: The fundamental unit of information, representing either 0 or 1.
- Transistors: Semiconductor devices that act as switches, forming the basis
  of logic gates.
- Logic gates: AND, OR, NOT, NAND, NOR, XOR operations that process binary data.
- The stored-program concept: Instructions and data share the same memory space.

Current State (2026):
- Transistor sizes have reached 3nm with leading-edge nodes.
- Moore's Law has slowed but not stopped; chipmakers are exploring 2nm and 1nm
  processes.
- Heterogeneous computing (CPU + GPU + NPU) is now standard in modern processors.
- Chiplet architectures allow mixing different manufacturing processes.

Key Advantages:
- Extremely reliable: error rates below 10^-18 per operation
- Room temperature operation
- Mature manufacturing ecosystem
- Extensive software ecosystem and programming models
- Cost-effective for most everyday computing tasks

Limitations:
- Classical computers struggle with problems requiring exponential time
- Energy consumption is a growing concern for large data centers
- Physical limits of silicon transistor miniaturization are approaching
- Cannot efficiently simulate quantum systems of meaningful size
"""


# ===================================================================
def main() -> None:
    """Run the Citations API demonstration."""
    print_header("CITATIONS API DEMONSTRATION")
    print(f"Model: {MODEL}")
    print()

    print("Source Documents:")
    print(f"  1. '{DOCUMENT_1_TITLE}' - {len(DOCUMENT_1_CONTENT)} chars")
    print(f"  2. '{DOCUMENT_2_TITLE}' - {len(DOCUMENT_2_CONTENT)} chars")
    print()

    # ------------------------------------------------------------------
    # Part 1: Non-streaming citation response
    # ------------------------------------------------------------------
    print_header("PART 1: Non-streaming citation response")

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "text",
                            "media_type": "text/plain",
                            "data": DOCUMENT_1_CONTENT,
                        },
                        "title": DOCUMENT_1_TITLE,
                        "citations": {"enabled": True},
                    },
                    {
                        "type": "document",
                        "source": {
                            "type": "text",
                            "media_type": "text/plain",
                            "data": DOCUMENT_2_CONTENT,
                        },
                        "title": DOCUMENT_2_TITLE,
                        "citations": {"enabled": True},
                    },
                    {
                        "type": "text",
                        "text": (
                            "Compare quantum computing and classical computing "
                            "across these dimensions:\n"
                            "1. Basic unit of information (bit vs qubit)\n"
                            "2. Current state of technology in 2026\n"
                            "3. Key advantages of each approach\n"
                            "4. Primary limitations\n\n"
                            "For each point, cite the specific passages you "
                            "are referencing from the provided documents."
                        ),
                    },
                ],
            }
        ],
    )

    # Separate text and citation blocks
    text_parts = [b for b in response.content if b.type == "text"]
    citation_parts = [b for b in response.content if b.type == "citation"]

    print(f"Total content blocks: {len(response.content)}")
    print(f"  - Text blocks:    {len(text_parts)}")
    print(f"  - Citation blocks: {len(citation_parts)}")
    print()

    # Print the response with inline citation markers
    print_header("CLAUDE'S RESPONSE")

    for block in response.content:
        if block.type == "text":
            print(block.text)
        elif block.type == "citation":
            print(f"\n[Citation {citation_parts.index(block) + 1}]:")
            print(f"  Source: '{block.document_title}'")
            print(f"  Type: {block.citation_type}")
            print(f"  Referenced text: \"{block.referenced_text}\"")
            print(f"  Start offset: {block.start_block_index}:{block.start_line_number}")
            print(f"  End offset:   {block.end_block_index}:{block.end_line_number}")

    print(f"\nUsage: input_tokens={response.usage.input_tokens}, "
          f"output_tokens={response.usage.output_tokens}")

    # ------------------------------------------------------------------
    # Part 2: Detailed citation inspection
    # ------------------------------------------------------------------
    print_header("PART 2: DETAILED CITATION INSPECTION")

    print(f"Number of citations in response: {len(citation_parts)}")
    print()

    for idx, citation in enumerate(citation_parts, 1):
        print(f"--- Citation {idx} ---")
        print(f"  Citation type:    {citation.citation_type}")
        print(f"  Document title:   {citation.document_title}")
        print(f"  Referenced text:  \"{citation.referenced_text}\"")

        # For char-based citations, show offsets
        if hasattr(citation, "start_char_index") and citation.start_char_index is not None:
            print(f"  Char offset:      [{citation.start_char_index}:{citation.end_char_index}]")

        # For block/line citations, show block/line offsets
        if hasattr(citation, "start_block_index") and citation.start_block_index is not None:
            print(f"  Block/Line range: "
                  f"[{citation.start_block_index}:{citation.start_line_number}] -> "
                  f"[{citation.end_block_index}:{citation.end_line_number}]")

        # Show the surrounding document context
        source_doc = (
            DOCUMENT_1_CONTENT
            if citation.document_title == DOCUMENT_1_TITLE
            else DOCUMENT_2_CONTENT
        )
        cited_text = citation.referenced_text
        if cited_text in source_doc:
            idx_in_doc = source_doc.index(cited_text)
            context_start = max(0, idx_in_doc - 40)
            context_end = min(len(source_doc), idx_in_doc + len(cited_text) + 40)
            context = source_doc[context_start:context_end]
            prefix = "..." if context_start > 0 else ""
            suffix = "..." if context_end < len(source_doc) else ""
            print(f"  Context:          {prefix}{context}{suffix}")

        print()

    # ------------------------------------------------------------------
    # Part 3: Streaming citation display
    # ------------------------------------------------------------------
    print_header("PART 3: Streaming citation response")

    print("Streaming response with citations:\n")

    collected_text = ""
    collected_citations: list[dict] = []

    with client.messages.stream(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "text",
                            "media_type": "text/plain",
                            "data": DOCUMENT_1_CONTENT,
                        },
                        "title": DOCUMENT_1_TITLE,
                        "citations": {"enabled": True},
                    },
                    {
                        "type": "document",
                        "source": {
                            "type": "text",
                            "media_type": "text/plain",
                            "data": DOCUMENT_2_CONTENT,
                        },
                        "title": DOCUMENT_2_TITLE,
                        "citations": {"enabled": True},
                    },
                    {
                        "type": "text",
                        "text": (
                            "What are the key applications of quantum computing "
                            "mentioned in the documents, and what are the main "
                            "advantages of classical computing? Cite your sources."
                        ),
                    },
                ],
            }
        ],
    ) as stream:
        # Collect all events
        for event in stream:
            if event.type == "content_block_delta" and event.delta.type == "text_delta":
                collected_text += event.delta.text
                print(event.delta.text, end="", flush=True)

        # After streaming completes, get the full response with citations
        response_streamed = stream.get_final_message()

    # Stream is done -- now show citations
    stream_citations = [b for b in response_streamed.content if b.type == "citation"]
    if stream_citations:
        print("\n")
        print_header("CITATIONS FROM STREAMING RESPONSE")
        for idx, citation in enumerate(stream_citations, 1):
            print(f"[{idx}] From '{citation.document_title}': "
                  f"\"{citation.referenced_text[:100]}{'...' if len(citation.referenced_text) > 100 else ''}\"")

    # ------------------------------------------------------------------
    # Part 4: Cost considerations
    # ------------------------------------------------------------------
    print_header("PART 4: CITATIONS SUMMARY")
    print("The Citations API enables Claude to ground responses in source documents.")
    print()
    print("Key features:")
    print(" - Documents are sent as 'document' content blocks")
    print(" - Citations are enabled per-document with citations={'enabled': True}")
    print(" - Each citation includes: document_title, referenced_text, and offsets")
    print(" - Citation types can be 'char_location', 'content_block_location', etc.")
    print(" - Streaming and non-streaming both support citations")
    print()
    print("Best practices:")
    print(" - Always provide document titles for clear source attribution")
    print(" - Use citations for RAG (Retrieval Augmented Generation) applications")
    print(" - Citations increase input token usage (document content is sent)")
    print(" - Display citations alongside responses for transparency")


if __name__ == "__main__":
    main()
