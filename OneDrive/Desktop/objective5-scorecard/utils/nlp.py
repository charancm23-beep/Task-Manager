# utils/nlp.py
"""
Provide NLP helpers. Try to use spaCy and sentence-transformers when available,
but fall back to lightweight implementations when those heavy dependencies
are not installed. The fallbacks are intentionally simple and intended for
local testing or environments where installing large packages isn't possible.
"""
try:
    import spacy
    from sentence_transformers import SentenceTransformer, util

    nlp = spacy.load("en_core_web_sm")
    embedder = SentenceTransformer('all-MiniLM-L6-v2')

    def get_sentence_complexity(transcript: str) -> float:
        doc = nlp(transcript)
        # Use words-per-sentence as a lightweight complexity metric
        lengths = [len(sent.split()) for sent in doc.sents]
        return sum(lengths) / len(lengths) if lengths else 0

    def cosine_similarity(text1: str, text2: str) -> float:
        emb1 = embedder.encode(text1)
        emb2 = embedder.encode(text2)
        return util.cos_sim(emb1, emb2)[0][0].item()

except Exception:
    # Lightweight fallbacks (no external dependencies)
    import re
    import math
    from collections import Counter

    class SimpleDoc:
        def __init__(self, text: str):
            # Very simple sentence splitter
            self._sents = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]

        @property
        def sents(self):
            for s in self._sents:
                yield s

    def nlp(text: str):
        return SimpleDoc(text)

    def get_sentence_complexity(transcript: str) -> float:
        doc = nlp(transcript)
        # For fallbacks, measure words-per-sentence rather than characters
        lengths = [len(sent.split()) for sent in doc.sents]
        return sum(lengths) / len(lengths) if lengths else 0

    def cosine_similarity(text1: str, text2: str) -> float:
        # Token-based cosine similarity without numpy
        t1 = re.findall(r"\w+", text1.lower())
        t2 = re.findall(r"\w+", text2.lower())
        v1 = Counter(t1)
        v2 = Counter(t2)
        dot = sum(v1[k] * v2.get(k, 0) for k in v1)
        mag1 = math.sqrt(sum(v * v for v in v1.values()))
        mag2 = math.sqrt(sum(v * v for v in v2.values()))
        sim = (dot / (mag1 * mag2)) if mag1 and mag2 else 0.0
        # Small smoothing boost to better approximate embedding similarities
        return min(1.0, sim + 0.03)
