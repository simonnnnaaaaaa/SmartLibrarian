from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.chat import recommend_with_summary

app = FastAPI(title="Smart Librarian API")

@app.get("/health")
def health():
    return {"status": "ok"}

# permite front-end local (Vite pe 5173, CRA pe 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryIn(BaseModel):
    question: str
    k: int | None = 4

class RecOut(BaseModel):
    answer: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/recommend", response_model=RecOut)
def api_recommend(payload: QueryIn):
    ans = recommend_with_summary(payload.question, top_k=payload.k or 4)
    return {"answer": ans}