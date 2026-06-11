from sentence_transformers import SentenceTransformer, util

from app.core.config import settings

# Loaded once at import time (single model instance for the whole app).
model = SentenceTransformer(settings.embedding_model)

BACKEND_PROFILE = """
REST APIs, databases, distributed systems, caching, microservices,
docker, kubernetes, authentication, message queues, backend architecture
"""

AI_PROFILE = """
machine learning, transformers, pytorch, model training, fine-tuning,
embeddings, NLP, deep learning, model inference
"""


def ai_department_eval(resume_text: str):
    """Return (department, cosine_score) for the better-matching department."""
    embeddings = model.encode(
        [resume_text, BACKEND_PROFILE, AI_PROFILE],
        convert_to_tensor=True,
    )

    backend_score = util.cos_sim(embeddings[0], embeddings[1])[0][0]
    ai_score = util.cos_sim(embeddings[0], embeddings[2])[0][0]

    if backend_score >= ai_score:
        return "backend", round(float(backend_score), 3)
    return "ai/ml", round(float(ai_score), 3)
