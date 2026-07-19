"""Retrieval for the chatbot — a small, hand-written BM25 index.

Owner: H.G.P.C. Sagara (PM & Integration Dev)

Why BM25 and not embeddings? The knowledge base is a handful of markdown
files, and BM25 (the ranking function behind classic search engines such as
Lucene/Elasticsearch) ranks them well with zero external services, zero cost
and no multi-gigabyte ML dependencies. The whole retriever is ~60 lines of
plain Python, which also makes it easy to explain in the viva.

How it works:
    1. Every markdown file in ``knowledge/`` is split into chunks on ``##``
       headings, so each chunk covers one topic.
    2. Each chunk is tokenised into lowercase words.
    3. ``retrieve(query)`` scores every chunk against the query with the
       standard BM25 formula and returns the top-k chunks.

The index is built once on first use and cached in a module global.
"""

import math
import re
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"

# BM25 constants — the textbook defaults.
K1 = 1.5
B = 0.75

_WORD_RE = re.compile(r"[a-z0-9]+")

# Lazily built index: list of chunk dicts + document-frequency table.
_index = None


def _tokenize(text):
    """Lowercase a string and return its alphanumeric words."""
    return _WORD_RE.findall(text.lower())


def load_chunks(knowledge_dir=KNOWLEDGE_DIR):
    """Read every markdown file and split it into one chunk per ## section."""
    chunks = []
    for path in sorted(Path(knowledge_dir).glob("*.md")):
        text = path.read_text(encoding="utf-8")
        # Keep the text before the first "## " together with the file title.
        sections = re.split(r"(?m)^## ", text)
        for i, section in enumerate(sections):
            body = section.strip()
            if not body:
                continue
            heading = body.splitlines()[0].lstrip("# ").strip() if i else path.stem
            chunks.append({"source": path.name, "heading": heading, "text": body})
    return chunks


def build_index(knowledge_dir=KNOWLEDGE_DIR):
    """Build the BM25 index over all knowledge chunks and return it."""
    chunks = load_chunks(knowledge_dir)
    doc_freq = {}
    for chunk in chunks:
        chunk["tokens"] = _tokenize(chunk["text"])
        for word in set(chunk["tokens"]):
            doc_freq[word] = doc_freq.get(word, 0) + 1
    total = len(chunks) or 1
    avg_len = sum(len(c["tokens"]) for c in chunks) / total
    return {"chunks": chunks, "doc_freq": doc_freq, "avg_len": avg_len or 1.0}


def _get_index():
    global _index
    if _index is None:
        _index = build_index()
    return _index


def retrieve(query, k=3):
    """Return the top-k knowledge chunks for a query, best first.

    Each result is ``{"source", "heading", "text", "score"}``; chunks that
    match nothing are never returned.
    """
    index = _get_index()
    chunks, doc_freq = index["chunks"], index["doc_freq"]
    n = len(chunks)
    scored = []
    query_words = set(_tokenize(query))

    for chunk in chunks:
        score = 0.0
        doc_len = len(chunk["tokens"])
        for word in query_words:
            tf = chunk["tokens"].count(word)
            if tf == 0:
                continue
            # BM25: idf * tf saturation, normalised by document length.
            idf = math.log(1 + (n - doc_freq[word] + 0.5) / (doc_freq[word] + 0.5))
            score += idf * (tf * (K1 + 1)) / (
                tf + K1 * (1 - B + B * doc_len / index["avg_len"])
            )
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [
        {
            "source": chunk["source"],
            "heading": chunk["heading"],
            "text": chunk["text"],
            "score": round(score, 3),
        }
        for score, chunk in scored[:k]
    ]
