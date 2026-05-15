from sqlalchemy.orm import Session
from app.models.attempt import Attempt
from typing import List, Dict, Any, Optional

SKILL_ADVICE: Dict[str, str] = {
    # TOEFL skills
    "main_idea":            "You should focus on identifying the main idea in reading passages.",
    "supporting_detail":    "Practice finding supporting details that back up main arguments.",
    "inference":            "Work on making logical inferences from context and indirect clues.",
    "vocabulary":           "Build your academic vocabulary — focus on words used in context.",
    "cohesion":             "Practice connecting ideas with appropriate transition words and phrases.",
    "grammar":              "Review key grammar rules, especially tense consistency and sentence structure.",
    "argument_structure":   "Work on organizing arguments with a clear thesis and strong supporting evidence.",
    "fluency":              "Practice speaking continuously for 45 seconds without pausing or stopping.",
    "pronunciation":        "Focus on clear articulation, especially consonant clusters and word stress.",
    "integrated_writing":   "Practice summarizing lecture points and contrasting them with reading passages.",
    "independent_writing":  "Work on developing a clear position and supporting it with specific examples.",
    "integrated_speaking":  "Practice paraphrasing information from reading and listening sources.",
    "independent_speaking": "State your opinion clearly and support it with two well-developed reasons.",
    "paraphrasing":         "Practice restating ideas in your own words without changing the meaning.",
    "summarizing":          "Work on condensing long texts into concise summaries of key points.",
    "details":              "Pay attention to specific details and examples mentioned in passages.",
    # TELC-specific skills
    "leitpunkte":           "Practice addressing all Leitpunkte (guided points) clearly and completely — missing even one lowers your Aufgabenbewältigung score.",
    "register":             "Focus on matching register to the task: informal (du, Grüße) for emails to friends; formal (Sie, Mit freundlichen Grüßen) for official letters.",
    "koharenz":             "Work on using connectors (aber, weil, obwohl, deshalb, außerdem) to link your ideas smoothly.",
    "grammatik":            "Review German grammar — especially case endings (Akkusativ/Dativ), verb conjugation, and word order after conjunctions.",
    "wortschatz":           "Expand your German B1 vocabulary with phrases for common writing topics like travel, work, and everyday life.",
    "rechtschreibung":      "Practice German spelling — pay special attention to compound nouns, ß vs ss, and mandatory capitalization of all nouns.",
    "beschwerde":           "Practice writing formal complaint letters: state the problem clearly, give evidence, and make a specific demand.",
    "email":                "Focus on informal email writing — use a friendly tone, short sentences, and appropriate greetings like 'Liebe/Lieber'.",
    "aussprache":           "Work on German vowel sounds (ü, ö, ä) and consonant clusters that differ from your native language.",
}


def save_attempt(db: Session, data: Dict[str, Any]) -> Attempt:
    attempt = Attempt(**data)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def get_student_progress(db: Session, student_id: str) -> Dict:
    attempts = (
        db.query(Attempt)
        .filter(Attempt.student_id == student_id)
        .order_by(Attempt.created_at)
        .all()
    )
    return {
        "student_id": student_id,
        "total_attempts": len(attempts),
        "attempts": [_serialize(a) for a in attempts],
    }


def detect_weak_points(
    db: Session,
    student_id: str,
    task_type: Optional[str] = None,
    exam: Optional[str] = None,
) -> Dict:
    q = db.query(Attempt).filter(Attempt.student_id == student_id)
    if task_type:
        q = q.filter(Attempt.task_type == task_type)
    if exam:
        q = q.filter(Attempt.exam == exam)
    attempts = q.all()

    if not attempts:
        return {"weak_points": [], "skill_warnings": [], "message": "No attempts found"}

    detected_exam = exam or _detect_exam(attempts)

    if task_type == "speaking":
        categories = {
            "Fluency & Coherence":     ([a.fluency_score for a in attempts], 10),
            "Pronunciation & Clarity": ([a.pronunciation_score for a in attempts], 8),
            "Task Response & Content": ([a.content_score for a in attempts], 7),
            "Language Use":            ([a.speaking_language_score for a in attempts], 5),
        }
    elif detected_exam == "TELC":
        categories = {
            "Aufgabenbewältigung":    ([a.aufgabenbewaltigung_score for a in attempts], 5),
            "Kommunikative Gestaltung": ([a.kommunikative_gestaltung_score for a in attempts], 5),
            "Formale Richtigkeit":    ([a.formale_richtigkeit_score for a in attempts], 5),
        }
    else:  # TOEFL writing
        categories = {
            "Task Response": ([a.task_response_score for a in attempts], 5),
            "Organization":  ([a.organization_score for a in attempts], 5),
            "Language Use":  ([a.language_use_score for a in attempts], 5),
        }

    weak_points = []
    for category, (raw_scores, max_score) in categories.items():
        scores = [s for s in raw_scores if s is not None]
        if not scores:
            continue
        avg = sum(scores) / len(scores)
        pct = (avg / max_score) * 100
        if pct < 70:
            weak_points.append({
                "category": category,
                "average_score": round(avg, 1),
                "max_score": max_score,
                "percentage": round(pct, 1),
                "status": "critical" if pct < 50 else "needs_improvement",
            })

    weak_points.sort(key=lambda x: x["percentage"])
    skill_warnings = _detect_skill_patterns(attempts)

    return {
        "weak_points": weak_points,
        "skill_warnings": skill_warnings,
        "total_attempts_analyzed": len(attempts),
        "exam": detected_exam,
    }


def _detect_skill_patterns(attempts: List[Attempt]) -> List[Dict]:
    skill_groups: Dict[str, List[float]] = {}
    for a in attempts:
        tag = getattr(a, "skill_tag", None)
        if not tag or a.overall_score is None:
            continue
        key = tag.lower().strip()
        skill_groups.setdefault(key, []).append(a.overall_score)

    warnings = []
    for tag, scores in skill_groups.items():
        if len(scores) < 2:
            continue
        avg = sum(scores) / len(scores)
        # Normalize: TELC overall is /15, TOEFL is /30 — use 50% threshold of whichever
        # We don't know the scale here, so compare against 50% of the max observed score
        # as a proxy (simple heuristic: flag if avg < 50% of 30 for TOEFL or 15 for TELC)
        # Since we can't know exam here, use raw percentage vs 30 (TOEFL default)
        avg_pct = (avg / 30) * 100
        if avg_pct < 50:
            advice = SKILL_ADVICE.get(
                tag, f"Focus on improving your {tag.replace('_', ' ')} skills."
            )
            warnings.append({
                "skill_tag": tag,
                "display_name": tag.replace("_", " ").title(),
                "average_score": round(avg, 1),
                "attempts": len(scores),
                "percentage": round(avg_pct, 1),
                "advice": advice,
            })

    warnings.sort(key=lambda x: x["percentage"])
    return warnings


def predict_score(
    db: Session,
    student_id: str,
    task_type: Optional[str] = None,
    exam: Optional[str] = None,
) -> Dict:
    q = (
        db.query(Attempt)
        .filter(Attempt.student_id == student_id, Attempt.overall_score.isnot(None))
    )
    if task_type:
        q = q.filter(Attempt.task_type == task_type)
    if exam:
        q = q.filter(Attempt.exam == exam)
    attempts = q.order_by(Attempt.created_at).all()

    if not attempts:
        return {
            "predicted_score": None,
            "trend": "no_data",
            "message": "No scored attempts found",
            "prediction_message": None,
        }

    detected_exam = exam or _detect_exam(attempts)
    # TELC writing is /15; everything else (speaking, TOEFL writing) is /30
    max_score = 15.0 if (detected_exam == "TELC" and task_type == "writing") else 30.0

    scores = [a.overall_score for a in attempts]

    if len(scores) < 2:
        return {
            "predicted_score": scores[-1],
            "trend": "insufficient_data",
            "message": "Need at least 2 attempts for a trend",
            "historical_scores": scores,
            "prediction_message": "Keep practicing to unlock score predictions!",
            "max_score": max_score,
        }

    slope, intercept = _linear_regression(list(range(len(scores))), scores)
    next_x = len(scores)
    predicted = max(0.0, min(max_score, round(slope * next_x + intercept, 1)))
    trend = "improving" if slope > 0.3 else "declining" if slope < -0.3 else "stable"

    # Estimate pace → project 4-week forecast
    first_ts = attempts[0].created_at
    last_ts  = attempts[-1].created_at
    if first_ts and last_ts:
        days_span = max((last_ts - first_ts).days, 1)
    else:
        days_span = 7
    attempts_per_week = (len(attempts) / (days_span / 7)) if days_span >= 3 else 3.0
    attempts_in_4w = attempts_per_week * 4
    projected_4w = max(0.0, min(max_score, round(
        slope * (next_x + attempts_in_4w - 1) + intercept, 1
    )))

    exam_label  = detected_exam
    task_label  = (task_type or "").replace("_", " ") or "section"
    current     = scores[-1]

    if trend == "improving":
        prediction_message = (
            f"If you keep up this pace, your {exam_label} {task_label} score "
            f"could reach {projected_4w}/{int(max_score)} in about a month."
        )
    elif trend == "declining":
        prediction_message = (
            f"Your {exam_label} {task_label} score has been declining lately. "
            "Consistent daily practice could help reverse this trend."
        )
    else:
        prediction_message = (
            f"Your {exam_label} {task_label} score is holding steady around "
            f"{current}/{int(max_score)}. Increasing your weekly practice "
            "frequency is the fastest way to improve."
        )

    return {
        "predicted_score": predicted,
        "trend": trend,
        "slope_per_attempt": round(slope, 2),
        "historical_scores": scores,
        "attempts_count": len(scores),
        "max_score": max_score,
        "prediction_message": prediction_message,
    }


# ── helpers ──────────────────────────────────────────────────────────────────

def _detect_exam(attempts: List[Attempt]) -> str:
    counts: Dict[str, int] = {}
    for a in attempts:
        counts[a.exam] = counts.get(a.exam, 0) + 1
    return max(counts, key=counts.get) if counts else "TOEFL"


def _linear_regression(x: List[float], y: List[float]):
    n = len(x)
    sum_x  = sum(x)
    sum_y  = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi ** 2 for xi in x)
    denom  = n * sum_x2 - sum_x ** 2
    if denom == 0:
        return 0.0, sum_y / n
    slope     = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    return slope, intercept


def _serialize(a: Attempt) -> Dict:
    return {
        "id":                          a.id,
        "exam":                        a.exam,
        "task_type":                   a.task_type,
        "task_prompt":                 a.task_prompt,
        "skill_tag":                   getattr(a, "skill_tag", None),
        "overall_score":               a.overall_score,
        # TOEFL writing
        "task_response_score":         a.task_response_score,
        "organization_score":          a.organization_score,
        "language_use_score":          a.language_use_score,
        # Speaking (both exams)
        "fluency_score":               a.fluency_score,
        "pronunciation_score":         a.pronunciation_score,
        "content_score":               a.content_score,
        "speaking_language_score":     a.speaking_language_score,
        # TELC writing
        "aufgabenbewaltigung_score":      getattr(a, "aufgabenbewaltigung_score", None),
        "kommunikative_gestaltung_score": getattr(a, "kommunikative_gestaltung_score", None),
        "formale_richtigkeit_score":      getattr(a, "formale_richtigkeit_score", None),
        # Speaking metadata
        "duration_seconds":            a.duration_seconds,
        "speech_rate_wpm":             a.speech_rate_wpm,
        "filler_count":                a.filler_count,
        "transcript":                  a.transcript,
        "created_at":                  a.created_at.isoformat() if a.created_at else None,
    }
