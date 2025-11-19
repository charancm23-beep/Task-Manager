# engine/clarity.py
"""
Clarity scoring. Prefer spaCy when available, but fall back to the
`nlp` implementation in `utils.nlp` if spaCy isn't installed so the
module can be imported in constrained environments (e.g., CI or test
environments without heavy binaries).
"""
try:
    import spacy
    from utils.nlp import get_sentence_complexity
    # Load spaCy model
    nlp = spacy.load('en_core_web_sm')
except Exception:
    from utils.nlp import get_sentence_complexity, nlp

def calculate_clarity(
    transcript: str,
    filler_count: int,
    speech_rate: float,
    duration: float
) -> dict:
    sentences = len(list(nlp(transcript).sents))
    wpm = speech_rate
    filler_ratio = filler_count / max(1, len(transcript.split()))

    # Enhanced scoring with stronger complexity penalties
    complexity = get_sentence_complexity(transcript)
    grammar_score = 100 if complexity < 20 else (80 if complexity < 25 else 60)  # Graduated complexity penalties
    pace_score = 100 if 120 <= wpm <= 160 else max(0, 100 - abs(wpm - 140) * 1.5)
    filler_penalty = min(60, filler_ratio * 600)

    # Base score from grammar and pace
    base_score = (grammar_score * 0.6 + pace_score * 0.4)
    clarity = base_score - filler_penalty

    insights = []
    if filler_count > 5: insights.append("Too many filler words")
    if wpm > 160: insights.append("Slow down for clarity")

    return {"score": max(0, min(100, round(clarity))), "insights": "; ".join(insights) or "Clear speech"}