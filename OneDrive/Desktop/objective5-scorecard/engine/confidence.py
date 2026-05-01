# engine/confidence.py
"""
Confidence scoring based on non-verbal and vocal delivery signals.

Inputs
------
filler_ratio   : float  – filler words / total words (0–1)
speech_rate    : float  – words per minute
eye_contact    : float  – fraction of time eye contact was maintained (0–1)
voice_energy   : float  – voice energy / volume consistency score (0–100)
posture        : float  – posture quality score (0–100)

Returns
-------
dict with:
  "score"    – int 0-100
  "insights" – human-readable summary string
"""


def calculate_confidence(
    filler_ratio: float,
    speech_rate: float,
    eye_contact: float,
    voice_energy: float,
    posture: float,
) -> dict:
    """Return a confidence score (0-100) and insight string."""

    # --- Eye contact (0-100) ------------------------------------------------
    # Full marks at >= 0.65; linearly penalised below that threshold.
    eye_score = min(100.0, eye_contact * 100 / 0.65) if eye_contact < 0.65 else 100.0

    # --- Voice energy (already 0-100) ----------------------------------------
    voice_score = float(voice_energy)

    # --- Posture (already 0-100) ---------------------------------------------
    posture_score = float(posture)

    # --- Speech rate (0-100) -------------------------------------------------
    # Ideal confident pace: 130-160 wpm.  Penalise deviations.
    if 130 <= speech_rate <= 160:
        rate_score = 100.0
    else:
        rate_score = max(0.0, 100.0 - abs(speech_rate - 145) * 1.2)

    # --- Filler penalty (0-40 points deducted) --------------------------------
    # Each percentage point of filler ratio costs ~4 points, capped at 40.
    filler_penalty = min(40.0, filler_ratio * 400)

    # --- Weighted composite --------------------------------------------------
    base = (
        eye_score    * 0.30 +
        voice_score  * 0.25 +
        posture_score * 0.25 +
        rate_score   * 0.20
    )
    score = max(0.0, base - filler_penalty)

    # --- Insights ------------------------------------------------------------
    insights = []
    if eye_contact < 0.40:
        insights.append("Maintain more consistent eye contact")
    if voice_energy < 50:
        insights.append("Project your voice with more energy")
    if posture < 50:
        insights.append("Improve posture to appear more confident")
    if filler_ratio > 0.05:
        insights.append("Reduce filler words (um, uh, like)")
    if speech_rate < 110:
        insights.append("Speak at a slightly faster pace to sound more assured")
    elif speech_rate > 180:
        insights.append("Slow down to convey calm confidence")

    return {
        "score": max(0, min(100, round(score))),
        "insights": "; ".join(insights) if insights else "Strong confident delivery",
    }
