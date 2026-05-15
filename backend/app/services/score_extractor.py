import re
from typing import Optional, Dict


def extract_overall_score(feedback_text: str, exam: str = "TOEFL") -> Optional[float]:
    if exam == "TELC":
        patterns = [
            r'overall\s+score[:\s*|]+(\d+(?:\.\d+)?)\s*/\s*15',
            r'\*{0,2}overall\s+score\*{0,2}[:\s|]+(\d+(?:\.\d+)?)\s*/\s*15',
            r'(\d+(?:\.\d+)?)\s*/\s*15',
        ]
        max_val = 15.0
    else:
        patterns = [
            r'overall\s+score[:\s*]+(\d+(?:\.\d+)?)\s*/\s*30',
            r'\*{1,2}overall\s+score[:\s*]+(\d+(?:\.\d+)?)\s*/\s*30\*{0,2}',
            r'(\d+(?:\.\d+)?)\s*/\s*30',
        ]
        max_val = 30.0

    for pattern in patterns:
        match = re.search(pattern, feedback_text, re.IGNORECASE)
        if match:
            score = float(match.group(1))
            if 0 <= score <= max_val:
                return score
    return None


def extract_rubric_scores(feedback_text: str, task_type: str, exam: str = "TOEFL") -> Dict[str, Optional[float]]:
    if task_type == "speaking":
        # Same rubric columns for both TOEFL and TELC speaking
        patterns = {
            "fluency_score":           (r'fluency[^|/\n]*?\|?\s*(\d+(?:\.\d+)?)\s*/\s*10', 10),
            "pronunciation_score":     (r'pronunciation[^|/\n]*?\|?\s*(\d+(?:\.\d+)?)\s*/\s*8',  8),
            "content_score":           (r'task\s+response[^|/\n]*?\|?\s*(\d+(?:\.\d+)?)\s*/\s*7', 7),
            "speaking_language_score": (r'language\s+use[^|/\n]*?\|?\s*(\d+(?:\.\d+)?)\s*/\s*5',  5),
        }
    elif exam == "TELC":
        patterns = {
            "aufgabenbewaltigung_score": (
                r'aufgabenbew[äa]ltigung[^|/\n]*?\|?\s*(\d+(?:\.\d+)?)\s*/?\s*5', 5),
            "kommunikative_gestaltung_score": (
                r'kommunikative\s+gestaltung[^|/\n]*?\|?\s*(\d+(?:\.\d+)?)\s*/?\s*5', 5),
            "formale_richtigkeit_score": (
                r'formale\s+richtigkeit[^|/\n]*?\|?\s*(\d+(?:\.\d+)?)\s*/?\s*5', 5),
        }
    else:  # TOEFL writing
        patterns = {
            "task_response_score": (r'task\s+response[^|/\n]*?\|?\s*(\d+(?:\.\d+)?)\s*/\s*5', 5),
            "organization_score":  (r'organization[^|/\n]*?\|?\s*(\d+(?:\.\d+)?)\s*/\s*5',    5),
            "language_use_score":  (r'language\s+use[^|/\n]*?\|?\s*(\d+(?:\.\d+)?)\s*/\s*5',  5),
        }

    scores: Dict[str, Optional[float]] = {}
    for key, (pattern, max_score) in patterns.items():
        match = re.search(pattern, feedback_text, re.IGNORECASE)
        if match:
            val = float(match.group(1))
            scores[key] = val if 0 <= val <= max_score else None
        else:
            scores[key] = None
    return scores
