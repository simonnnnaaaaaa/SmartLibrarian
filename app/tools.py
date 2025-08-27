from pathlib import Path
import json
from typing import List
from copy import deepcopy

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "book_summaries.json"

def get_summary_by_title(title: str) -> str:
    """Returnează rezumatul pentru titlul dat (case-insensitive)."""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)
    for item in items:
        if item["title"].strip().lower() == title.strip().lower():
            return item["summary"]
    raise ValueError(f"Titlul nu a fost găsit: {title}")

def _load_items() -> list[dict]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    # acceptă fie listă simplă, fie {"books":[...]}
    return data.get("books", data) if isinstance(data, dict) else data

def get_all_titles() -> List[str]:
    return [it["title"] for it in _load_items() if it.get("title")]

def build_get_summary_tool_for_titles(allowed_titles: List[str]) -> dict:
    """Schema function-calling care permite DOAR titluri din lista dată."""
    base = {
        "type": "function",
        "function": {
            "name": "get_summary_by_title",
            "description": "Returnează rezumatul complet (3–5 fraze) pentru un titlu exact din lista admisă.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Titlul EXACT al cărții."}
                },
                "required": ["title"]
            },
        },
    }
    tool = deepcopy(base)
    tool["function"]["parameters"]["properties"]["title"]["enum"] = allowed_titles
    return tool