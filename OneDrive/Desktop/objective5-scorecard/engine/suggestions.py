# engine/suggestions.py
"""
Generate actionable improvement suggestions based on the evaluated metrics,
the candidate's transcript, the interview question, and expected keywords.

Inputs
------
metrics    : dict  – {"confidence": {"score": …, "insights": …},
                       "clarity":    {"score": …, "insights": …},
                       "relevance":  {"score": …, "insights": …}}
transcript : str   – candidate's spoken answer
question   : str   – the interview question
keywords   : list  – expected keywords / concepts

Returns
-------
list[str] – ordered list of actionable suggestion strings (may be empty if
            the candidate performed well across all dimensions)
"""


# Thresholds below which a dimension is considered "needs improvement"
_SCORE_THRESHOLD = 70


def generate_suggestions(
    metrics: dict,
    transcript: str,
    question: str,
    keywords: list,
) -> list:
    """Return a list of improvement suggestion strings."""

    suggestions = []

    confidence = metrics.get("confidence", {})
    clarity    = metrics.get("clarity",    {})
    relevance  = metrics.get("relevance",  {})

    conf_score = confidence.get("score", 100)
    clar_score = clarity.get("score",    100)
    rel_score  = relevance.get("score",  100)

    # --- Confidence suggestions ----------------------------------------------
    if conf_score < _SCORE_THRESHOLD:
        suggestions.append(
            "Work on projecting confidence: maintain steady eye contact, "
            "keep an upright posture, and speak with consistent vocal energy."
        )
    if conf_score < 50:
        suggestions.append(
            "Practice your answer out loud several times before the interview "
            "to reduce hesitation and filler words."
        )

    # --- Clarity suggestions -------------------------------------------------
    if clar_score < _SCORE_THRESHOLD:
        suggestions.append(
            "Improve speech clarity by pacing yourself between 120-160 wpm "
            "and minimising filler words such as 'um', 'uh', and 'like'."
        )
    if clar_score < 50:
        suggestions.append(
            "Structure your answer using the STAR method (Situation, Task, "
            "Action, Result) to make your response easier to follow."
        )

    # --- Relevance suggestions -----------------------------------------------
    if rel_score < _SCORE_THRESHOLD:
        # Surface any missing keywords from the relevance insights string
        rel_insights = relevance.get("insights", "")
        if "Missing key concepts" in rel_insights:
            suggestions.append(
                f"Strengthen your answer by addressing: {rel_insights.split('Missing key concepts: ')[-1].split(';')[0]}."
            )
        else:
            suggestions.append(
                "Tailor your answer more directly to the question asked and "
                "ensure you cover the core concepts expected."
            )
    if rel_score < 50:
        suggestions.append(
            "Re-read the question carefully and make sure every part of your "
            "answer connects back to what was specifically asked."
        )

    # --- Keyword coverage check (independent of score) -----------------------
    if keywords:
        answer_lower = transcript.lower()
        missing_kw = [kw for kw in keywords if kw.lower() not in answer_lower]
        if missing_kw and rel_score >= _SCORE_THRESHOLD:
            # Score was acceptable but some keywords were still absent
            suggestions.append(
                f"Consider weaving in these concepts for a stronger answer: "
                f"{', '.join(missing_kw)}."
            )

    # --- Answer length check -------------------------------------------------
    word_count = len(transcript.split())
    if word_count < 30:
        suggestions.append(
            "Expand your answer with specific examples or details – aim for "
            "at least 60-90 words to fully demonstrate your experience."
        )
    elif word_count > 300:
        suggestions.append(
            "Keep your answer concise; interviewers typically prefer focused "
            "responses under 2 minutes."
        )

    # --- Overall positive feedback when everything is strong -----------------
    if not suggestions:
        suggestions.append(
            "Great performance overall – continue practising to maintain "
            "this level of confidence, clarity, and relevance."
        )

    return suggestions
