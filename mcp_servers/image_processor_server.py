#!/usr/bin/env python3
"""
MCP Image Processor Server — demonstrates image manipulation, OCR text extraction,
color analysis, EXIF reading, and binary content types in MCP responses.

Install: pip install mcp pillow pytesseract
Configure in .claude/settings.json:
{
  "mcpServers": {
    "image": {
      "type": "stdio",
      "command": "python",
      "args": ["mcp_servers/image_processor_server.py"]
    }
  }
}
"""

import asyncio
import base64
import io
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import StdioServerTransport
from mcp.types import Tool, TextContent, ImageContent

server = Server("image")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _b64_decode(data: str) -> bytes:
    """Decode base64, handling data URI prefix."""
    if "," in data and data.startswith("data:"):
        data = data.split(",", 1)[1]
    return base64.b64decode(data)

def _b64_encode(data: bytes, mime: str = "image/png") -> str:
    return f"data:{mime};base64," + base64.b64encode(data).decode()

def _load_image(data_b64: str):
    """Load a PIL Image from base64 string."""
    from PIL import Image
    raw = _b64_decode(data_b64)
    return Image.open(io.BytesIO(raw))

def _image_to_b64(img, fmt: str = "PNG") -> str:
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return _b64_encode(buf.getvalue(), f"image/{fmt.lower()}")

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@server.tool()
async def image_info(image_data: str) -> list[TextContent]:
    """Get detailed information about an image.

    Args:
        image_data: Base64-encoded image (with or without data: URI prefix)
    """
    from PIL import Image, ExifTags

    img = _load_image(image_data)

    info: dict[str, Any] = {
        "format": img.format,
        "mode": img.mode,
        "width": img.width,
        "height": img.height,
        "megapixels": round(img.width * img.height / 1_000_000, 2),
        "aspect_ratio": f"{img.width}:{img.height}",
        "is_animated": getattr(img, "is_animated", False),
        "n_frames": getattr(img, "n_frames", 1),
        "has_transparency": img.mode in ("RGBA", "LA", "PA", "P") or (
            img.mode == "P" and "transparency" in img.info
        ),
    }

    # Color statistics
    if img.mode in ("RGB", "RGBA"):
        # Sample pixels for color analysis
        small = img.resize((50, 50))
        pixels = list(small.getdata())
        if small.mode == "RGBA":
            pixels = [p[:3] for p in pixels]
        avg_color = tuple(int(sum(c) / len(c)) for c in zip(*pixels))
        info["average_color"] = {
            "rgb": avg_color,
            "hex": f"#{avg_color[0]:02x}{avg_color[1]:02x}{avg_color[2]:02x}",
        }

    # EXIF
    try:
        exif_data = img.getexif()
        if exif_data:
            exif = {}
            for tag_id, value in exif_data.items():
                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                if isinstance(value, bytes):
                    value = f"<{len(value)} bytes>"
                exif[tag_name] = value
            info["exif"] = exif
    except Exception:
        pass

    return [TextContent(type="text", text=json.dumps(info, indent=2, default=str))]

@server.tool()
async def image_crop(
    image_data: str,
    left: int = 0,
    top: int = 0,
    right: int = 100,
    bottom: int = 100,
) -> list[TextContent]:
    """Crop an image to a bounding box.

    Args:
        image_data: Base64-encoded image
        left: Left coordinate (pixels from left edge)
        top: Top coordinate (pixels from top edge)
        right: Right coordinate (pixels from left edge)
        bottom: Bottom coordinate (pixels from top edge)
    """
    img = _load_image(image_data)
    cropped = img.crop((left, top, right, bottom))
    return [TextContent(type="text", text=json.dumps({
        "original_size": f"{img.width}x{img.height}",
        "cropped_size": f"{right - left}x{bottom - top}",
        "data": _image_to_b64(cropped),
    }, indent=2))]

@server.tool()
async def image_filters(
    image_data: str,
    filter_name: str = "grayscale",
    intensity: float = 1.0,
) -> list[TextContent]:
    """Apply visual filters to an image.

    Args:
        image_data: Base64-encoded image
        filter_name: "grayscale", "sepia", "invert", "blur", "sharpen", "emboss", "edge_enhance"
        intensity: Filter intensity 0.0-1.0 (for blur: radius multiplier; for others: blend ratio)
    """
    from PIL import ImageFilter, ImageOps

    img = _load_image(image_data)
    original = img.copy()

    filters = {
        "grayscale": lambda i: i.convert("L").convert(i.mode),
        "invert": ImageOps.invert,
        "blur": lambda i: i.filter(ImageFilter.GaussianBlur(radius=3 * intensity)),
        "sharpen": lambda i: i.filter(ImageFilter.SHARPEN),
        "emboss": lambda i: i.filter(ImageFilter.EMBOSS),
        "edge_enhance": lambda i: i.filter(ImageFilter.EDGE_ENHANCE),
    }

    if filter_name == "sepia":
        gray = img.convert("L")
        w, h = img.size
        sepia_img = gray.copy()
        pixels = sepia_img.load()
        for y in range(h):
            for x in range(w):
                v = pixels[x, y]
                r = min(255, int(v * 1.2))
                g = min(255, int(v * 0.9))
                b = min(255, int(v * 0.6))
                pixels[x, y] = (r, g, b)
        filtered = sepia_img.convert("RGB")
    elif filter_name in filters:
        filtered = filters[filter_name](img.convert("RGB"))
    else:
        return [TextContent(type="text",
            text=json.dumps({"error": f"Unknown filter: {filter_name}"}, indent=2))]

    # Blend with original if intensity < 1.0
    if intensity < 1.0:
        filtered = Image.blend(original.convert("RGB"), filtered.convert("RGB"), intensity)

    return [TextContent(type="text", text=json.dumps({
        "filter": filter_name,
        "intensity": intensity,
        "data": _image_to_b64(filtered),
    }, indent=2))]

@server.tool()
async def extract_colors(
    image_data: str,
    count: int = 5,
) -> list[TextContent]:
    """Extract dominant colors from an image using k-means clustering.

    Args:
        image_data: Base64-encoded image
        count: Number of dominant colors to extract (1-20)
    """
    from PIL import Image

    img = _load_image(image_data)
    # Reduce size for performance
    img = img.resize((150, 150))
    if img.mode == "RGBA":
        img = img.convert("RGB")

    # Simple color quantization
    pixels = list(img.getdata())
    # Simplified: use histogram-based extraction
    color_counts = Counter(pixels[:5000])  # Sample 5000 pixels
    dominant = color_counts.most_common(min(count, 20))

    result = []
    total = sum(c for _, c in dominant)
    for rgb, cnt in dominant:
        result.append({
            "hex": f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}",
            "rgb": list(rgb),
            "percentage": round(cnt / total * 100, 1),
        })

    return [TextContent(type="text", text=json.dumps({
        "dominant_colors": result,
        "total_colors_sampled": len(color_counts),
    }, indent=2))]

@server.tool()
async def create_placeholder(
    width: int = 800,
    height: int = 600,
    color: str = "#cccccc",
    text: str = "",
) -> list[TextContent]:
    """Generate a placeholder image with specified dimensions and color.

    Args:
        width: Image width in pixels (max 4000)
        height: Image height in pixels (max 4000)
        color: Hex color code or name (e.g. "#ff0000" or "red")
        text: Optional text to overlay on the image
    """
    from PIL import Image, ImageDraw, ImageFont

    width = min(width, 4000)
    height = min(height, 4000)

    img = Image.new("RGB", (width, height), color)
    draw = ImageDraw.Draw(img)

    if text:
        # Draw centered text
        try:
            font_size = min(width, height) // 10
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (width - tw) // 2
        y = (height - th) // 2
        draw.text((x, y), text, fill="#ffffff", font=font)

    # Draw border
    draw.rectangle([0, 0, width - 1, height - 1], outline="#333333", width=2)

    return [TextContent(type="text", text=json.dumps({
        "width": width,
        "height": height,
        "color": color,
        "text": text,
        "data": _image_to_b64(img),
    }, indent=2))]

@server.tool()
async def ocr_extract(image_data: str, language: str = "eng") -> list[TextContent]:
    """Extract text from an image using OCR (Tesseract).

    Args:
        image_data: Base64-encoded image
        language: OCR language code (e.g. "eng", "fra", "deu", "jpn", "chi_sim")
    """
    try:
        import pytesseract
    except ImportError:
        return [TextContent(type="text", text=json.dumps({
            "error": "pytesseract not installed. Run: pip install pytesseract",
            "note": "Also requires Tesseract OCR engine installed on the system.",
        }, indent=2))]

    img = _load_image(image_data)
    text = pytesseract.image_to_string(img, lang=language)
    data = pytesseract.image_to_data(img, lang=language, output_type=pytesseract.Output.DICT)

    # Build word-level result
    words = []
    for i in range(len(data["text"])):
        if data["text"][i].strip():
            words.append({
                "text": data["text"][i],
                "confidence": data["conf"][i],
                "bbox": {
                    "x": data["left"][i],
                    "y": data["top"][i],
                    "w": data["width"][i],
                    "h": data["height"][i],
                },
            })

    return [TextContent(type="text", text=json.dumps({
        "text": text.strip(),
        "language": language,
        "word_count": len(words),
        "avg_confidence": round(
            sum(w["confidence"] for w in words) / len(words), 1
        ) if words else 0,
        "words": words[:200],
    }, indent=2))]

@server.tool()
async def create_collage(
    images: list[str],
    columns: int = 3,
    cell_size: int = 200,
) -> list[TextContent]:
    """Create a collage by arranging multiple images in a grid.

    Args:
        images: List of base64-encoded images
        columns: Number of columns in the grid
        cell_size: Each cell will be resized to this square size
    """
    from PIL import Image

    if not images:
        return [TextContent(type="text", text=json.dumps({"error": "No images provided"}, indent=2))]

    # Load and resize all images
    cells = []
    for img_b64 in images[:25]:  # Max 25 images
        img = _load_image(img_b64)
        img.thumbnail((cell_size, cell_size), Image.LANCZOS)
        # Center in square
        square = Image.new("RGBA", (cell_size, cell_size), (0, 0, 0, 0))
        x = (cell_size - img.width) // 2
        y = (cell_size - img.height) // 2
        square.paste(img, (x, y))
        cells.append(square)

    # Arrange in grid
    rows = (len(cells) + columns - 1) // columns
    collage = Image.new("RGBA", (columns * cell_size, rows * cell_size), (0, 0, 0, 0))

    for i, cell in enumerate(cells):
        row, col = divmod(i, columns)
        collage.paste(cell, (col * cell_size, row * cell_size))

    return [TextContent(type="text", text=json.dumps({
        "images_used": len(cells),
        "grid": f"{columns}x{rows}",
        "cell_size": cell_size,
        "total_size": f"{columns * cell_size}x{rows * cell_size}",
        "data": _image_to_b64(collage),
    }, indent=2))]

# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@server.resource("image://supported-formats")
async def supported_formats() -> str:
    return json.dumps({
        "read_formats": ["PNG", "JPEG", "WebP", "BMP", "GIF", "TIFF", "ICO"],
        "operations": ["info", "crop", "filters", "extract_colors", "ocr", "placeholder", "collage"],
        "filters": ["grayscale", "sepia", "invert", "blur", "sharpen", "emboss", "edge_enhance"],
    }, indent=2)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

@server.prompt(
    name="image-editor",
    description="Guided image editing workflow with step-by-step instructions",
    arguments={
        "task": {
            "type": "string",
            "enum": ["social_media", "product_photo", "document_scan", "artistic", "batch_prep"],
            "description": "What kind of image editing task?",
            "required": True,
        },
    },
)
async def image_editor_prompt(task: str) -> dict:
    workflows = {
        "social_media": "1) Use image_info to check dimensions. 2) Crop to 1:1 square with image_crop. 3) Apply sharpen filter. 4) Resize to 1080x1080. 5) Add text with create_placeholder.",
        "product_photo": "1) Use image_info to check format. 2) Extract dominant colors to verify product color accuracy. 3) Apply slight sharpen. 4) Create a white-background placeholder and compose with create_collage.",
        "document_scan": "1) Use image_info. 2) Apply grayscale filter. 3) Enhance contrast (use invert+edge_enhance). 4) Run OCR with ocr_extract to extract text.",
        "artistic": "1) Use image_info. 2) Try sepia filter. 3) Extract dominant colors for palette. 4) Apply edge_enhance for sketch effect. 5) Create a collage of original + 3 filtered versions.",
        "batch_prep": "1) Use image_info on each. 2) Identify common dimensions. 3) Use batch processing for thumbnails. 4) Create a collage preview of all images.",
    }
    return {
        "messages": [{
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""You are an image editing assistant. The user wants to: {task}.

Workflow:
{workflows.get(task, workflows['social_media'])}

For each step, use the appropriate tool and explain what you're doing. After each transformation, describe the result before moving to the next step.

At the end, provide:
- Summary of all edits applied
- Before/after comparison of key attributes (size, format, colors)
- The final image data""",
            },
        }],
    }

# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

async def main():
    transport = StdioServerTransport()
    await server.run(transport)

if __name__ == "__main__":
    asyncio.run(main())
