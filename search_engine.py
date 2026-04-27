import os, re, sys, json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

def load_model():
    return TfidfVectorizer(stop_words='english')


# ── Text extraction ──

def read_txt(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def read_pdf(path):
    import fitz
    doc = fitz.open(path)
    text = "".join(page.get_text() for page in doc)
    doc.close()
    return text

def read_docx(path):
    from docx import Document
    return "\n".join(p.text for p in Document(path).paragraphs if p.text.strip())

def extract_text(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".txt":  return read_txt(path)
    if ext == ".pdf":  return read_pdf(path)
    if ext == ".docx": return read_docx(path)
    return ""


# ── Preprocessing ──

def clean(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\x20-\x7E\n]', '', text)
    return text.strip()


# ── Sentence-aware chunking ──
# Old way: split every N words blindly -> cuts sentences mid-way, loses meaning
# New way: split into sentences first, then group them -> meaning stays intact

def split_sentences(text):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 20]

def chunk(text, max_words=100, overlap_sentences=1):
    sentences = split_sentences(text)
    chunks = []
    i = 0
    while i < len(sentences):
        group, word_count, j = [], 0, i
        while j < len(sentences) and word_count < max_words:
            group.append(sentences[j])
            word_count += len(sentences[j].split())
            j += 1
        if group:
            chunks.append(" ".join(group))
        i = j - overlap_sentences if j - overlap_sentences > i else j
    return chunks


# ── Cosine similarity ──

def cosine(a, b):
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom else 0.0


# ── MMR (Maximal Marginal Relevance) re-ranking ──
# Problem: plain cosine top-5 often returns near-identical chunks (repetitive)
# MMR fixes this: balances relevance to query vs diversity from each other
# lambda_=0.7 means 70% relevance + 30% diversity (tunable)

def mmr(query_emb, candidates, top_n, lambda_=0.7):
    if not candidates:
        return []
    selected, remaining = [], list(range(len(candidates)))
    while len(selected) < top_n and remaining:
        scores = []
        for idx in remaining:
            relevance = cosine(query_emb, candidates[idx]["embedding"])
            redundancy = max(
                (cosine(candidates[idx]["embedding"], candidates[s]["embedding"]) for s in selected),
                default=0.0
            )
            scores.append((idx, lambda_ * relevance - (1 - lambda_) * redundancy))
        best = max(scores, key=lambda x: x[1])[0]
        selected.append(best)
        remaining.remove(best)
    return [candidates[i] for i in selected]


# ── Build index ──

def build_index(file_paths, model):
    index = []
    all_chunks = []
    file_map = []

    for path in file_paths:
        text = clean(extract_text(path))
        text = text[:20000]
        if not text:
            continue

        pieces = chunk(text)
        for p in pieces:
            all_chunks.append(p)
            file_map.append(os.path.basename(path))
            
    all_chunks = all_chunks[:300]  # LIMIT TOTAL CHUNKS
    file_map = file_map[:300]

    if not all_chunks:
        return []

    # FIT ONLY ONCE
    embeddings = model.fit_transform(all_chunks).toarray()

    for piece, emb, fname in zip(all_chunks, embeddings, file_map):
        index.append({
            "filename": fname,
            "chunk_text": piece,
            "embedding": emb
        })

    return index


# ── Search ──
# Step 1: top 20 candidates by cosine (wide net)
# Step 2: re-rank with MMR -> diverse + accurate final results

def semantic_search(query, index, model, top_n=5):
    q_emb = model.transform([query]).toarray()[0]
    scored = sorted(index, key=lambda x: cosine(q_emb, x["embedding"]), reverse=True)
    candidates = scored[:min(20, len(index))]
    final = mmr(q_emb, candidates, top_n)
    return [
        {"rank": i+1, "filename": item["filename"],
         "chunk_text": item["chunk_text"],
         "score": round(cosine(q_emb, item["embedding"]), 4)}
        for i, item in enumerate(final)
    ]


# ── CLI entry point (called by Java) ──

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: python search_engine.py <query> <file1> ..."}))
        sys.exit(1)

    query, files = sys.argv[1], sys.argv[2:]
    model = load_model()
    index = build_index(files, model)

    if not index:
        print(json.dumps({"error": "No content indexed."}))
        sys.exit(1)

    results = semantic_search(query, index, model)
    print(json.dumps({"query": query, "results": [
        {"rank": r["rank"], "filename": r["filename"],
         "score": r["score"], "preview": r["chunk_text"][:300]}
        for r in results
    ]}, indent=2))
