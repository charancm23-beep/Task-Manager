import json
from models import ScorecardInput, VideoAnalysis, SpeechAnalysis, QuestionContext
from main import evaluate_interview

sample = ScorecardInput(
    video=VideoAnalysis(eye_contact_ratio=0.7, facial_expression_score=80, posture_score=85),
    speech=SpeechAnalysis(
        transcript=("During a major outage, I led a team of 5 engineers to restore service in under 2 hours "
                    "by prioritizing critical systems and coordinating with ops."),
        filler_words_count=1,
        speech_rate_wpm=140.0,
        total_duration_sec=30.0,
        voice_energy_score=80
    ),
    context=QuestionContext(
        question_text="Tell me about a time you led a team through a crisis.",
        expected_keywords=["led", "team", "crisis", "restore"],
        role="Software Engineer",
        company="ACME"
    )
)

result = evaluate_interview(sample)
print(json.dumps(result.model_dump(), indent=2))
