#!/usr/bin/env python3
"""
Example 13: Vision -- image analysis with Claude.

Demonstrates three ways to use Claude's vision capabilities:
  1. URL-based image: pass a publicly available image URL
  2. Base64-encoded image: create a simple PNG programmatically and send it
  3. Multi-image comparison: send two images and ask Claude to compare them

If Pillow is not installed, examples 2 and 3 gracefully fall back.
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
MAX_TOKENS = 1024

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# Whether Pillow is available
HAVE_PIL = False
try:
    from PIL import Image, ImageDraw  # noqa: F401
    HAVE_PIL = True
except ImportError:
    pass


def print_header(label: str) -> None:
    print(f"\n{'=' * 72}")
    print(f"  {label}")
    print(f"{'=' * 72}")


# ---------------------------------------------------------------------------
# Image sources
# ---------------------------------------------------------------------------
# A well-known public domain / CC0 image (Placekitten provides cat photos)
CAT_IMAGE_URL = "https://placekitten.com/400/300"
# Another image for comparison
DOG_IMAGE_URL = "https://placedog.net/400/300"


def create_test_image(color: str = "blue", label: str = "Test") -> str:
    """
    Create a simple solid-color PNG with a label, return base64-encoded string.
    """
    if not HAVE_PIL:
        return ""

    from PIL import Image, ImageDraw

    img = Image.new("RGB", (200, 150), color=color)
    draw = ImageDraw.Draw(img)
    draw.text((50, 65), label, fill="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def create_two_test_images() -> tuple[str, str]:
    """Create two different colored test images."""
    img1_b64 = create_test_image("blue", "Image A (Blue)")
    img2_b64 = create_test_image("red", "Image B (Red)")
    return img1_b64, img2_b64


# ===================================================================
def main() -> None:
    """Run the vision demonstration."""
    print_header("VISION -- IMAGE ANALYSIS DEMONSTRATION")
    print(f"Model: {MODEL}")
    print(f"Pillow available: {HAVE_PIL}")
    print()

    # ------------------------------------------------------------------
    # Part 1: URL-based image
    # ------------------------------------------------------------------
    print_header("PART 1: URL-based image analysis")

    response_1 = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "url",
                            "url": CAT_IMAGE_URL,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Describe this image in detail. What do you see? "
                                "Include colors, composition, and any subjects.",
                    },
                ],
            }
        ],
    )

    print(f"Image source: {CAT_IMAGE_URL}")
    print(f"Response:\n{response_1.content[0].text}")
    print(f"\nUsage: input_tokens={response_1.usage.input_tokens}, "
          f"output_tokens={response_1.usage.output_tokens}")

    # ------------------------------------------------------------------
    # Part 2: Base64-encoded image (if Pillow available)
    # ------------------------------------------------------------------
    print_header("PART 2: Base64-encoded image")

    if HAVE_PIL:
        img_b64 = create_test_image("green", "Hello from Claude!")

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
                                "media_type": "image/png",
                                "data": img_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Describe this image. What color is the "
                                    "background and what text does it contain?",
                        },
                    ],
                }
            ],
        )

        print(f"Response:\n{response_2.content[0].text}")
        print(f"\nUsage: input_tokens={response_2.usage.input_tokens}, "
              f"output_tokens={response_2.usage.output_tokens}")

    else:
        print("Pillow not installed -- skipping base64 image example.")
        print("Install it with: pip install Pillow")
        print()
        # Fall back to URL-only for part 2
        print("Fallback: using URL-based image instead.")
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
                                "type": "url",
                                "url": DOG_IMAGE_URL,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Describe this image in detail.",
                        },
                    ],
                }
            ],
        )
        print(f"Image source: {DOG_IMAGE_URL}")
        print(f"Response:\n{response_2.content[0].text}")
        print(f"\nUsage: input_tokens={response_2.usage.input_tokens}, "
              f"output_tokens={response_2.usage.output_tokens}")

    # ------------------------------------------------------------------
    # Part 3: Multi-image comparison
    # ------------------------------------------------------------------
    print_header("PART 3: Multi-image comparison")

    if HAVE_PIL:
        img_a_b64, img_b_b64 = create_two_test_images()

        response_3 = client.messages.create(
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
                                "media_type": "image/png",
                                "data": img_a_b64,
                            },
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img_b_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Compare these two images. What are their "
                                    "background colors, and what text do they "
                                    "contain? How are they similar or different?",
                        },
                    ],
                }
            ],
        )

        print(f"Response:\n{response_3.content[0].text}")
        print(f"\nUsage: input_tokens={response_3.usage.input_tokens}, "
              f"output_tokens={response_3.usage.output_tokens}")

    else:
        print("Pillow not installed -- using two URL-based images instead.")
        response_3 = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "url",
                                "url": CAT_IMAGE_URL,
                            },
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "url",
                                "url": DOG_IMAGE_URL,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Compare these two images. What subjects do "
                                    "they depict? How are they similar or "
                                    "different in terms of composition and style?",
                        },
                    ],
                }
            ],
        )
        print(f"Images: {CAT_IMAGE_URL} and {DOG_IMAGE_URL}")
        print(f"Response:\n{response_3.content[0].text}")
        print(f"\nUsage: input_tokens={response_3.usage.input_tokens}, "
              f"output_tokens={response_3.usage.output_tokens}")

    print_header("DEMONSTRATION COMPLETE")
    print("Claude can analyze images from URLs or base64-encoded data.")
    print("Multiple images can be sent in a single request for comparison.")
    print("Supported formats: PNG, JPEG, GIF, WebP, and PDF.")


if __name__ == "__main__":
    main()
