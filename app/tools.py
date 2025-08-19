from pathlib import Path
import json

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "book_summaries.json"

def get_summary_by_title(title: str) -> str:
    """Returnează rezumatul pentru titlul dat (case-insensitive)."""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)
    for item in items:
        if item["title"].strip().lower() == title.strip().lower():
            return item["summary"]
    raise ValueError(f"Titlul nu a fost găsit: {title}")
