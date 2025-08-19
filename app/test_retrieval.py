# app/test_retrieval.py
from app.retrieval import retrieve

query = "vreau o carte despre prietenie si magie"
results = retrieve(query, top_k=3)

for r in results:
    print(f"- {r['title']}  (dist={r['distance']})")
    print(f"  themes: {r['themes']}")
    print(f"  {r['preview']}\n")
