"""Rule-based candidate scoring (max 100 points).

Breakdown (per technical task):
  - Skill overlap >= 60% of required skills        -> +50
  - years_of_experience >= job.min_experience_years -> +30
  - >= 3 required skills mentioned in resume_text   -> +20
"""


def _normalize(skills) -> set:
    return {str(s).strip().lower() for s in (skills or []) if str(s).strip()}


def compute_score(application: dict, job: dict) -> int:
    required = _normalize(job.get("required_skills"))
    candidate = _normalize(application.get("skills"))
    resume_text = (application.get("resume_text") or "").lower()

    score = 0

    # 1. Skill overlap (+50)
    if required:
        overlap_ratio = len(required & candidate) / len(required)
        if overlap_ratio >= 0.60:
            score += 50

    # 2. Experience (+30)
    min_exp = job.get("min_experience_years", 0) or 0
    if application.get("years_of_experience", 0) >= min_exp:
        score += 30

    # 3. Resume keyword hits (+20)
    if required:
        hits = sum(1 for skill in required if skill in resume_text)
        if hits >= 3:
            score += 20

    return score
