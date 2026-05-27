#!/usr/bin/env python3
"""
Example 14: PDF analysis using Claude Vision.

Demonstrates how to send a PDF to Claude for analysis:
  1. Create a simple PDF programmatically using reportlab or fpdf
  2. Base64-encode the PDF and send it as an image content block
  3. Ask Claude to summarize and extract key information
  4. Show how Claude handles PDF pages as images

If PDF libraries are not available, falls back to a publicly accessible PDF URL.
"""

import base64
import io
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
MAX_TOKENS = 2048

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def print_header(label: str) -> None:
    print(f"\n{'=' * 72}")
    print(f"  {label}")
    print(f"{'=' * 72}")


# ---------------------------------------------------------------------------
# PDF creation helpers
# ---------------------------------------------------------------------------
def check_pdf_libraries() -> str:
    """Check which PDF libraries are available. Returns 'fpdf', 'reportlab', or ''."""
    try:
        import fpdf  # noqa: F401
        return "fpdf"
    except ImportError:
        pass
    try:
        import reportlab  # noqa: F401
        return "reportlab"
    except ImportError:
        pass
    return ""


def create_pdf_fpdf() -> bytes | None:
    """Create a simple PDF using fpdf2."""
    try:
        from fpdf import FPDF

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.cell(text="Sample PDF Document", new_x="LMARGIN", new_y="NEXT", new_y_pos="NEXT")
        pdf.ln(10)
        pdf.set_font("Helvetica", size=10)
        pdf.multi_cell(
            w=0,
            text=(
                "This is a sample PDF document created for testing Claude's "
                "PDF analysis capabilities.\n\n"
                "Claude can read PDFs page by page, extracting text, tables, "
                "and images from each page.\n\n"
                "Key Features of PDF Analysis:\n"
                "- Page-by-page extraction\n"
                "- Text recognition (OCR quality)\n"
                "- Table structure understanding\n"
                "- Image analysis within PDFs\n\n"
                "Sample Data:\n"
                "- Project: Claude API Integration\n"
                "- Version: 2.1.0\n"
                "- Author: Anthropic SDK Team\n"
                "- Pages: 1\n"
                "- Format: PDF/A\n\n"
                "This document demonstrates the PDF vision capabilities "
                "available through the Anthropic API."
            ),
        )
        pdf_bytes = pdf.output()
        return pdf_bytes
    except Exception as e:
        print(f"  fpdf error: {e}")
        return None


def create_pdf_reportlab() -> bytes | None:
    """Create a simple PDF using reportlab."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter)
        styles = getSampleStyleSheet()

        story = [
            Paragraph("Sample PDF Document", styles["Title"]),
            Spacer(1, 12),
        ]

        body_text = (
            "This is a sample PDF document created for testing Claude's "
            "PDF analysis capabilities.\n\n"
            "Claude can read PDFs page by page, extracting text, tables, "
            "and images from each page.\n\n"
            "Key Features of PDF Analysis:\n"
            "- Page-by-page extraction\n"
            "- Text recognition (OCR quality)\n"
            "- Table structure understanding\n"
            "- Image analysis within PDFs\n\n"
            "Sample Data:\n"
            "- Project: Claude API Integration\n"
            "- Version: 2.1.0\n"
            "- Author: Anthropic SDK Team\n"
            "- Pages: 1\n"
            "- Format: PDF/A\n\n"
            "This document demonstrates the PDF vision capabilities "
            "available through the Anthropic API."
        )

        for para in body_text.split("\n\n"):
            story.append(Paragraph(para.replace("\n", "<br/>"), styles["Normal"]))
            story.append(Spacer(1, 6))

        doc.build(story)
        pdf_bytes = buf.getvalue()
        return pdf_bytes
    except Exception as e:
        print(f"  reportlab error: {e}")
        return None


def create_pdf() -> bytes | None:
    """Create a PDF using any available library."""
    lib = check_pdf_libraries()
    if lib == "fpdf":
        print("  Using fpdf2 library")
        return create_pdf_fpdf()
    elif lib == "reportlab":
        print("  Using reportlab library")
        return create_pdf_reportlab()
    else:
        print("  No PDF library available")
        return None


# ---------------------------------------------------------------------------
# PDF from URL fallback
# ---------------------------------------------------------------------------
# A publicly accessible PDF (RFC 793 - TCP specification, public domain)
FALLBACK_PDF_URL = "https://www.rfc-editor.org/rfc/rfc793.txt"

# Try to find a real PDF publicly -- use a small PDF
PUBLIC_PDF_URL = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"


def fetch_pdf_from_url(url: str) -> bytes:
    """Fetch a PDF from a public URL."""
    import requests
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.content


# ===================================================================
def main() -> None:
    """Run the PDF analysis demonstration."""
    print_header("PDF ANALYSIS USING CLAUDE VISION")
    print(f"Model: {MODEL}")
    print()

    pdf_bytes: bytes | None = None
    source_label = ""

    # Try to create a PDF programmatically
    print("Attempting to create a PDF programmatically...")
    pdf_bytes = create_pdf()

    if pdf_bytes is not None:
        source_label = "programmatically created PDF"
        print(f"  PDF created successfully: {len(pdf_bytes)} bytes")
    else:
        print("  Falling back to fetching a PDF from the internet...")
        try:
            pdf_bytes = fetch_pdf_from_url(PUBLIC_PDF_URL)
            source_label = f"URL: {PUBLIC_PDF_URL}"
            print(f"  PDF fetched: {len(pdf_bytes)} bytes")
        except Exception as e:
            print(f"  Failed to fetch PDF from URL: {e}")
            print("  Cannot proceed without a PDF source. Exiting.")
            return

    # ------------------------------------------------------------------
    # Part 1: Send PDF as base64 image content block
    # ------------------------------------------------------------------
    print_header("PART 1: Sending PDF for analysis")
    print(f"Source: {source_label}")
    print()

    pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "Please analyze this PDF document and provide:\n"
                            "1. The document title and overall purpose\n"
                            "2. Key information and data points mentioned\n"
                            "3. Any structured data (tables, lists, etc.)\n"
                            "4. A brief summary of the content\n\n"
                            "If you can see multiple pages, describe each one."
                        ),
                    },
                ],
            }
        ],
    )

    print_header("CLAUDE'S ANALYSIS")
    print(response.content[0].text)

    usage = response.usage
    print(f"\nUsage: input_tokens={usage.input_tokens}, "
          f"output_tokens={usage.output_tokens}")

    # ------------------------------------------------------------------
    # Part 2: Page-by-page analysis (if we have a multi-page approach)
    # ------------------------------------------------------------------
    print_header("PART 2: Additional analysis")

    response_2 = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "Extract the sample data from this document and "
                            "present it as a structured JSON object. Include "
                            "all fields and values mentioned in the document."
                        ),
                    },
                ],
            }
        ],
    )

    print("Claude's structured extraction:")
    print(response_2.content[0].text)

    usage_2 = response_2.usage
    print(f"\nUsage: input_tokens={usage_2.input_tokens}, "
          f"output_tokens={usage_2.output_tokens}")

    print_header("DEMONSTRATION COMPLETE")
    print("Claude can analyze PDF documents by treating each page as an image.")
    print("Key points:")
    print(" - Send PDFs as base64-encoded image blocks with media_type='application/pdf'")
    print(" - Claude handles multi-page PDFs automatically")
    print(" - You can ask Claude to extract text, tables, or structured data")
    print(" - The same image analysis capabilities apply to PDF pages")


if __name__ == "__main__":
    main()
