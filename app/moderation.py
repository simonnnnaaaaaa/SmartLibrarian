from __future__ import annotations
import os, re, unicodedata
from typing import Dict, Tuple, List

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


def _normalize(text: str) -> str:
    t = unicodedata.normalize("NFKD", text)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    return t.lower()


def _mk_root_pattern(root: str) -> str:
    return rf"(?<!\w){root}[a-z]{{0,4}}(?!\w)"


_INSULT_ROOTS_RO = ["prost", "idiot", "tampit"]
_BAD_PATTERNS = [
                    r"(?<!\w)f\*?u?c?k(?!\w)",
                    r"(?<!\w)s\*?h?i?t(?!\w)",
                    r"(?<!\w)bastard(?!\w)",
                    r"(?<!\w)suck(?!\w)",
                    r"(?<!\w)rahat(?!\w)",
                    r"(?<!\w)du-?te\s+(dracului|naibii)(?!\w)",
                ] + [_mk_root_pattern(r) for r in _INSULT_ROOTS_RO]

_REGEXES = [re.compile(pat, re.IGNORECASE) for pat in _BAD_PATTERNS]


def _local_hits(text: str) -> List[str]:
    nt = _normalize(text)
    hits: List[str] = []
    for rx in _REGEXES:
        for m in rx.finditer(nt):
            g = next((grp for grp in m.groups() if grp), m.group(0))
            hits.append(g)
    return list(dict.fromkeys(hits))


def check_inappropriate(text: str) -> Tuple[bool, Dict]:
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
            pass

    return False, {}
