# app/moderation.py
from __future__ import annotations
import os, re, unicodedata
from typing import Dict, Tuple, List

try:
    from openai import OpenAI
except Exception:  # openai nu e obligatoriu pentru filtrul local
    OpenAI = None  # type: ignore

def _normalize(text: str) -> str:
    # lower + fără diacritice, ca să prindem „tâmpit/tampit” etc.
    t = unicodedata.normalize("NFKD", text)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    return t.lower()

# listă minimală (deliberat fără insultă gravă/ură explicită)
# liste/regex pentru cuvinte nepotrivite (RO/EN)
# Ideea: pentru română folosim rădăcini + sufixe scurte (0–4 litere) ca să prindem vocativul: "prostule", "idiotule", "tampitule".
def _mk_root_pattern(root: str) -> str:
    # limite de cuvânt fără să prindem compuse lungi (ex. 'prosthetic' nu se potrivește: are >4 litere după 'prost')
    return rf"(?<!\w){root}[a-z]{{0,4}}(?!\w)"

_INSULT_ROOTS_RO = ["prost", "idiot", "tampit"]  # poți adăuga ușor alte rădăcini aici
_BAD_PATTERNS = [
    # EN uzuale
    r"(?<!\w)f\*?u?c?k(?!\w)",       # fuck, f*ck, fck
    r"(?<!\w)s\*?h?i?t(?!\w)",       # shit, s*it
    r"(?<!\w)bastard(?!\w)",
    r"(?<!\w)suck(?!\w)",
    # RO uzuale (fără rădăcini)
    r"(?<!\w)rahat(?!\w)",
    r"(?<!\w)du-?te\s+(dracului|naibii)(?!\w)",
] + [_mk_root_pattern(r) for r in _INSULT_ROOTS_RO]

_REGEXES = [re.compile(pat, re.IGNORECASE) for pat in _BAD_PATTERNS]

def _local_hits(text: str) -> List[str]:
    nt = _normalize(text)
    hits: List[str] = []
    for rx in _REGEXES:
        for m in rx.finditer(nt):
            # ia primul grup non-empty sau întreaga potrivire
            g = next((grp for grp in m.groups() if grp), m.group(0))
            hits.append(g)
    # unic, în ordinea apariției
    return list(dict.fromkeys(hits))


def check_inappropriate(text: str) -> Tuple[bool, Dict]:
    """
    Întoarce (flagged, info). Dacă flagged=True, NU mai trimitem promptul la LLM.
    1) Filtru local pe cuvinte.
    2) (opțional) OpenAI Moderation pentru cazuri mai subtile.
    """
    hits = _local_hits(text)
    if hits:
        return True, {"source": "local", "hits": hits}

    use_openai = os.getenv("USE_OPENAI_MODERATION", "1").lower() in ("1", "true", "yes")
    if use_openai and OpenAI is not None:
        try:
            client = OpenAI()
            resp = client.moderations.create(model="omni-moderation-latest", input=text)
            res = resp.results[0]
            if res.flagged:
                cats = [k for k, v in res.categories.items() if v]
                return True, {"source": "openai", "categories": cats}
        except Exception:
            # în caz de eroare de rețea/cheie, trecem mai departe fără blocare
            pass

    return False, {}
