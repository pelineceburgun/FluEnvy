import os
from langchain_ollama import OllamaLLM
from app.services.rag_service import RAGService

_OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")


class FeedbackGenerator:
    def __init__(self):
        self.rag = RAGService()
        self.llm = OllamaLLM(
            model="llama3.2:3b",
            base_url=_OLLAMA_URL,
            temperature=0.5,
            num_ctx=8192,
        )

    async def generate_writing_feedback(self, student_text: str, task_prompt: str, exam: str = "TOEFL"):
        similar_examples = self.rag.retrieve_similar_examples(
            query=f"{task_prompt}\n{student_text}",
            exam=exam,
            k=5,
        )

        examples_text = "\n\n".join([
            f"--- Example {i+1} ({ex['metadata'].get('quality', 'unknown')}) ---\n{ex['content']}"
            for i, ex in enumerate(similar_examples)
        ])

        if exam == "TELC":
            rubric_rules = """\
- Score Aufgabenbewältigung, Kommunikative Gestaltung, Formale Richtigkeit out of 5 each (total out of 15).
- Aufgabenbewältigung: Did the student address ALL Leitpunkte (guided points)?
- Kommunikative Gestaltung: Is the register (formal/informal) appropriate? Are connectors used naturally?
- Formale Richtigkeit: Grammar, spelling, punctuation, and sentence structure accuracy.

**Rubric Scores** (use EXACTLY this table format):
| Criterion | Score | Max |
|---|---|---|
| Aufgabenbewältigung | [score] | 5 |
| Kommunikative Gestaltung | [score] | 5 |
| Formale Richtigkeit | [score] | 5 |
| **Overall Score** | [total] | **15** |"""
            lang_note = "Provide all feedback in English. Quote specific German sentences from the student text when explaining errors."
        else:
            rubric_rules = """\
- Score Task Response, Organization, Language Use out of 5 each (total out of 30).

**Rubric Scores** (use EXACTLY this table format):
| Criterion | Score | Max |
|---|---|---|
| Task Response | [score] | 5 |
| Organization | [score] | 5 |
| Language Use | [score] | 5 |
| **Overall Score** | [total] | **30** |"""
            lang_note = "Provide all feedback in English."

        system_prompt = f"""
You are a professional, experienced, and encouraging writing coach for {exam} exams.

Use the following Golden Dataset examples as reference:

{examples_text}

Task Prompt:
{task_prompt}

Student's Essay:
{student_text}

**Strict Rules:**
{rubric_rules}
{lang_note}
- Be specific, constructive, and motivating.

**Feedback Structure (follow exactly):**

1. **Overall Evaluation**
   Start with a positive, encouraging sentence. Give a clear overall score and brief summary.

2. **Rubric Scores**
   Use the exact table format defined above.

3. **Strengths**
   List 2-3 specific strengths with short explanations.

4. **Error Analysis**
   For each major error:
   - Category
   - Location (quote the sentence)
   - Correction
   - Explanation (why it affects the score)
   - Suggestion
   - Improved Example

5. **Revised Model Text**
   Provide a complete, higher-scoring version of the essay.

6. **Improvement Plan**
   Give 3 concrete, actionable recommendations for this week.

7. **Motivational Closing**
   End with warm, sincere encouragement.

Focus on clarity, specificity, and motivation.
"""

        try:
            response = self.llm.invoke(system_prompt)
            return {
                "status": "success",
                "exam": exam,
                "feedback": response.strip(),
                "used_examples": len(similar_examples),
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def generate_speaking_feedback(self, enriched_input: str, exam: str = "TOEFL"):
        if exam == "TELC":
            criteria = """\
- **Aufgabenbewältigung (Fluency & Coherence)**: Did the speaker fulfill the task? Is the speech fluent and well-organised?
- **Aussprache & Intonation (Pronunciation & Clarity)**: How clear and natural is the German pronunciation?
- **Kommunikativer Inhalt (Task Response & Content)**: Are the ideas relevant, developed, and clearly expressed?
- **Sprachliche Richtigkeit (Language Use)**: Accuracy of German grammar, vocabulary range and appropriateness."""
            lang_note = "Evaluate this German speaking performance. Provide all feedback in English."
        else:
            criteria = """\
- **Fluency & Coherence**: Speech rate, filler words, pauses, natural flow
- **Pronunciation & Clarity**: How clear and understandable the speech is
- **Task Response & Content**: How well the speaker answered the question with relevant ideas and examples
- **Language Use**: Vocabulary range, grammar accuracy, sentence variety"""
            lang_note = "Provide all feedback in English."

        system_prompt = f"""
You are an expert, encouraging, and highly detailed speaking coach for {exam} exams.

{lang_note}

Analyze the following speaking performance carefully:

{enriched_input}

**Evaluation Criteria (be specific):**
{criteria}

**Required Feedback Structure (follow exactly):**

**Overall Evaluation**
- Start with a positive and encouraging sentence.
- Give an overall score out of 30.
- One short summary sentence.

**Rubric Scores**
Show in a clean markdown table:
| Criterion | Score | Max |
|---|---|---|
| Fluency & Coherence | [score] | 10 |
| Pronunciation & Clarity | [score] | 8 |
| Task Response & Content | [score] | 7 |
| Language Use | [score] | 5 |
| **Overall Score** | [total] | **30** |

**Strengths**
List 2-3 specific strengths with examples from the transcript.

**Areas for Improvement**
List 2-3 concrete areas with specific quotes from the transcript and clear explanations.

**Practical Tips**
Give 3 actionable, practical tips the student can apply immediately.

**Motivational Closing**
End with warm, sincere encouragement and motivation.

Be specific, supportive, and helpful.
"""

        try:
            response = self.llm.invoke(system_prompt)
            return response.strip()
        except Exception as e:
            return f"Error generating speaking feedback: {str(e)}"
