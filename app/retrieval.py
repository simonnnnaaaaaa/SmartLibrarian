import os
from pathlib import Path
from openai import OpenAI
import chromadb
from chromadb.config import Settings

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

DB_DIR = Path(__file__).resolve().parents[1] / ".chroma"


def _embed(text: str) -> list[float]:
    client = OpenAI()
    model = os.getenv("EMBEDDING_MODEL", EMBEDDING_MODEL)
    resp = client.embeddings.create(model=model, input=[text])
    return resp.data[0].embedding


if __name__ == "__main__":
    v = _embed("test embedding")
    print("lungime vector:", len(v))
    print("primele 3 valori:", v[:3])


def retrieve(query: str, top_k: int = 4):
    q_vec = _embed(query)

    db = chromadb.PersistentClient(path=str(DB_DIR), settings=Settings(allow_reset=False))
    coll = db.get_or_create_collection("books")

    res = coll.query(query_embeddings=[q_vec], n_results=top_k)

    docs = res["documents"][0]
    metas = res["metadatas"][0]
    dists = res.get("distances", [[None] * len(docs)])[0]

    out = []
    for doc, meta, dist in zip(docs, metas, dists):
        out.append({
            "title": meta.get("title"),
            "themes": meta.get("themes"),
            "distance": dist,  # mai mic = mai similar
            "preview": (doc[:160] + ("..." if len(doc) > 160 else "")),
        })
    return out
