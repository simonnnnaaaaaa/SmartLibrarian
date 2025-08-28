import os
from openai import OpenAI
from app.retrieval import retrieve
from app.tools import get_summary_by_title


CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")

def _format_context(results):
    lines = []
    for r in results:
        lines.append(f"[{r['title']}] {r['preview']}")
    return "\n---\n".join(lines)

def recommend(query: str, top_k: int = 4) -> str:
    top = retrieve(query, top_k=top_k)
    context = _format_context(top)

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

    client = OpenAI()
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.4,
    )
    return resp.choices[0].message.content


def recommend_with_summary(query: str, top_k: int = 4) -> str:
    from app.tools import build_get_summary_tool_for_titles, get_all_titles

    top = retrieve(query, top_k=top_k) or []
    context = _format_context(top)

    allowed_titles = [r["title"] for r in top if r.get("title")] or get_all_titles()

    system = (
        "Ești Smart Librarian. Folosind DOAR contextul primit, alege o SINGURĂ carte din fragmente. "
        "NU inventa titluri. Apoi apelează EXACT o dată get_summary_by_title(title) cu un titlu "
        "din lista admisă.\n"
        "Formatul final:\n"
        "Titlu: <titlu>\n"
        "De ce:\n"
        "• <motiv 1 scurt din context>\n"
        "• <motiv 2 scurt din context>\n"
        "• <motiv 3 scurt din context>\n"
        "Note: <o propoziție despre ton/teme>\n"
        "Rezumat:\n"
        "<TEXTUL întors de tool, nemodificat>"
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": query},
        {"role": "system", "content": f"CONTEXT RAG (fragmente):\n{context}\n\nTitluri admise: {allowed_titles}"},
    ]

    client = OpenAI()
    tool = build_get_summary_tool_for_titles(allowed_titles)

    first = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        tools=[tool],
        tool_choice="auto",
        temperature=0.1,
    )
    msg = first.choices[0].message

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
            return {
                "answer": followup.choices[0].message.content,
                "picked_title": title or None,
            }

    return {
        "answer": msg.content or "Nu am putut genera un răspuns.",
        "picked_title": None,
    }