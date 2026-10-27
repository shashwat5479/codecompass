"""Unit tests for the recommendation engine. Pure Python: no database or HTTP needed."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.recommendation import (  # noqa: E402
    ProfileView,
    build_insights,
    build_job_skill_roadmap,
    estimate_experience_years,
    find_career_for_title,
    generate_recommendations,
    score_job,
)
from app.skills import expand_skills, extract_skills_from_text, normalize_skill_name  # noqa: E402

FRONTEND_PROFILE = {
    "skills": ["React", "JavaScript", "HTML", "CSS", "Git"],
    "career_interest": "I want to be a frontend developer",
    "education_level": "Bachelor's degree in Computer Science",
    "experience_years": 1,
}
DATA_PROFILE = {
    "skills": ["Python", "SQL", "Excel", "Statistics", "Power BI", "Data Visualization"],
    "career_interest": "Data analyst",
    "education_level": "Bachelor's in Statistics",
    "experience_years": 2,
}


def by_title(recs, title):
    return next(r for r in recs if r["title"] == title)


def test_normalization_and_aliases():
    assert normalize_skill_name(" ReactJS ") == "react"
    assert normalize_skill_name("Node JS") == "node.js"
    assert normalize_skill_name("K8s") == "kubernetes"
    assert normalize_skill_name("Postgres") == "postgresql"


def test_text_extraction_uses_aliases_and_avoids_substrings():
    found = extract_skills_from_text("Built apps with ReactJS and Postgres on AWS using k8s. Wrote JavaScript and Java.")
    assert {"React", "PostgreSQL", "AWS", "Kubernetes", "JavaScript", "Java"} <= set(found)
    assert "Git" not in extract_skills_from_text("Hosted on GitHub")  # 'Git' must not match inside 'GitHub'


def test_implied_and_related_skills_give_partial_credit():
    credits = expand_skills({"react": 0.9, "pytorch": 1.0})
    assert credits["javascript"].kind == "implied" and 0.6 < credits["javascript"].value < 0.9
    assert credits["tensorflow"].kind == "related"
    assert credits["react"].kind == "direct"


def test_ranking_follows_the_profile():
    front = generate_recommendations(FRONTEND_PROFILE)
    assert front[0]["title"] == "Frontend Developer"
    data = generate_recommendations(DATA_PROFILE)
    assert data[0]["title"] == "Data Analyst"
    assert by_title(data, "Data Analyst")["readiness"] == "Job-ready"


def test_scores_are_bounded_sorted_and_ranked():
    recs = generate_recommendations(FRONTEND_PROFILE)
    scores = [r["score"] for r in recs]
    assert scores == sorted(scores, reverse=True)
    assert all(0.0 < s < 1.0 for s in scores)
    assert [r["rank"] for r in recs] == list(range(1, len(recs) + 1))


def test_breakdown_is_consistent_with_score():
    rec = generate_recommendations(FRONTEND_PROFILE)[0]
    assert abs(sum(c["weight"] for c in rec["score_breakdown"]) - 100) <= 2
    assert abs(sum(c["points"] for c in rec["score_breakdown"]) - rec["score"] * 100) <= 2


def test_missing_data_is_excluded_not_penalised():
    no_goal = generate_recommendations({**FRONTEND_PROFILE, "career_interest": ""})[0]
    assert "interest" not in {c["key"] for c in no_goal["score_breakdown"]}
    assert "interest" in {c["key"] for c in no_goal["not_scored"]}


def test_empty_profile_is_safe_and_low():
    recs = generate_recommendations({})
    assert len(recs) == 14
    assert max(r["score"] for r in recs) < 0.25
    assert recs[0]["confidence"] == "Low"


def test_distinctive_skills_weigh_more_than_common_ones():
    # DevOps Engineer requires Linux, Docker, Kubernetes, CI/CD, Git, Bash.
    # Git is listed by many careers (low IDF weight); Bash is rare (high weight).
    core = ["Linux", "Docker", "Kubernetes", "CI/CD"]
    missing_git = by_title(generate_recommendations({"skills": core + ["Bash"]}), "DevOps Engineer")
    missing_bash = by_title(generate_recommendations({"skills": core + ["Git"]}), "DevOps Engineer")
    assert missing_git["required_coverage"] > missing_bash["required_coverage"]


def test_related_skill_gives_partial_not_full_credit():
    only_docker = by_title(generate_recommendations({"skills": ["Docker"]}), "DevOps Engineer")
    assert any(p["skill"] == "Kubernetes" and p["via"] == "Docker" for p in only_docker["partial_skills"])
    assert "Kubernetes" not in only_docker["matching_skills"]


def test_resume_backed_skills_score_higher_and_are_reported():
    declared = generate_recommendations({**DATA_PROFILE})
    backed = generate_recommendations({**DATA_PROFILE, "resume_skills": ["Python", "SQL", "Excel"]})
    assert by_title(backed, "Data Analyst")["score"] > by_title(declared, "Data Analyst")["score"]
    assert set(by_title(backed, "Data Analyst")["resume_matching_skills"]) == {"Python", "SQL", "Excel"}


def test_proficiency_levels_matter():
    novice = generate_recommendations({"skill_levels": {"Python": 0.6, "SQL": 0.6}})
    expert = generate_recommendations({"skill_levels": {"Python": 1.0, "SQL": 1.0}})
    assert by_title(expert, "Data Analyst")["score"] > by_title(novice, "Data Analyst")["score"]


def test_missing_skills_are_ordered_by_importance_and_roadmap_is_personalised():
    rec = by_title(generate_recommendations(FRONTEND_PROFILE), "Full-Stack Developer")
    assert rec["missing_skills"]  # Node.js, TypeScript, SQL are still missing
    assert rec["career_roadmap"][0]["description"].count(rec["missing_skills"][0]) == 1
    assert [s["title"] for s in rec["career_roadmap"]] == [
        "Phase 1: Close your core gaps",
        "Phase 2: Strengthen what you partly know",
        "Phase 3: Build a proof-of-skill project",
        "Phase 4: Certify and get interview-ready",
    ]


def test_insights_surface_skills_shared_across_top_careers():
    recs = generate_recommendations(FRONTEND_PROFILE)
    insights = build_insights(FRONTEND_PROFILE, recs)
    assert insights["best_fit"] == "Frontend Developer"
    assert insights["top_skills_to_learn"]
    assert insights["profile_strength"]["tips"]


def test_experience_years_merges_overlaps_and_handles_present():
    today = date(2026, 1, 1)
    assert estimate_experience_years([("2020", "2022")], today) == 2.0
    assert estimate_experience_years([("2020", "2022"), ("2021", "2023")], today) == 3.0
    assert estimate_experience_years([("2025-01", "present")], today) == 1.0
    assert estimate_experience_years([(None, None), ("n/a", "n/a")], today) == 2.0


def test_job_scoring_rewards_fit_and_flags_gaps():
    profile = ProfileView({**FRONTEND_PROFILE, "work_mode": "Remote"})
    good = score_job(
        {"title": "Frontend Developer", "required_skills": "React, JavaScript, CSS, HTML",
         "experience": "0-2 years", "work_mode": "Remote", "location": "Remote"},
        profile,
    )
    poor = score_job(
        {"title": "DevOps Engineer", "required_skills": "Kubernetes, Terraform, Linux, Docker",
         "experience": "4-6 years", "work_mode": "Onsite", "location": "Pune"},
        profile,
    )
    assert good["match_percentage"] > poor["match_percentage"] + 30
    assert good["missing_skills"] == [] and set(poor["missing_skills"]) >= {"Kubernetes", "Terraform"}
    assert any("stretch" in r for r in poor["reasons"])


def test_job_title_lookup_and_roadmap():
    assert find_career_for_title("Senior Data Analyst")["title"] == "Data Analyst"
    assert find_career_for_title("Chef") is None
    roadmap = build_job_skill_roadmap("Backend Developer", "Python, FastAPI, Redis, Docker", user_skills=["Python"])
    assert "Python" in roadmap["matched_skills"]
    assert {"Redis", "Docker"} <= set(roadmap["missing_skills"])
    assert [p["step"] for p in roadmap["roadmap"]] == [1, 2, 3, 4]
    assert roadmap["estimated_weeks"] > 0
