# app/ingest.py
import os, uuid
from pathlib import Path
from openai import OpenAI
import chromadb
from chromadb.config import Settings

from app.data_utils import load_books  # din pasul 2

DB_DIR = Path(__file__).resolve().parents[1] / ".chroma"  # folder local pentru Chroma

def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Setează OPENAI_API_KEY înainte de rulare.")

    books = load_books()

    # 1) pregătim textele ce vor fi indexate
    documents, metadatas, ids = [], [], []
    for b in books:
        doc = f"Titlu: {b['title']}\nTeme: {', '.join(b['themes'])}\nRezumat: {b['summary']}"
        documents.append(doc)
        metadatas.append({
            "title": str(b["title"]),
            "themes": ", ".join(map(str, b.get("themes", [])))  # serializăm lista într-un șir
        })

        ids.append(str(uuid.uuid4()))

    # 2) embeddings cu OpenAI
    client = OpenAI()
    resp = client.embeddings.create(model="text-embedding-3-small", input=documents)
    vectors = [d.embedding for d in resp.data]

    # 3) (re)creăm colecția Chroma
    db = chromadb.PersistentClient(path=str(DB_DIR), settings=Settings(allow_reset=True))
    try:
        db.delete_collection("books")
    except Exception:
        pass
    coll = db.create_collection("books")

    # 4) adăugăm documentele
    coll.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=vectors)

    print(f"Ingestare completă: {len(documents)} documente în {DB_DIR} (colecția 'books').")

if __name__ == "__main__":
    main()
