from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.chat import recommend_with_summary
from app.moderation import check_inappropriate

app = FastAPI(title="Smart Librarian API")

@app.get("/health")
def health():
    return {"status": "ok"}

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

# @app.post("/api/recommend", response_model=RecOut)
# def api_recommend(payload: QueryIn):
#     ans = recommend_with_summary(payload.question, top_k=payload.k or 4)
#     return {"answer": ans}

# fragment în handlerul /api/recommend
from fastapi import APIRouter
from pydantic import BaseModel
from app.chat import recommend_with_summary
from app.moderation import check_inappropriate

router = APIRouter()

class RecommendReq(BaseModel):
    question: str

@app.post("/api/recommend")
def api_recommend(req: RecommendReq):
    flagged, info = check_inappropriate(req.question)
    if flagged:
        # răspuns politicos, fără a trimite promptul la RAG/LLM
        return {
            "answer": (
                "Îți pot oferi recomandări imediat, dar te rog să reformulezi "
                "fără cuvinte jignitoare. Mulțumesc pentru înțelegere! 🙂"
            ),
            "picked_title": None,
            "moderated": True,
            "info": info,  # util pentru debugging; poți elimina în producție
        }

    # continuăm fluxul normal
    return recommend_with_summary(req.question, top_k=5)
