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
    """Recomandă o carte și include rezumatul prin tool calling, ANCORAT în candidații RAG."""
    from app.tools import build_get_summary_tool_for_titles, get_all_titles  # lazy import ca să evităm cicluri

    # 1) context din RAG
    top = retrieve(query, top_k=top_k) or []
    context = _format_context(top)

    # titluri permise = din candidați; fallback pe toate (dacă retrieverul nu găsește nimic)
    allowed_titles = [r["title"] for r in top if r.get("title")] or get_all_titles()

    # 2) mesaje + instrucțiuni stricte
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

    # 3) PRIMUL apel
    first = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        tools=[tool],
        tool_choice="auto",
        temperature=0.1,  # mai puțină „creativitate”
    )
    msg = first.choices[0].message

    # 4) Tool-call + VALIDARE titlu
    if getattr(msg, "tool_calls", None):
        import json
        tc = msg.tool_calls[0]
        if tc.function and tc.function.name == "get_summary_by_title":
            args = json.loads(tc.function.arguments or "{}")
            title = (args.get("title") or "").strip()
            if title not in allowed_titles:
                title = allowed_titles[0]  # fallback sigur
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
                temperature=0.1,
            )
            return followup.choices[0].message.content

    # 5) fallback: dacă nu a făcut tool-call, alegem top-1 și servim rezumatul noi
    chosen = allowed_titles[0] if allowed_titles else "(n/a)"
    try:
        summary = get_summary_by_title(chosen)
    except Exception:
        summary = "(nu am găsit rezumatul)"
    return f"Titlu: {chosen}\nDe ce:\n• potrivire din context\n• …\n• …\nNote: —\nRezumat:\n{summary}"