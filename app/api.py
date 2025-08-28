from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.chat import recommend_with_summary
from app.moderation import check_inappropriate
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from app.imagegen import generate_book_image

app = FastAPI(title="Smart Librarian API")

router = APIRouter()

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



class RecommendReq(BaseModel):
    question: str

@app.post("/api/recommend")
def api_recommend(req: RecommendReq):
    flagged, info = check_inappropriate(req.question)
    if flagged:
        return {
            "answer": (
                "Îți pot oferi recomandări imediat, dar te rog să reformulezi "
                "fără cuvinte jignitoare. Mulțumesc pentru înțelegere! 🙂"
            ),
            "picked_title": None,
            "moderated": True,
            "info": info,
        }

    return recommend_with_summary(req.question, top_k=5)

class ImageReq(BaseModel):
    title: str
    hint: str | None = ""
    style: str | None = "cinematic cover"
    size: str | None = "1024x1024"

@app.post("/api/image")
def api_image(req: ImageReq):
    title = (req.title or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title required.")
    flagged, _ = check_inappropriate(f"{title} {req.hint or ''}")
    if flagged:
        raise HTTPException(status_code=400, detail="Text nepotrivit pentru imagine.")
    try:
        img_bytes, ctype, fname = generate_book_image(
            title=title,
            hint=req.hint or "",
            style=req.style or "cinematic cover",
            size=req.size or "1024x1024",
        )
        return Response(
            content=img_bytes,
            media_type=ctype,
            headers={"Content-Disposition": f'inline; filename="{fname}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image error: {e}")