from faster_whisper import WhisperModel
import re
from typing import Dict, Any
from app.services.feedback_generator import FeedbackGenerator

class SpeakingService:
    def __init__(self):
        print("🔄 Whisper 'small' model yükleniyor...")
        self.model = WhisperModel("small", device="cpu", compute_type="int8")
        self.feedback_generator = FeedbackGenerator()
        print("✅ Whisper model başarıyla yüklendi")

    def analyze_audio(self, audio_path: str, exam: str = "TOEFL", task_prompt: str = "") -> Dict[str, Any]:
        try:
            print(f"🎤 Ses dosyası analiz ediliyor: {audio_path}")

            segments, info = self.model.transcribe(
                audio_path,
                beam_size=5,
                word_timestamps=True,
                language="en" if exam == "TOEFL" else "de"
            )

            full_text = " ".join([segment.text for segment in segments]).strip()

            # Metrikler
            words = re.findall(r'\b\w+\b', full_text.lower())
            filler_count = len(re.findall(r'\b(um|uh|like|you know|so|well|yeah|okay)\b', full_text.lower()))
            duration_sec = info.duration if info.duration else 0
            speech_rate = len(words) / (duration_sec / 60) if duration_sec > 0 else 0

            enriched_input = f"""
Speaking Task: {task_prompt}
Transcript: {full_text}
Duration: {duration_sec:.1f} seconds
Speech Rate: {speech_rate:.1f} words per minute
Filler Words: {filler_count}
"""

            feedback_text = self.feedback_generator.generate_speaking_feedback(enriched_input, exam)

            return {
                "status": "success",
                "transcript": full_text,
                "duration_seconds": round(duration_sec, 2),
                "speech_rate_wpm": round(speech_rate, 1),
                "filler_count": filler_count,
                "feedback": feedback_text
            }

        except Exception as e:
            print(f"❌ Speaking hatası: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }