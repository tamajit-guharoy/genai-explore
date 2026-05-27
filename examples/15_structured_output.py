#!/usr/bin/env python3
"""
Example 15: Structured outputs and JSON mode.

Demonstrates two approaches for getting structured responses from Claude:
  1. JSON mode (output_config format="json_object") -- Claude returns valid JSON
  2. Structured Outputs with a full JSON schema -- Claude strictly follows
     a user-defined schema with type validation and constraints

Use cases:
  - Extracting structured data from unstructured text
  - Classifying content into predefined categories
  - Generating consistent API responses
  - Building data pipelines with guaranteed output formats
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


def pretty_print_json(data: Any) -> None:
    """Pretty-print a JSON-serializable object."""
    print(json.dumps(data, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Schema definitions
# ---------------------------------------------------------------------------

PRODUCT_REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "product_name": {
            "type": "string",
            "description": "The name of the product being reviewed.",
        },
        "rating": {
            "type": "number",
            "description": "Rating from 0 to 5 (supports half-stars).",
            "minimum": 0,
            "maximum": 5,
        },
        "pros": {
            "type": "array",
            "description": "List of positive aspects of the product.",
            "items": {"type": "string"},
            "minItems": 1,
        },
        "cons": {
            "type": "array",
            "description": "List of negative aspects of the product.",
            "items": {"type": "string"},
            "minItems": 1,
        },
        "verdict": {
            "type": "string",
            "description": "Overall recommendation.",
            "enum": ["buy", "wait", "skip"],
        },
        "summary": {
            "type": "string",
            "description": "One-sentence summary of the review.",
            "maxLength": 150,
        },
    },
    "required": [
        "product_name",
        "rating",
        "pros",
        "cons",
        "verdict",
        "summary",
    ],
    "additionalProperties": False,
}


CLASSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {
            "type": "string",
            "description": "The original text being classified.",
        },
        "category": {
            "type": "string",
            "description": "Primary category label.",
            "enum": [
                "technology",
                "health",
                "finance",
                "education",
                "entertainment",
                "sports",
                "politics",
                "other",
            ],
        },
        "sentiment": {
            "type": "string",
            "description": "Overall sentiment of the text.",
            "enum": ["positive", "negative", "neutral", "mixed"],
        },
        "confidence": {
            "type": "number",
            "description": "Confidence score between 0.0 and 1.0.",
            "minimum": 0.0,
            "maximum": 1.0,
        },
        "tags": {
            "type": "array",
            "description": "Relevant keywords or tags extracted from the text.",
            "items": {"type": "string"},
            "maxItems": 5,
        },
        "language": {
            "type": "string",
            "description": "Detected language (e.g., 'en', 'es', 'fr').",
        },
        "word_count": {
            "type": "integer",
            "description": "Approximate word count of the text.",
            "minimum": 0,
        },
    },
    "required": [
        "text",
        "category",
        "sentiment",
        "confidence",
        "tags",
        "language",
        "word_count",
    ],
    "additionalProperties": False,
}


# ===================================================================
def main() -> None:
    """Run the structured output demonstrations."""
    print_header("STRUCTURED OUTPUTS AND JSON MODE")
    print(f"Model: {MODEL}")
    print()

    # ------------------------------------------------------------------
    # Part 1: JSON mode (free-form JSON)
    # ------------------------------------------------------------------
    print_header("PART 1: JSON mode (output_config with json_object)")

    response_1 = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        output_config={"format": {"type": "json_object"}},
        messages=[
            {
                "role": "user",
                "content": (
                    "Extract the following information as JSON from this text:\n\n"
                    "Text: 'I recently bought the UltraPhone X Pro. The battery "
                    "lasts two full days which is amazing, and the camera takes "
                    "incredible photos. However, it's quite expensive at $1,200 "
                    "and the phone is heavier than I expected. Overall I think "
                    "it's a great phone but you should wait for a sale.'\n\n"
                    "Include: product name, rating (0-5), pros list, cons list, "
                    "verdict (buy/wait/skip), and a one-sentence summary. "
                    "Return ONLY valid JSON, no other text."
                ),
            }
        ],
    )

    print("Raw JSON response:")
    raw_json_1 = response_1.content[0].text
    print(raw_json_1[:500])
    print()

    # Parse and validate
    try:
        parsed = json.loads(raw_json_1)
        print("Parsed JSON:")
        pretty_print_json(parsed)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")

    print(f"\nUsage: input_tokens={response_1.usage.input_tokens}, "
          f"output_tokens={response_1.usage.output_tokens}")

    # ------------------------------------------------------------------
    # Part 2: Structured Outputs with JSON schema
    # ------------------------------------------------------------------
    print_header("PART 2: Structured Outputs with product_review schema")

    response_2 = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[
            {
                "role": "user",
                "content": (
                    "Review this product and return data matching the provided schema:\n\n"
                    "Product: CodeBot Pro\n"
                    "Review: CodeBot Pro is an AI-powered code review tool that "
                    "integrates with GitHub and GitLab. It catches bugs early and "
                    "provides helpful suggestions. The setup was straightforward "
                    "and the documentation is excellent. On the downside, the "
                    "pricing is steep for small teams at $50 per developer per "
                    "month, and it sometimes gives false positives on style "
                    "issues. It also doesn't support all languages equally well. "
                    "Overall, it's a useful tool but I'd recommend waiting for "
                    "better language support and possibly lower pricing."
                ),
            }
        ],
        output_config={
            "format": {
                "type": "json_schema",
                "name": "product_review",
                "schema": PRODUCT_REVIEW_SCHEMA,
                "strict": True,
            }
        },
    )

    raw_json_2 = response_2.content[0].text
    print("Schema-validated response:")
    try:
        parsed_2 = json.loads(raw_json_2)
        pretty_print_json(parsed_2)

        # Show field-level access
        print_header("FIELD ACCESS")
        print(f"Product: {parsed_2['product_name']}")
        print(f"Rating:  {parsed_2['rating']}/5")
        print(f"Verdict: {parsed_2['verdict']}")
        print(f"Summary: {parsed_2['summary']}")
        print(f"Pros ({len(parsed_2['pros'])}):")
        for p in parsed_2["pros"]:
            print(f"  + {p}")
        print(f"Cons ({len(parsed_2['cons'])}):")
        for c in parsed_2["cons"]:
            print(f"  - {c}")

    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")

    # ------------------------------------------------------------------
    # Part 3: Classification with schema
    # ------------------------------------------------------------------
    print_header("PART 3: Classification use case")

    texts_to_classify = [
        "The Federal Reserve raised interest rates by 25 basis points today, "
        "citing persistent inflation. Markets reacted with mixed results as "
        "investors digest the implications for the coming quarters.",

        "Scientists at MIT have developed a new machine learning model that "
        "can predict protein folding with 95% accuracy, potentially "
        "accelerating drug discovery for diseases like Alzheimer's and cancer.",
    ]

    for idx, text in enumerate(texts_to_classify, 1):
        print(f"\n--- Text {idx} ---")
        print(f"Input: {text[:80]}...")

        response_3 = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Classify the following text using the provided schema:\n\n{text}"
                    ),
                }
            ],
            output_config={
                "format": {
                    "type": "json_schema",
                    "name": "text_classification",
                    "schema": CLASSIFICATION_SCHEMA,
                    "strict": True,
                }
            },
        )

        try:
            parsed_3 = json.loads(response_3.content[0].text)
            print(f"  Category:      {parsed_3['category']}")
            print(f"  Sentiment:     {parsed_3['sentiment']}")
            print(f"  Confidence:    {parsed_3['confidence']}")
            print(f"  Tags:          {', '.join(parsed_3['tags'])}")
            print(f"  Language:      {parsed_3['language']}")
            print(f"  Word count:    {parsed_3['word_count']}")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  Error parsing classification: {e}")

    print_header("DEMONSTRATION COMPLETE")
    print("JSON mode: Claude returns valid JSON but the structure is guided "
          "by prompts.")
    print("Structured Outputs: Claude strictly follows a JSON Schema with "
          "type checking, enums, constraints, and required fields.")
    print("Use 'strict: true' to enforce the schema exactly.")


if __name__ == "__main__":
    main()
