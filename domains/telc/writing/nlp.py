from app.services.feedback_generator import generate_feedback

async def analyze_telc_writing(student_text: str, task_prompt: str, level: str = "B1"):
    # TELC'e özel: Leitpunkte kontrolü, register kontrolü (resmi/günlük)
    system_prompt = f"TELC B1 Schreiben uzmanısın. Leitpunkte tamamlama, Kohärenz ve Formale Richtigkeit'e odaklan..."
    
    feedback = await generate_feedback(
        student_text=student_text,
        task_prompt=task_prompt,
        exam="TELC",
        rubric="B1 Schreiben"
    )
    return feedback