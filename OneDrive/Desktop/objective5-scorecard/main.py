# main.py
from fastapi import FastAPI
from datetime import datetime
import uuid
import logging
import logging.handlers
import os
import json
import contextvars
from fastapi import Request
from starlette.responses import JSONResponse

from models import ScorecardInput, ScorecardOutput
from engine.confidence import calculate_confidence
from engine.clarity import calculate_clarity
from engine.relevance import calculate_relevance
from engine.suggestions import generate_suggestions
from report.generator import generate_pdf

app = FastAPI(title="AI Interview Scorecard Engine")
# Basic logger and request-id contextvar used by middleware and handlers
REQUEST_ID = contextvars.ContextVar("request_id", default=None)
logger = logging.getLogger("scorecard")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Assign a UUID request id and store it in a contextvar for logging.

    The request id is also added to the response header `X-Request-ID`.
    """
    req_id = str(uuid.uuid4())
    # set contextvar token so it's available to log formatter
    token = REQUEST_ID.set(req_id)
    try:
        response = await call_next(request)
    finally:
        # Reset contextvar to previous value
        try:
            REQUEST_ID.reset(token)
        except Exception:
            pass

    # Expose request id to clients via header
    response.headers["X-Request-ID"] = req_id

    # If the response is JSON, try to inject the request_id into the body
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type.lower():
        try:
            # Attempt to read the response body (works for regular responses)
            body_bytes = None
            try:
                body_bytes = await response.body()
            except Exception:
                # Some Response objects expose .body directly
                body_bytes = getattr(response, "body", None)

            if body_bytes:
                # Ensure we have raw bytes
                if isinstance(body_bytes, str):
                    body_bytes = body_bytes.encode()
                data = json.loads(body_bytes.decode())
                if isinstance(data, dict):
                    data["request_id"] = req_id
                    # Build a new JSONResponse preserving status and headers
                    headers = dict(response.headers)
                    # Remove content-length because body changed
                    headers.pop("content-length", None)
                    return JSONResponse(content=data, status_code=response.status_code, headers=headers)
        except Exception as e:
            logger.debug("Could not inject request_id into response body: %s", e)

    return response

@app.post("/evaluate", response_model=ScorecardOutput)
def evaluate_interview(data: ScorecardInput):
    # Unpack
    v = data.video
    s = data.speech
    c = data.context
    logger.info("Handling /evaluate request")

    filler_ratio = s.filler_words_count / max(1, len(s.transcript.split()))

    # Calculate metrics
    confidence = calculate_confidence(
        filler_ratio=filler_ratio,
        speech_rate=s.speech_rate_wpm,
        eye_contact=v.eye_contact_ratio,
        voice_energy=s.voice_energy_score,
        posture=v.posture_score
    )

    clarity = calculate_clarity(
        transcript=s.transcript,
        filler_count=s.filler_words_count,
        speech_rate=s.speech_rate_wpm,
        duration=s.total_duration_sec
    )

    relevance = calculate_relevance(
        question=c.question_text,
        answer=s.transcript,
        keywords=c.expected_keywords
    )

    metrics = {
        "confidence": confidence,
        "clarity": clarity,
        "relevance": relevance
    }

    overall = (
        confidence["score"] * 0.3 +
        clarity["score"] * 0.3 +
        relevance["score"] * 0.4
    )

    suggestions = generate_suggestions(metrics, s.transcript, c.question_text, c.expected_keywords)

    scorecard = ScorecardOutput(
        overall_score=round(overall, 1),
        metrics={k: {"score": v["score"], "insights": v["insights"]} for k, v in metrics.items()},
        improvement_suggestions=suggestions,
        timestamp=datetime.utcnow().isoformat(),
        request_id=REQUEST_ID.get()
    )

    # Optional: Generate PDF
    # generate_pdf(scorecard.dict(), f"reports/{uuid.uuid4()}.pdf")

    return scorecard