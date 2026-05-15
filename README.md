# FluEnvy

An AI-powered exam preparation platform for TOEFL and TELC B1, featuring automated writing and speaking feedback, progress analytics, and personalized weak-point detection.

---

## Features

### Exam Support

| Exam | Skills Covered | Language |
|------|---------------|----------|
| TOEFL | Writing (Independent & Integrated), Speaking (Independent & Integrated), Reading | English |
| TELC B1 | Writing (Informelle E-Mail, Beschwerdebrief), Speaking (Monolog & Dialog) | German |

---

### Writing Feedback

- Accepts essay submissions alongside the task prompt and exam type
- Retrieves the 5 most semantically similar high-scoring examples from a golden dataset via **RAG (Retrieval-Augmented Generation)** using ChromaDB + `intfloat/e5-base-v2` embeddings
- An Ollama-hosted local LLM (`llama3.2:3b`) generates structured feedback covering:
  - Rubric-based scores (exam-specific criteria, see below)
  - Identified strengths with direct text evidence
  - Error analysis with category, location, correction, and explanation
  - A fully revised model version of the student's essay
  - A 3-step weekly improvement plan

**TOEFL Writing Rubric** (scored /5 each → /30 total):

| Criterion | Description |
|-----------|-------------|
| Task Response | Addresses the prompt fully and develops ideas |
| Organization | Logical structure, clear paragraphing, transitions |
| Language Use | Grammar, vocabulary range, sentence variety |

**TELC B1 Writing Rubric** (scored /5 each → /15 total):

| Criterion | Description |
|-----------|-------------|
| Aufgabenbewältigung | Task completion and leitpunkte coverage |
| Kommunikative Gestaltung | Register, coherence, communicative effectiveness |
| Formale Richtigkeit | Grammar, spelling, and formal accuracy |

---

### Speaking Feedback

- Accepts audio file uploads (`.wav`, `.mp3`, etc.)
- Transcribes speech using **Faster-Whisper** (`small` model, CPU-optimized, `int8` quantization) with language auto-detection
- Extracts objective speech metrics from the transcript:
  - Total duration (seconds)
  - Speech rate (words per minute)
  - Filler word count (`um`, `uh`, `like`, `you know`, etc.)
- LLM generates rubric-scored feedback using both the transcript and the speech metrics

**Speaking Rubric** (same for both exams, /30 total):

| Criterion | Max Score |
|-----------|-----------|
| Fluency & Coherence | /10 |
| Pronunciation & Clarity | /8 |
| Task Response & Content | /7 |
| Language Use | /5 |

---

### Reading Assessment

- Accepts a correct-answer count and total question count
- Scales the result to a /30 score
- Stores the attempt for inclusion in progress analytics

---

### Progress Analytics

All attempts (writing, speaking, reading) are persisted in SQLite and exposed through three analytics endpoints:

**Full History** — returns all stored attempts with scores, skill tags, and metadata for a given student.

**Weak-Point Detection** — analyzes rubric component averages across attempts and flags categories below 70% achievement:
- Below 50% → `critical`
- 50–70% → `needs_improvement`

Includes personalized improvement advice drawn from a curated taxonomy of 34 skill tags spanning TOEFL and TELC areas (task response, cohesion, pronunciation, German case endings, register, etc.).

**Score Prediction** — fits a linear regression over historical attempt scores to produce:
- Detected trend: `improving`, `declining`, or `stable`
- Estimated slope (score points gained per attempt)
- 4-week projected score ceiling
- Personalized motivational message

---

### RAG Knowledge Base

- Stored in ChromaDB (`golden_dataset` collection)
- Each entry contains a task prompt, student text with score level, detailed error annotations, and strengths/weaknesses breakdown
- Covers: TOEFL Independent Writing, TOEFL Integrated Writing, TELC B1 Informelle E-Mail, TELC B1 Beschwerdebrief, and Speaking examples
- Filtered by exam type at retrieval time so TOEFL feedback is never contaminated by TELC examples

---

### Error Taxonomy

A structured error taxonomy (`error-tagging.json`) classifies errors into five categories used in feedback generation and weak-point detection:

- **Syntactic**: subject-verb agreement, tense, articles, prepositions, fragments, conditionals
- **Lexical**: word choice, collocations, vocabulary range, word forms, register, false friends
- **Discourse Cohesion**: missing linkers, weak topic sentences, poor logical progression, inadequate conclusion
- **Task Achievement**: off-topic responses, missing key points, insufficient development
- **Speaking-Specific**: fillers/pauses, intonation/stress, pronunciation clarity, pacing

---

## Tech Stack

### Backend
- **FastAPI** + Uvicorn
- **SQLite** via SQLAlchemy ORM (auto-migrates new columns on startup)
- **Ollama** — local LLM hosting (`llama3.2:3b`)
- **LangChain** — LLM orchestration and prompt management
- **ChromaDB** — vector store for RAG
- **HuggingFace Sentence Transformers** — `intfloat/e5-base-v2` embeddings
- **Faster-Whisper** — speech-to-text transcription
- **pydub / torchaudio** — audio processing
- Python 3.11

### Frontend
- **Next.js** (React + TypeScript)
- **Tailwind CSS**

### Infrastructure
- **Docker Compose** orchestrates three services: FastAPI backend, Ollama LLM, and ChromaDB
- Persistent volumes for Ollama models, ChromaDB data, and the SQLite database

---

## Getting Started

### Prerequisites
- Docker and Docker Compose
- (Optional) A GPU for faster Whisper transcription and Ollama inference

### Run

```bash
docker compose up --build
```

The backend API will be available at `http://localhost:8000`.

To load the golden dataset into ChromaDB on first run:

```bash
docker compose exec backend python scripts/load_rag.py
```

### Environment

Copy `.env.example` to `.env` and fill in your values (API keys, database path, etc.) before starting.

---

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/feedback/writing` | Submit an essay for AI feedback and scoring |
| `POST` | `/api/v1/feedback/speaking` | Upload an audio file for transcription and feedback |
| `POST` | `/api/v1/feedback/reading` | Record a reading comprehension result |
| `GET` | `/api/v1/progress/{student_id}` | Full attempt history for a student |
| `GET` | `/api/v1/progress/{student_id}/weak-points` | Weak-skill analysis with improvement advice |
| `GET` | `/api/v1/progress/{student_id}/prediction` | Score trend and 4-week projection |
| `GET` | `/health` | Health check |

---

## Project Structure

```
toefl_platform/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── feedback/       # Writing, speaking, reading endpoints
│   │   │   └── progress/       # Analytics endpoints
│   │   ├── core/               # Database, config, security
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/            # Pydantic schemas
│   │   └── services/           # Feedback generation, RAG, Whisper, progress
│   ├── data/                   # Golden dataset (JSON)
│   ├── scripts/                # RAG loader script
│   └── Dockerfile
├── frontend/
│   └── app/auth/dashboard/     # Next.js writing feedback dashboard
├── domains/
│   ├── toefl/                  # TOEFL-specific NLP and service logic
│   └── telc/                   # TELC-specific NLP and service logic
├── docker-compose.yml
├── error-tagging.json          # Structured error taxonomy
└── data.json                   # Sample data
```

---

## Roadmap

- **Listening Integration** — automated comprehension exercises and scoring for both TOEFL Listening and TELC Hören
- **Lesen / Reading Module** — structured reading passage interface with answer validation
- **IELTS Support** — Task 1 (graph description) and Task 2 (essay), Speaking Parts 1–3
- **TELC A1/A2** — extend the German exam track to beginner levels
- **Additional Language Exams** — DELF/DALF (French), DELE (Spanish), and other standardized tests
- **User Authentication** — secure accounts, per-user dashboards, and study plans
- **Adaptive Practice** — automatically suggest exercises based on detected weak points
