import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from app.core.models import PlaybookDocument


def chunk_text(text: str, size: int = 700, overlap: int = 120) -> list[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(clean):
        chunks.append(clean[start:start + size])
        if start + size >= len(clean):
            break
        start += size - overlap
    return chunks


def search_playbooks(db: Session, query: str, limit: int = 4) -> list[dict]:
    docs = db.query(PlaybookDocument).all()
    candidates: list[tuple[str, str]] = []
    for doc in docs:
        for chunk in chunk_text(doc.content):
            candidates.append((doc.filename, chunk))
    if not candidates:
        return []
    corpus = [query] + [chunk for _, chunk in candidates]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
    matrix = vectorizer.fit_transform(corpus)
    scores = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:limit]
    return [
        {"source": candidates[i][0], "score": round(float(score), 3), "excerpt": candidates[i][1]}
        for i, score in ranked if score > 0
    ]
