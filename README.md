Chatbot AI care recomandă cărți în funcție de interesele utilizatorului, folosind OpenAI + RAG (ChromaDB), apoi completează recomandarea cu rezumatul complet printr-un tool local. UI în React (Vite, JS). Conține și image generation și Text-to-Speech în browser.

Flow:
1. Utilizatorul scrie o întrebare naturală (ex: „Vreau o carte despre prietenie și magie”).
2. Backend:
  - caută semantic în ChromaDB (OpenAI embeddings) – RAG;
  - trece printr-un filtru de limbaj nepotrivit (nu trimite la LLM dacă e ofensator);
  - cheamă modelul de chat cu contextul; modelul alege un singur titlu din rezultate;
  -apelează tool-ul local get_summary_by_title(title) → adaugă rezumatul complet.

3. UI afișează titlul + motive + rezumat și poate genera o imagine reprezentativă pentru carte.
4. Opțional, utilizatorul poate asculta răspunsul (Web Speech API: Ascultă/Pauză/Continuă/Oprește).

Arhitectură & foldere
smart_librarian/
├─ app/
│  ├─ api.py               # rutele FastAPI (/health, /api/recommend, /api/image)
│  ├─ chat.py              # orchestrare chat + tool-calling + format răspuns JSON
│  ├─ retrieval.py         # ChromaDB client + query semantic (OpenAI embeddings)
│  ├─ ingest.py            # încărcare dataset în ChromaDB (.chroma/)
│  ├─ tools.py             # get_summary_by_title() din data/book_summaries.json
│  ├─ moderation.py        # filtru limbaj (regex + derivate: “prostule”, etc.)
│  ├─ imagegen.py          # /api/image – OpenAI gpt-image-1 + cache .img_cache/
│  └─ data/
│     └─ book_summaries.json  # 10+ cărți cu titlu + rezumat + teme
├─ .chroma/                # vector store local (generat)
├─ .img_cache/             # cache imagini generate (generat)
├─ main.py                 # pornire app FastAPI (uvicorn)
└─ smart-librarian-ui/     # UI (Vite + React JS)
   └─ src/
      ├─ App.jsx           # formular, răspuns, buton imagine, Web TTS
      ├─ lib/api.js        # client API (fetch)
      ├─ styles.css        # stiluri (dark theme + responsive)
      └─ index.css

CerințeȘ
Python 3.10+
Node 18+ (sau mai nou)
Un OpenAI API key (OPENAI_API_KEY)

Configurare (backend)
1. Creează și activează un virtualenv (opțional):

python -m venv .venv
# Windows PowerShell:
. .venv/Scripts/Activate.ps1
# Linux/Mac:
source .venv/bin/activate

2. Instalează dependențele:
   
pip install -r requirements.txt

3. Variabile de mediu (poți folosi un .env în root):

# obligatoriu
OPENAI_API_KEY=sk-...

# opțional (au valori implicite sensibile)
CHAT_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
IMAGE_MODEL=gpt-image-1

4. Ingest – creează colecția ChromaDB din book_summaries.json:

python app/ingest.py

5. Rulează backend-ul:

uvicorn main:app --reload
# => http://localhost:8000/docs  (Swagger)

Configurare (frontend – React)Ș

1. În directorul smart-librarian-ui, creează .env.local:

VITE_API_BASE_URL=http://localhost:8000

2. Instalează și rulează:

cd smart-librarian-ui
npm install
npm run dev
# => http://localhost:5173

Endpoints principale:
- GET /health
health check.

- POST /api/recommend
Body:
{ "question": "Vreau o carte despre prietenie și magie" }
Răspuns:
{
  "answer": "Titlu: ...\nDe ce:\n• ...\n• ...\nNote: ...\nRezumat: ...",
  "picked_title": "Harry Potter and the Sorcerer's Stone"
}

- POST /api/image
Generează o imagine originală (PNG) pentru titlu.
Body:
{ "title": "The Hobbit", "hint": "aventură și prietenie", "style": "cinematic cover" }
Răspuns: image/png (servit ca fișier; UI îl afișează inline).
Cache: fișiere în .img_cache/.

UI – ce include:
- Form cu textarea → trimite la /api/recommend.
- Afișează titlul, motivele, nota și rezumatul.
- Generează imagine → /api/image → <img> inline (fără download obligatoriu).
- Text-to-Speech (fără backend): Web Speech API – Ascultă / Pauză / Continuă / Oprește.
- Funcționează în Chrome/Edge/Safari. Nu consumă API.

Moderare (limbaj nepotrivit)
- Filtru local (regex + rădăcini cu sufixe) blochează mesaje jignitoare (prost, prostule, idiotule, tâmpit, etc.).
- Dacă e detectat: răspuns politicos, nu trimite promptul la LLM / TTS / imagine.

Exemple de întrebări:
„Vreau o carte despre libertate și control social.”
„Ce-mi recomanzi dacă iubesc poveștile fantastice?”
„Ce este 1984?”

Troubleshooting:
- UI afișează „Nu am primit răspuns”
Asigură-te că backendul răspunde JSON {answer, picked_title}. Dacă nu, UI extrage Titlu: din text, dar e mai bine să rulezi backend-ul actualizat.
- 404 /api/recommend
Verifică VITE_API_BASE_URL din smart-librarian-ui/.env.local și că backendul rulează pe :8000.
- OpenAI errors / modele indisponibile
Verifică OPENAI_API_KEY.
EMBEDDING_MODEL=text-embedding-3-small trebuie să existe în cont.
Pentru imagini, IMAGE_MODEL=gpt-image-1.
- Reset vector store
Șterge .chroma/ și rulează din nou python app/ingest.py.
- Windows PowerShell: “running scripts is disabled”
Deschide VS Code → Terminal integrat PowerShell (User) sau cere IT să permită ExecutionPolicy RemoteSigned pentru user.
