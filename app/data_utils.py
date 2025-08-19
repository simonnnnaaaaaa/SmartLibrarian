from pathlib import Path
import json

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "book_summaries.json"

def load_books():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_books(books):
    errors = []
    seen = set()

    if not isinstance(books, list):
        return ["Fișierul trebuie să conțină o listă JSON."]

    for i, b in enumerate(books):
        # title
        t = (b.get("title") or "").strip()
        if not t:
            errors.append(f"[{i}] 'title' lipsă sau gol")
        elif t.lower() in seen:
            errors.append(f"[{i}] titlu duplicat: {t}")
        else:
            seen.add(t.lower())

        # summary
        s = (b.get("summary") or "").strip()
        if len(s.split()) < 5:
            errors.append(f"[{i}] 'summary' prea scurt (minim ~5 cuvinte)")

        # themes
        th = b.get("themes")
        if not isinstance(th, list) or not all(isinstance(x, str) for x in th):
            errors.append(f"[{i}] 'themes' trebuie să fie listă de stringuri")

    if len(books) < 10:
        errors.append("Trebuie minim 10 cărți.")

    return errors

if __name__ == "__main__":
    data = load_books()
    errs = validate_books(data)
    if errs:
        print("Erori de validare:")
        for e in errs:
            print(" -", e)
        raise SystemExit(1)
    print(f"OK: {len(data)} cărți validate.")
