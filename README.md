# Candidate Screening Platform API

**FastAPI + MongoDB + Local Transformer AI (HuggingFace)**

A recruiting backend where recruiters create job postings, candidates apply, and
each application is automatically **scored (0–100)** in the background and given an
AI **department recommendation** (Backend vs AI/ML) using a local embedding model.
No external AI APIs are used — all inference runs locally.

---

## Features

- JWT authentication (register / login), bcrypt-free PBKDF2 password hashing
- Role-based access: only **admin** can deactivate jobs
- Job management with filtering & pagination
- Candidate applications with duplicate / active-job validation
- Background scoring pipeline: `submitted → processing → scored`
- Rule-based score (skills, experience, resume keywords)
- Local Transformer department recommendation (`all-MiniLM-L6-v2`, cosine similarity)
- MongoDB indexes, structured logging, configuration via `.env`

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI, Uvicorn |
| DB | MongoDB + Motor (async driver) |
| Validation | Pydantic v2, pydantic-settings |
| Auth | python-jose (JWT), passlib (PBKDF2-SHA256) |
| AI | sentence-transformers `all-MiniLM-L6-v2`, PyTorch (CPU) |
| Background | FastAPI BackgroundTasks |

---

## Project Structure

```
app/
  core/        config.py, jwt.py, security.py, dependencies.py
  db/          mongodb.py
  routers/     auth.py, jobs.py, applications.py
  schemas/     user_schema.py, job_schema.py, application_schema.py
  services/    job_service.py, application_service.py,
               scoring_service.py, ai_service.py, background.py
  main.py
tests/         test_scoring.py
```

---

## Architecture & Request Flow

```
                       ┌──────────────────────────────────────────┐
   Recruiter / Admin   │  FastAPI app (app/main.py)               │
   ──────────────────► │   ├─ /auth      JWT register / login     │
   (JWT protected)     │   ├─ /jobs      CRUD + filters           │
                       │   └─ /applications  list + ai-evaluation │
                       └───────────────┬──────────────────────────┘
                                       │
   Candidate (public)                  │  insert (status: submitted)
   POST /jobs/{id}/apply ─────────────►│──────────────► MongoDB (Motor, async)
                                       │                     ▲
                                       │ BackgroundTasks     │ update
                                       ▼                     │ (status: scored)
                       ┌──────────────────────────────────────────┐
                       │  process_application (services/background)│
                       │   1. status → processing                  │
                       │   2. rule-based score  (scoring_service)  │
                       │   3. AI department eval (ai_service)       │
                       │      via asyncio.to_thread (non-blocking) │
                       │   4. status → scored, persist results     │
                       └──────────────────────────────────────────┘
```

The embedding model is loaded **once** at process start (`ai_service.py` module
import) and reused for every evaluation.

**Status flow:** `submitted` → `processing` → `scored`

---

## 1. Setup

```bash
git clone <repository-url>
cd candidate-screening-api

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS

pip install -r requirements.txt
```

## 2. Run MongoDB

Make sure MongoDB is running locally on the default port:

```bash
mongod --dbpath ./.mongo-data --port 27017
```

Default connection string: `mongodb://localhost:27017`

## 3. AI Model Download

The embedding model is downloaded automatically from HuggingFace on **first run**
and cached locally (`~/.cache/huggingface`). To pre-download it manually:

```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

To store the model cache on a different drive, set `HF_HOME` before running, e.g.:

```powershell
$env:HF_HOME = "E:\hf_cache"
```

## 4. Environment Variables

Copy `.env.example` to `.env` and adjust:

| Variable | Default | Description |
|---|---|---|
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGO_DB_NAME` | `candidate_screening` | Database name |
| `JWT_SECRET_KEY` | _(required)_ | Secret used to sign JWTs |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_EXPIRE_HOURS` | `2` | Token lifetime in hours |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Local embedding model |

## 5. Run the Server

```bash
python -m uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Swagger docs: http://127.0.0.1:8000/docs

## 6. Run Tests

```bash
pip install pytest
pytest
```

`tests/test_scoring.py` verifies the rule-based scoring logic (no DB required).

---

## API Overview

### Auth
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | — | Register (`role`: admin / recruiter) |
| POST | `/auth/login` | — | Login → `access_token` |

### Jobs (JWT required)
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/jobs/` | user | Create job |
| GET | `/jobs/` | user | List jobs (filters below) |
| GET | `/jobs/{id}` | user | Get a job |
| PATCH | `/jobs/{id}/deactivate` | **admin** | Deactivate a job |

`GET /jobs/` filters: `is_active`, `required_skill` (contains), `min_experience_lte`, `limit`, `skip`.

### Applications
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/jobs/{job_id}/apply` | — | Apply to a job (triggers scoring) |
| GET | `/applications` | user | List applications (filters: `job_id`, `status`, `min_score`, `limit`, `skip`) |
| GET | `/applications/{id}/ai-evaluation` | — | AI department recommendation |

### Health
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/` | — | Health check → `{"status": "ok"}` |

---

## Data Models

**Job** (`jobs` collection)
```json
{
  "title": "Backend Developer",
  "description": "FastAPI role",
  "required_skills": ["python", "fastapi", "mongodb"],
  "min_experience_years": 2,
  "is_active": true,
  "created_at": "2026-06-11T12:00:00Z"
}
```

**Application** (`applications` collection)
```json
{
  "job_id": "6a2aa538599e50a57b3018d0",
  "candidate_name": "John Doe",
  "email": "john@example.com",
  "years_of_experience": 3,
  "skills": ["python", "fastapi", "mongodb"],
  "resume_text": "Backend developer ...",
  "status": "scored",
  "score": 100,
  "ai_department": "backend",
  "ai_department_score": 0.608,
  "created_at": "2026-06-11T12:00:00Z",
  "scored_at": "2026-06-11T12:00:01Z",
  "ai_processed_at": "2026-06-11T12:00:01Z"
}
```

**Indexes** (created at startup): unique `(job_id, email)` on `applications`
(blocks duplicate applications), plus `status`, `score`, and `jobs.is_active`.

---

## Error Responses

| Status | When |
|---|---|
| `401 Unauthorized` | Missing / invalid JWT, or wrong login credentials |
| `403 Forbidden` | Non-admin calls an admin-only route (job deactivate) |
| `404 Not Found` | Job / application id does not exist |
| `400 Bad Request` | Invalid object id, or applying to an inactive job |
| `409 Conflict` | Same email already applied to the same job |
| `422 Unprocessable Entity` | Body validation failed (e.g. invalid `role` or email) |

---

## Scoring Logic (max 100)

| Rule | Points |
|---|---|
| Skill overlap ≥ 60% of required skills | +50 |
| `years_of_experience` ≥ job's `min_experience_years` | +30 |
| ≥ 3 required skills mentioned in `resume_text` | +20 |

## AI Department Recommendation

The resume text is embedded and compared (cosine similarity) against two hardcoded
reference profiles; the higher-scoring department wins.

- **Backend**: REST APIs, databases, distributed systems, caching, microservices, docker, kubernetes, authentication, message queues
- **AI/ML**: machine learning, transformers, pytorch, fine-tuning, embeddings, NLP, deep learning, model inference

---

## Sample Requests (curl)

```bash
# 1. Register a recruiter
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"rec@example.com","password":"secret123","role":"recruiter"}'

# 2. Login (form-encoded; username = email)
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=rec@example.com&password=secret123"
# -> {"access_token":"<TOKEN>","token_type":"bearer"}

# 3. Create a job (use the token)
curl -X POST http://127.0.0.1:8000/jobs/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Backend Developer","description":"FastAPI role","required_skills":["python","fastapi","mongodb"],"min_experience_years":2,"is_active":true}'

# 4. List jobs with filters
curl "http://127.0.0.1:8000/jobs/?required_skill=python&limit=5" \
  -H "Authorization: Bearer <TOKEN>"

# 5. Apply to a job (public)
curl -X POST http://127.0.0.1:8000/jobs/<JOB_ID>/apply \
  -H "Content-Type: application/json" \
  -d '{"candidate_name":"John Doe","email":"john@example.com","years_of_experience":3,"skills":["python","fastapi","mongodb"],"resume_text":"Backend developer experienced with python, fastapi and mongodb building REST APIs."}'

# 6. List scored applications
curl "http://127.0.0.1:8000/applications?min_score=50" \
  -H "Authorization: Bearer <TOKEN>"

# 7. Get AI evaluation
curl http://127.0.0.1:8000/applications/<APPLICATION_ID>/ai-evaluation
```

---

## Design Decisions

- AI model is loaded **once** at import (not per request)
- CPU-bound AI inference runs via `asyncio.to_thread` so it never blocks the event loop
- Background tasks keep the apply endpoint fast and non-blocking
- A unique compound index on `(job_id, email)` enforces "no duplicate application"
- Configuration is environment-driven; no secrets are hardcoded
