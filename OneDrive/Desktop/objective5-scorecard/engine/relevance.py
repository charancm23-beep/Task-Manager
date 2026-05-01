# engine/relevance.py
"""
Relevance scoring – how well the candidate's answer addresses the question
and covers the expected keywords / concepts.

Prefer sentence-transformers semantic similarity when available; falls back
to the token-based cosine similarity already implemented in utils.nlp so the
module works in constrained environments without heavy ML dependencies.

Inputs
------
question : str       – the interview question that was asked
answer   : str       – the candidate's transcript
keywords : list[str] – expected keywords / concepts for a strong answer

Returns
-------
dict with:
  "score"    – int 0-100
  "insights" – human-readable summary string
"""

from utils.nlp import cosine_similarity


def calculate_relevance(
    question: str,
    answer: str,
    keywords: list,
) -> dict:
    """Return a relevance score (0-100) and insight string."""

    if not answer.strip():
        return {"score": 0, "insights": "No answer provided"}

    # --- Semantic similarity between question and answer (0-1) ---------------
    # Scaled to 0-100 and weighted at 50 % of the final score.
    similarity = cosine_similarity(question, answer)
    semantic_score = min(100.0, similarity * 100)

    # --- Keyword coverage (0-100) --------------------------------------------
    # Count how many expected keywords appear in the answer (case-insensitive).
    if keywords:
        answer_lower = answer.lower()
        matched = sum(1 for kw in keywords if kw.lower() in answer_lower)
        keyword_score = (matched / len(keywords)) * 100
    else:
        # No keywords provided – rely entirely on semantic similarity.
        keyword_score = semantic_score

    # --- Answer length adequacy (0-100) --------------------------------------
    # A very short answer (< 20 words) is penalised; long answers are fine.
    word_count = len(answer.split())
    if word_count >= 40:
        length_score = 100.0
    elif word_count >= 20:
        length_score = 60.0 + (word_count - 20) * 2.0   # 60-100 range
    else:
        length_score = max(0.0, word_count * 3.0)         # 0-60 range

    # --- Weighted composite --------------------------------------------------
    score = (
        semantic_score * 0.50 +
        keyword_score  * 0.35 +
        length_score   * 0.15
    )

    # --- Insights ------------------------------------------------------------
    insights = []
    if keywords:
        answer_lower = answer.lower()
        missing = [kw for kw in keywords if kw.lower() not in answer_lower]
        if missing:
            insights.append(f"Missing key concepts: {', '.join(missing)}")
    if semantic_score < 40:
        insights.append("Answer does not closely address the question asked")
    if word_count < 20:
        insights.append("Provide a more detailed answer")

    return {
        "score": max(0, min(100, round(score))),
        "insights": "; ".join(insights) if insights else "Answer is relevant and on-topic",
    }
