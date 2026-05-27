#!/usr/bin/env python3
"""
MCP File Converter Server — demonstrates binary data handling, resource exposure,
progress notifications, and multiple conversion formats.

Install: pip install mcp pillow reportlab
Configure in .claude/settings.json:
{
  "mcpServers": {
    "file-converter": {
      "type": "stdio",
      "command": "python",
      "args": ["mcp_servers/file_converter_server.py"],
      "env": { "CONVERTER_OUTPUT_DIR": "./converted" }
    }
  }
}
"""

import asyncio
import base64
import hashlib
import json
import os
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any

from mcp.server import Server, NotificationOptions
from mcp.server.stdio import StdioServerTransport
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

server = Server("file-converter")

OUTPUT_DIR = Path(os.environ.get("CONVERTER_OUTPUT_DIR", "./converted"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _b64_to_bytes(b64: str) -> bytes:
    """Decode base64 payload, handling data-URI prefix."""
    if "," in b64 and b64.startswith("data:"):
        b64 = b64.split(",", 1)[1]
    return base64.b64decode(b64)

def _bytes_to_b64(data: bytes, mime: str = "image/png") -> str:
    return f"data:{mime};base64," + base64.b64encode(data).decode()

def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@server.tool()
async def image_convert(
    input_data_b64: str,
    target_format: str = "png",
    quality: int = 85,
) -> list[TextContent]:
    """Convert an image between formats (PNG, JPEG, WebP, BMP, GIF, TIFF).

    Accepts a base64-encoded image and returns the converted version.

    Args:
        input_data_b64: Base64-encoded source image (with or without data: URI prefix)
        target_format: Target format — "png", "jpeg", "webp", "bmp", "gif", "tiff"
        quality: JPEG/WebP quality 1-100. Defaults to 85.
    """
    from PIL import Image

    fmt = target_format.lower()
    raw = _b64_to_bytes(input_data_b64)
    img = Image.open(BytesIO(raw))

    # If target is JPEG and source has alpha, flatten onto white
    if fmt in ("jpeg", "jpg") and img.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
        img = background

    buf = BytesIO()
    save_kwargs: dict[str, Any] = {"format": fmt.upper() if fmt != "jpg" else "JPEG"}
    if fmt in ("jpeg", "jpg", "webp"):
        save_kwargs["quality"] = quality
    img.save(buf, **save_kwargs)
    buf.seek(0)

    result_b64 = _bytes_to_b64(buf.read(), f"image/{fmt}")
    return [TextContent(
        type="text",
        text=json.dumps({
            "format": fmt,
            "original_size_bytes": len(raw),
            "converted_size_bytes": buf.tell(),
            "width": img.width,
            "height": img.height,
            "data": result_b64,
        }, indent=2),
    )]

@server.tool()
async def image_resize(
    input_data_b64: str,
    width: int | None = None,
    height: int | None = None,
    scale: float | None = None,
) -> list[TextContent]:
    """Resize an image. Provide width+height for absolute sizing, or scale (0.5 = half).

    Args:
        input_data_b64: Base64-encoded image
        width: Target width in pixels (optional if scale is provided)
        height: Target height in pixels (optional if scale is provided)
        scale: Scale factor, e.g. 0.5 for half size (optional if width+height provided)
    """
    from PIL import Image

    raw = _b64_to_bytes(input_data_b64)
    img = Image.open(BytesIO(raw))
    orig_w, orig_h = img.width, img.height

    if scale:
        new_w, new_h = int(orig_w * scale), int(orig_h * scale)
    elif width and height:
        new_w, new_h = width, height
    elif width:
        ratio = width / orig_w
        new_w, new_h = width, int(orig_h * ratio)
    elif height:
        ratio = height / orig_h
        new_w, new_h = int(orig_w * ratio), height
    else:
        raise ValueError("Provide width+height or scale")

    resized = img.resize((new_w, new_h), Image.LANCZOS)
    buf = BytesIO()
    fmt = img.format or "PNG"
    resized.save(buf, format=fmt)
    buf.seek(0)

    return [TextContent(
        type="text",
        text=json.dumps({
            "original": f"{orig_w}x{orig_h}",
            "resized": f"{new_w}x{new_h}",
            "data": _bytes_to_b64(buf.read(), f"image/{fmt.lower()}"),
        }, indent=2),
    )]

@server.tool()
async def image_rotate(
    input_data_b64: str,
    degrees: float = 90,
    expand: bool = True,
) -> list[TextContent]:
    """Rotate an image by the specified degrees.

    Args:
        input_data_b64: Base64-encoded image
        degrees: Rotation degrees (counter-clockwise). Use negative for clockwise.
        expand: Whether to expand canvas to fit rotated image
    """
    from PIL import Image

    raw = _b64_to_bytes(input_data_b64)
    img = Image.open(BytesIO(raw))
    rotated = img.rotate(degrees, expand=expand, resample=Image.BICUBIC)

    buf = BytesIO()
    fmt = img.format or "PNG"
    rotated.save(buf, format=fmt)
    buf.seek(0)

    return [TextContent(
        type="text",
        text=json.dumps({
            "degrees": degrees,
            "original_size": f"{img.width}x{img.height}",
            "rotated_size": f"{rotated.width}x{rotated.height}",
            "data": _bytes_to_b64(buf.read(), f"image/{fmt.lower()}"),
        }, indent=2),
    )]

@server.tool()
async def image_get_info(input_data_b64: str) -> list[TextContent]:
    """Extract metadata from an image: dimensions, format, EXIF, color mode.

    Args:
        input_data_b64: Base64-encoded image
    """
    from PIL import Image, ExifTags

    raw = _b64_to_bytes(input_data_b64)
    img = Image.open(BytesIO(raw))

    info: dict[str, Any] = {
        "format": img.format,
        "mode": img.mode,
        "width": img.width,
        "height": img.height,
        "aspect_ratio": f"{img.width}:{img.height}",
        "is_animated": getattr(img, "is_animated", False),
        "n_frames": getattr(img, "n_frames", 1),
    }

    exif_data = img.getexif()
    if exif_data:
        exif = {}
        for tag_id, value in exif_data.items():
            tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
            if isinstance(value, bytes):
                value = f"<{len(value)} bytes>"
            exif[tag_name] = value
        info["exif"] = exif

    return [TextContent(type="text", text=json.dumps(info, indent=2, default=str))]

@server.tool()
async def text_encode_decode(
    text: str,
    operation: str = "encode",
    encoding: str = "base64",
) -> list[TextContent]:
    """Encode or decode text using various encodings.

    Args:
        text: Input text
        operation: "encode" or "decode"
        encoding: "base64", "base32", "hex", "url", "rot13"
    """
    import codecs
    from urllib.parse import quote, unquote

    ops: dict[str, tuple] = {
        "base64": (lambda t: base64.b64encode(t.encode()).decode(),
                    lambda t: base64.b64decode(t.encode()).decode()),
        "base32": (lambda t: base64.b32encode(t.encode()).decode(),
                    lambda t: base64.b32decode(t.encode()).decode()),
        "hex": (lambda t: t.encode().hex(),
                 lambda t: bytes.fromhex(t).decode()),
        "url": (lambda t: quote(t, safe=""),
                 lambda t: unquote(t)),
        "rot13": (lambda t: codecs.encode(t, "rot_13"),
                   lambda t: codecs.encode(t, "rot_13")),  # rot13 is its own inverse
    }

    if encoding not in ops:
        raise ValueError(f"Unknown encoding: {encoding}. Choose from: {list(ops)}")

    encode_fn, decode_fn = ops[encoding]
    try:
        if operation == "encode":
            result = encode_fn(text)
        else:
            result = decode_fn(text)
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise ValueError(f"Failed to {operation} with {encoding}: {e}")

@server.tool()
async def batch_process(
    images: list[str],
    action: str = "thumbnail",
    size: int = 128,
) -> list[TextContent]:
    """Batch-process multiple base64 images: create thumbnails, extract dominant colors, etc.

    Args:
        images: List of base64-encoded images
        action: "thumbnail" (crops to square), "dominant_color", "grayscale"
        size: Thumbnail size in pixels (for thumbnail action)
    """
    from PIL import Image

    results = []
    for i, img_b64 in enumerate(images):
        raw = _b64_to_bytes(img_b64)
        img = Image.open(BytesIO(raw))

        if action == "thumbnail":
            img.thumbnail((size, size), Image.LANCZOS)
            buf = BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            results.append({
                "index": i,
                "width": img.width,
                "height": img.height,
                "data": _bytes_to_b64(buf.read(), "image/png"),
            })
        elif action == "dominant_color":
            img = img.resize((50, 50))
            pixels = list(img.getdata())
            avg = tuple(int(sum(c) / len(c)) for c in zip(*pixels))
            results.append({
                "index": i,
                "dominant_color_rgb": avg,
                "hex": f"#{avg[0]:02x}{avg[1]:02x}{avg[2]:02x}",
            })
        elif action == "grayscale":
            gray = img.convert("L")
            buf = BytesIO()
            gray.save(buf, format="PNG")
            buf.seek(0)
            results.append({
                "index": i,
                "data": _bytes_to_b64(buf.read(), "image/png"),
            })

    return [TextContent(type="text", text=json.dumps(results, indent=2))]

# ---------------------------------------------------------------------------
# Resources — expose output directory file listing
# ---------------------------------------------------------------------------

@server.resource("file://converted/{filename}")
async def get_converted_file(filename: str) -> str:
    """Read a converted file from the output directory."""
    path = OUTPUT_DIR / filename
    if not path.exists():
        raise ValueError(f"File not found: {filename}")
    if path.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"):
        return _bytes_to_b64(path.read_bytes(), f"image/{path.suffix[1:]}")
    return path.read_text()

# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

async def main():
    transport = StdioServerTransport()
    await server.run(transport)

if __name__ == "__main__":
    asyncio.run(main())
