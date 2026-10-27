import re
from typing import Dict, List

from app.db import fetch_all

STOP_WORDS = {
    "the","a","an","and","or","to","of","for","in","on","is","are","this","that",
    "with","before","after","be","by","it","as","at","from","your","you","we","our",
    "status","summary","summarize"
}

def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-zA-Z0-9_]+", text.lower()) if t not in STOP_WORDS}


def search_documents(query: str, allowed_classifications: List[str]) -> Dict[str, list]:
    q_tokens = _tokens(query)
    docs = fetch_all("SELECT doc_id, title, classification, content FROM documents")
    allowed = []
    blocked = []
    for doc in docs:
        text_tokens = _tokens(f"{doc['title']} {doc['content']}")
        overlap = len(q_tokens & text_tokens)
        if overlap <= 0:
            continue
        score = round(overlap / max(len(q_tokens), 1), 3)
        hit = {
            "doc_id": doc["doc_id"],
            "title": doc["title"],
            "classification": doc["classification"],
            "score": score,
            "content": doc["content"],
        }
        if doc["classification"] in allowed_classifications:
            allowed.append(hit)
        else:
            blocked.append(hit["doc_id"])
    allowed.sort(key=lambda x: x["score"], reverse=True)
    return {"results": allowed[:5], "blocked_matches": blocked}
