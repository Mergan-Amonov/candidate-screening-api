"""Unit tests for the rule-based scoring logic (no DB / no network)."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.scoring_service import compute_score


JOB = {
    "required_skills": ["python", "fastapi", "mongodb", "docker"],
    "min_experience_years": 2,
}


def test_perfect_candidate_scores_100():
    application = {
        "skills": ["python", "fastapi", "mongodb", "docker"],
        "years_of_experience": 5,
        "resume_text": "Expert in python, fastapi and mongodb with docker experience.",
    }
    assert compute_score(application, JOB) == 100


def test_no_match_scores_zero():
    application = {
        "skills": ["java", "spring"],
        "years_of_experience": 0,
        "resume_text": "Frontend designer who loves figma.",
    }
    assert compute_score(application, JOB) == 0


def test_experience_only():
    application = {
        "skills": [],
        "years_of_experience": 3,
        "resume_text": "Generalist.",
    }
    # experience >= 2 -> +30, no skill overlap, no keyword hits
    assert compute_score(application, JOB) == 30


def test_skills_but_low_experience():
    application = {
        "skills": ["python", "fastapi", "mongodb"],  # 3/4 = 75% overlap -> +50
        "years_of_experience": 0,                      # below min -> +0
        "resume_text": "python fastapi mongodb developer",  # 3 hits -> +20
    }
    assert compute_score(application, JOB) == 70


def test_skill_overlap_below_threshold():
    application = {
        "skills": ["python"],  # 1/4 = 25% -> no +50
        "years_of_experience": 5,  # +30
        "resume_text": "python only",  # 1 hit -> no +20
    }
    assert compute_score(application, JOB) == 30
