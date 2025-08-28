from __future__ import annotations
import os, base64, hashlib, re
from pathlib import Path
from openai import OpenAI

IMAGE_MODEL = os.getenv("IMAGE_MODEL", "gpt-image-1")
CACHE_DIR = Path(__file__).resolve().parents[1] / ".img_cache"
CACHE_DIR.mkdir(exist_ok=True)

def _ctype() -> str:
    return "image/png"

def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def _cache_key(*parts: str) -> str:
    h = hashlib.sha1("||".join(parts).encode("utf-8")).hexdigest()
    return h

def generate_book_image(title: str, hint: str = "", style: str = "cinematic cover", size: str = "1024x1024") -> tuple[bytes, str, str]:
    prompt = (
        f"Create an original, high-quality book-cover style illustration for the book '{title}'. "
        f"Capture mood and themes. Do not include any text, titles, logos, or real book cover replicas. "
        f"Style: {style}. Themes/Hints: {hint or '—'}."
    )

    key = _cache_key(IMAGE_MODEL, title, hint, style, size)
    path = CACHE_DIR / f"{key}.png"
    if path.exists():
        return path.read_bytes(), _ctype(), f"cover-{_slug(title)}.png"

    client = OpenAI()
    resp = client.images.generate(
        model=IMAGE_MODEL,
        prompt=prompt,
        size=size,
        quality="high",
    )
    b64 = resp.data[0].b64_json
    data = base64.b64decode(b64)
    path.write_bytes(data)
    return data, _ctype(), f"cover-{_slug(title)}.png"
