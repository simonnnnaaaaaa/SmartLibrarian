# app/chat.py
import os
from openai import OpenAI
from app.retrieval import retrieve
from app.tools import get_summary_by_title


CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")

def _format_context(results):
    """Construiește contextul pe care îl dăm modelului (din top-K)."""
    lines = []
    for r in results:
        lines.append(f"[{r['title']}] {r['preview']}")
    return "\n---\n".join(lines)

def recommend(query: str, top_k: int = 4) -> str:
    """Recomandă O SINGURĂ carte folosind contextul RAG."""
    # 1) luăm top-K fragmente din vector store
    top = retrieve(query, top_k=top_k)
    context = _format_context(top)

    # 2) construim mesaje pentru LLM
    system = (
        "Ești Smart Librarian. Primești o întrebare despre preferințe de lectură. "
        "Folosind DOAR contextul primit, recomandă o SINGURĂ carte potrivită "
        "și dă 3–4 motive scurte. Formatează astfel:\n"
        "Titlu: <titlu>\n"
        "De ce: • motiv1 • motiv2 • motiv3\n"
        "Note: menționează ton/teme în 1 propoziție."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": query},
        {"role": "system", "content": f"CONTEXT RAG (fragmente):\n{context}"}
    ]

    # 3) apelăm modelul „mini”
    client = OpenAI()
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.4,
    )
    return resp.choices[0].message.content


def recommend_with_summary(query: str, top_k: int = 4) -> str:
    """Recomandă o carte și, dacă e posibil, include rezumatul prin tool calling."""
    # 1) context din RAG
    top = retrieve(query, top_k=top_k)
    context = _format_context(top)

    # 2) mesaje + instrucțiuni
    system = (
        "Ești Smart Librarian. Folosind DOAR contextul primit, alege o SINGURĂ carte din fragmente. "
        "După ce alegi titlul, TREBUIE să apelezi funcția get_summary_by_title(title) EXACT o dată, "
        "cu titlul EXACT (așa cum apare în context). Răspunsul final trebuie să aibă EXACT acest format:\n\n"
        "Titlu: <titlu>\n"
        "De ce:\n"
        "• <motiv 1 scurt din context>\n"
        "• <motiv 2 scurt din context>\n"
        "• <motiv 3 scurt din context>\n"
        "Note: <o propoziție despre ton/teme din context>\n"
        "Rezumat:\n"
        "<TEXTUL întors de tool, fără parafrazări>"
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": query},
        {"role": "system", "content": f"CONTEXT RAG (fragmente):\n{context}"},
    ]

    # 3) definim tool-ul
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_summary_by_title",
                "description": "Returnează rezumatul complet (3–5 fraze) pentru un titlu exact.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Titlul exact al cărții recomandate."}
                    },
                    "required": ["title"]
                },
            },
        }
    ]

    client = OpenAI()

    # 4) PRIMUL apel: modelul poate decide să cheme tool-ul
    first = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        temperature=0.4,
    )
    msg = first.choices[0].message

    # 5) Dacă a cerut tool-ul, îl executăm local și facem AL DOILEA apel
    if getattr(msg, "tool_calls", None):
        tc = msg.tool_calls[0]
        if tc.function and tc.function.name == "get_summary_by_title":
            import json
            args = json.loads(tc.function.arguments or "{}")
            title = (args.get("title") or "").strip()

            try:
                summary = get_summary_by_title(title)
            except Exception as e:
                summary = f"(Nu am găsit rezumat pentru '{title}': {e})"

            # atașăm tool call + răspunsul tool-ului
            messages.append({"role": "assistant", "content": None, "tool_calls": [tc]})
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "name": "get_summary_by_title",
                "content": summary
            })

            followup = client.chat.completions.create(
                model=CHAT_MODEL,
                messages=messages,
                temperature=0.3,
            )
            return followup.choices[0].message.content

    # 6) Dacă nu a chemat tool-ul, măcar returnăm recomandarea de bază
    return msg.content or "Nu am putut genera un răspuns."
