"""Explainable career + job recommendation engine (v2).

How a score is built
--------------------
Every career (and job) is scored from independent, individually explainable components,
each between 0 and 1. The final score is their weighted average. Components that cannot be
judged for a given user (e.g. no career goal entered) are dropped and the remaining
weights are re-normalised, so missing data never silently pulls a score up or down.

    skills      70%  IDF-weighted coverage of required (75%) + recommended (25%) skills,
                     with partial credit for implied / related skills and proficiency.
                     Skills proven by a resume, project or certification are rated higher
                     than skills that are only claimed.
    interest    15%  How well the career matches the user's written career goal.
    experience   9%  Years of experience vs. the seniority the career expects.
    education    6%  Education level / field vs. what the career asks for.

IDF weighting means rare, distinguishing skills (Kubernetes, Figma) count for more than
skills every career lists (Git, SQL).
"""
from __future__ import annotations

import math
import re
from collections import Counter
from datetime import date
from typing import Any, Iterable

from app.catalog import CAREER_CATALOG
from app.skills import (
    Credit,
    expand_skills,
    extract_skills_from_text,
    normalize_skill_name,
    split_skill_list,
)

__all__ = [
    "CAREER_CATALOG",
    "normalize_skill_name",
    "ProfileView",
    "generate_recommendations",
    "score_job",
    "build_job_skill_roadmap",
    "build_insights",
    "estimate_experience_years",
    "find_career_for_title",
]

CAREER_WEIGHTS = {"skills": 0.70, "interest": 0.15, "experience": 0.09, "education": 0.06}
JOB_WEIGHTS = {"skills": 0.60, "preferred": 0.08, "role": 0.15, "experience": 0.12, "preferences": 0.05}
COMPONENT_LABELS = {
    "skills": "Skill match",
    "preferred": "Nice-to-have skills",
    "interest": "Career-goal fit",
    "role": "Role relevance",
    "experience": "Experience fit",
    "education": "Education fit",
    "preferences": "Work-mode & location",
}
REQUIRED_SHARE = 0.75
MIN_USEFUL_CREDIT = 0.30      # credits below this are treated as "not really covered"
MATCHED_THRESHOLD = 0.50      # a directly-listed skill counts as matched from here
PARTIAL_THRESHOLD = 0.40      # implied/related skills count as "likely covered" from here
DIFFICULTY_YEARS = {"beginner friendly": 0.0, "intermediate": 1.0, "advanced": 2.0}


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def _key(skill: str) -> str:
    return normalize_skill_name(skill)


def _clip(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _pct(value: float) -> int:
    return int(round(_clip(value) * 100))


def _effective_credit(credits: dict[str, Credit], skill: str) -> Credit:
    credit = credits.get(_key(skill))
    if credit is None or credit.value < MIN_USEFUL_CREDIT:
        return Credit(0.0, "none", None)
    return credit


def _idf_table(catalog: list[dict]) -> dict[str, float]:
    document_frequency: Counter[str] = Counter()
    for career in catalog:
        for key in {_key(s) for s in career["required_skills"] + career["recommended_skills"]}:
            document_frequency[key] += 1
    total = max(len(catalog), 1)
    return {key: 1.0 + math.log(total / count) for key, count in document_frequency.items()}


def _weight(idf: dict[str, float], skill: str, total: int) -> float:
    # Unknown skills (custom job requirements) get a neutral, mid-range weight.
    return idf.get(_key(skill), 1.0 + math.log(max(total, 3) / 3))


def _weighted_coverage(
    skills: list[str], credits: dict[str, Credit], idf: dict[str, float], total: int
) -> float:
    if not skills:
        return 0.0
    weights = [_weight(idf, s, total) for s in skills]
    covered = sum(w * _effective_credit(credits, s).value for w, s in zip(weights, skills))
    return covered / sum(weights)


def _classify(
    skills: list[str], credits: dict[str, Credit], idf: dict[str, float], total: int
) -> tuple[list[str], list[dict[str, Any]], list[str]]:
    """Split target skills into (matched, partial, missing); missing is most-important-first."""
    matched: list[str] = []
    partial: list[dict[str, Any]] = []
    missing: list[str] = []
    for skill in skills:
        credit = _effective_credit(credits, skill)
        if credit.kind == "direct" and credit.value >= MATCHED_THRESHOLD:
            matched.append(skill)
        elif credit.kind in {"implied", "related"} and credit.value >= PARTIAL_THRESHOLD:
            partial.append(
                {"skill": skill, "coverage": _pct(credit.value), "via": credit.via, "kind": credit.kind}
            )
        else:
            missing.append(skill)
    missing.sort(key=lambda s: -_weight(idf, s, total))
    partial.sort(key=lambda p: -p["coverage"])
    return matched, partial, missing


def _week_midpoint(text: str) -> float:
    numbers = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", text or "")]
    return sum(numbers[:2]) / len(numbers[:2]) if numbers else 3.0


def _join(items: Iterable[str], limit: int = 3) -> str:
    items = [str(i) for i in items if i]
    if len(items) <= limit:
        return ", ".join(items)
    return ", ".join(items[:limit]) + f" +{len(items) - limit} more"


# --------------------------------------------------------------------------- #
# Experience / education parsing
# --------------------------------------------------------------------------- #
_YEAR_RE = re.compile(r"(?<!\d)((?:19|20)\d{2})(?!\d)")
_MONTH_RE = re.compile(
    r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*", re.IGNORECASE
)
_MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
_PRESENT_WORDS = ("present", "current", "now", "ongoing", "today")


def _parse_month_year(text: str | None) -> float | None:
    """Parse '2022', '2022-06', 'Jun 2022', '06/2022' -> fractional year, else None."""
    if not text:
        return None
    year_match = _YEAR_RE.search(text)
    if not year_match:
        return None
    year = int(year_match.group(1))
    month = 1
    named = _MONTH_RE.search(text)
    if named:
        month = _MONTHS.index(named.group(1).lower()[:3]) + 1
    else:
        numeric = re.search(r"(?<!\d)(0?[1-9]|1[0-2])(?!\d)", text.replace(year_match.group(1), " "))
        if numeric:
            month = int(numeric.group(1))
    return year + (month - 1) / 12


def estimate_experience_years(
    periods: Iterable[tuple[str | None, str | None]], today: date | None = None
) -> float:
    """Total years of experience from (start, end) strings. Overlapping periods count once.

    Unparseable rows fall back to one year each so a filled-in entry is never worth zero.
    """
    today = today or date.today()
    now = today.year + (today.month - 1) / 12
    intervals: list[tuple[float, float]] = []
    fallback = 0.0
    for start_raw, end_raw in periods:
        start = _parse_month_year(start_raw)
        if start is None:
            fallback += 1.0
            continue
        end_text = (end_raw or "").strip().lower()
        end = now if (not end_text or any(w in end_text for w in _PRESENT_WORDS)) else _parse_month_year(end_text)
        if end is None:
            end = now
        if end > start:
            intervals.append((start, min(end, now)))
    intervals.sort()
    total = 0.0
    current_start = current_end = None
    for start, end in intervals:
        if current_end is None or start > current_end:
            if current_end is not None:
                total += current_end - current_start
            current_start, current_end = start, end
        else:
            current_end = max(current_end, end)
    if current_end is not None:
        total += current_end - current_start
    return round(min(total + fallback, 20.0), 1)


def education_rank(text: str | None) -> int:
    """0 unknown, 1 diploma/school, 2 bachelor, 3 master, 4 doctorate."""
    t = (text or "").lower()
    if not t.strip():
        return 0
    if re.search(r"\b(ph\.?\s?d|doctorate|doctoral)\b", t):
        return 4
    if re.search(r"\b(master|masters|master's|m\.?\s?tech|mtech|mca|m\.?\s?sc|msc|mba|m\.e)\b", t):
        return 3
    if re.search(r"\b(bachelor|bachelors|bachelor's|b\.?\s?tech|btech|bca|b\.?\s?sc|bsc|bba|b\.com|b\.e|undergraduate|degree|graduate)\b", t):
        return 2
    if re.search(r"\b(diploma|associate|certificate|high school|secondary|12th|intermediate|polytechnic)\b", t):
        return 1
    return 0


def _career_min_education(career: dict) -> int:
    text = career.get("education", "").lower()
    if any(w in text for w in ("portfolio", "bootcamp", "equivalent", "self-taught", "strong project")):
        return 1
    if "master" in text and "bachelor" not in text:
        return 3
    return 2


_FIELD_TERMS = {
    "computer", "science", "software", "information", "technology", "it", "cs", "data",
    "statistics", "mathematics", "design", "business", "engineering", "cybersecurity",
    "analytics", "artificial", "intelligence", "interaction", "electronics",
}


def _education_component(rank: int, user_text: str, career: dict) -> float | None:
    if rank == 0:
        return None
    needed = _career_min_education(career)
    if rank >= needed:
        base = 1.0
    elif rank == needed - 1:
        base = 0.65
    else:
        base = 0.4
    user_terms = set(re.findall(r"[a-z]+", user_text.lower())) & _FIELD_TERMS
    career_terms = set(re.findall(r"[a-z]+", career.get("education", "").lower())) & _FIELD_TERMS
    if base < 1.0 and user_terms & career_terms:
        base = min(1.0, base + 0.1)
    return base


def _experience_component(years: float, exp_text: str, career: dict) -> float:
    target = DIFFICULTY_YEARS.get(str(career.get("difficulty_level", "")).lower(), 1.0)
    base = 1.0 if years >= target or target == 0 else 0.5 + 0.5 * (years / target)
    if exp_text:
        phrases = [career["title"].lower(), *[j.lower() for j in career.get("related_jobs", [])]]
        if any(p in exp_text for p in phrases):
            base = min(1.0, base + 0.2)
    return base


# --------------------------------------------------------------------------- #
# Interest / goal alignment
# --------------------------------------------------------------------------- #
_STOPWORDS = {
    "a", "an", "and", "the", "or", "of", "in", "on", "to", "for", "with", "my", "i", "am",
    "want", "wants", "become", "be", "become", "get", "job", "jobs", "role", "roles",
    "career", "careers", "work", "working", "top", "best", "strong", "good", "great",
    "skills", "skill", "experience", "field", "position", "company", "companies", "like",
    "love", "interested", "interest", "build", "building", "learn", "learning", "at",
    "as", "is", "it", "me", "into", "from", "that", "this", "lot", "more", "very",
}
_GENERIC = {"developer", "engineer", "specialist", "professional", "associate", "junior", "senior", "lead", "manager"}
_ROLE_REWRITES = [
    (re.compile(r"\bengineers?\b"), "developer"),
    (re.compile(r"\bprogrammers?\b"), "developer"),
    (re.compile(r"\bdevelopers\b"), "developer"),
    (re.compile(r"\bswe\b|\bsde\b"), "software developer"),
    (re.compile(r"\bfront end\b"), "frontend"),
    (re.compile(r"\bback end\b"), "backend"),
    (re.compile(r"\bfull stack\b"), "fullstack"),
    (re.compile(r"\banalytics\b"), "analyst"),
    (re.compile(r"\bdesigners\b"), "designer"),
    (re.compile(r"\banalysts\b"), "analyst"),
    (re.compile(r"\bscientists\b"), "scientist"),
    (re.compile(r"\btesters?\b"), "qa"),
]


def _phrase(text: str) -> str:
    t = re.sub(r"[^a-z0-9+#.]+", " ", (text or "").lower().replace("/", " ")).strip()
    t = re.sub(r"\bfull-?\s?stack\b", "fullstack", t)
    for pattern, replacement in _ROLE_REWRITES:
        t = pattern.sub(replacement, t)
    return re.sub(r"\s+", " ", t)


def _tokens(text: str) -> set[str]:
    return {w.strip(".") for w in _phrase(text).split() if len(w.strip(".")) > 1 and w not in _STOPWORDS}


def _token_weight(token: str) -> float:
    return 0.4 if token in _GENERIC else 1.0


def interest_alignment(
    interest_text: str, phrases: list[str], core_text: str, skill_text: str = ""
) -> float | None:
    """0..1 similarity between a free-text career goal and a role. None if no goal given."""
    if not interest_text.strip():
        return None
    goal = _phrase(interest_text)
    for p in phrases:
        needle = _phrase(p)
        if needle and re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", goal):
            return 1.0
    user_tokens = _tokens(interest_text)
    if not user_tokens:
        return 0.0
    core = _tokens(core_text)
    skills = _tokens(skill_text)
    score = sum(_token_weight(t) for t in user_tokens if t in core)
    score += 0.6 * sum(_token_weight(t) for t in user_tokens if t in skills and t not in core)
    return _clip(score / min(sum(_token_weight(t) for t in user_tokens), 3.0))


# --------------------------------------------------------------------------- #
# Profile view
# --------------------------------------------------------------------------- #
class ProfileView:
    """Pre-computed, read-only view of a user's profile used by all scorers.

    Accepted keys in ``profile`` (all optional):
        skills            declared skill names
        skill_levels      {name: strength 0..1} (overrides default 0.85 strength)
        resume_skills     skills found in uploaded resumes
        project_skills    skills used in listed projects
        certifications    certification names the user holds
        education_level, education_text, career_interest, experience_years,
        experience_text, work_mode, preferred_location
    """

    def __init__(self, profile: dict):
        levels: dict[str, float] = {}

        def bump(name: str, strength: float) -> None:
            key = _key(name)
            if key:
                levels[key] = max(levels.get(key, 0.0), _clip(strength))

        declared_keys: set[str] = set()
        for name in profile.get("skills", []) or []:
            if str(name).strip():
                bump(name, 0.85)
                declared_keys.add(_key(name))
        for name, strength in (profile.get("skill_levels") or {}).items():
            bump(name, float(strength))
            declared_keys.add(_key(name))
        self.resume_keys = {_key(s) for s in profile.get("resume_skills", []) or [] if str(s).strip()}
        for key in self.resume_keys:
            bump(key, 0.9)
        self.project_keys = {_key(s) for s in profile.get("project_skills", []) or [] if str(s).strip()}
        for key in self.project_keys:
            bump(key, 0.8)
        # Corroboration: a skill the user declares AND that appears in a resume/project is stronger.
        for key in declared_keys & (self.resume_keys | self.project_keys):
            levels[key] = min(1.0, levels.get(key, 0.0) + 0.1)

        self.levels = levels
        self.credits = expand_skills(levels)
        self.declared_keys = declared_keys
        self.certifications = [str(c).lower() for c in profile.get("certifications", []) or [] if str(c).strip()]
        self.interest_text = str(profile.get("career_interest") or "").strip()
        self.education_text = str(profile.get("education_text") or profile.get("education_level") or "")
        self.education_rank = education_rank(self.education_text)
        self.years = float(profile.get("experience_years") or 0)
        self.experience_text = str(profile.get("experience_text") or "").lower()
        self.work_mode = str(profile.get("work_mode") or "").strip().lower()
        self.preferred_location = str(profile.get("preferred_location") or "").strip().lower()

    @property
    def skill_count(self) -> int:
        return len(self.levels)

    def confidence(self) -> tuple[float, str]:
        """How much real data backs the recommendations (not how good the matches are)."""
        skills_part = 1.0 if self.skill_count >= 6 else 0.6 if self.skill_count >= 3 else 0.3 if self.skill_count else 0.0
        value = (
            0.40 * skills_part
            + 0.25 * (1.0 if self.resume_keys else 0.0)
            + 0.15 * (1.0 if self.interest_text else 0.0)
            + 0.10 * (1.0 if self.education_rank else 0.0)
            + 0.10 * (1.0 if (self.years > 0 or self.project_keys or self.certifications) else 0.0)
        )
        label = "High" if value >= 0.7 else "Medium" if value >= 0.4 else "Low"
        return round(value, 2), label

    def tips(self) -> list[str]:
        tips = []
        if self.skill_count < 5:
            tips.append("Add at least 5 skills to your profile for sharper matches.")
        if not self.resume_keys:
            tips.append("Upload a PDF/DOCX resume — skills backed by a resume score higher.")
        if not self.interest_text:
            tips.append("Write your career goal in your profile so we can rank roles by interest.")
        if not self.education_rank:
            tips.append("Add your education level to improve education-fit scoring.")
        if not (self.project_keys or self.certifications):
            tips.append("List projects or certifications to show proof of your skills.")
        return tips


# --------------------------------------------------------------------------- #
# Combining components
# --------------------------------------------------------------------------- #
def _combine(
    components: dict[str, float | None], weights: dict[str, float]
) -> tuple[float, list[dict[str, Any]], list[dict[str, str]]]:
    applicable = {k: v for k, v in components.items() if v is not None}
    total_weight = sum(weights[k] for k in applicable) or 1.0
    score = sum(weights[k] * v for k, v in applicable.items()) / total_weight
    breakdown = [
        {
            "key": k,
            "label": COMPONENT_LABELS[k],
            "score": _pct(v),
            "weight": _pct(weights[k] / total_weight),
            "points": round(weights[k] / total_weight * v * 100, 1),
        }
        for k, v in sorted(applicable.items(), key=lambda kv: -weights[kv[0]])
    ]
    skipped = [
        {"key": k, "label": COMPONENT_LABELS[k]} for k, v in components.items() if v is None
    ]
    return score, breakdown, skipped


def _readiness(required_coverage: float) -> str:
    if required_coverage >= 0.85:
        return "Job-ready"
    if required_coverage >= 0.60:
        return "Almost there"
    if required_coverage >= 0.30:
        return "Building foundations"
    return "Getting started"


def _pick_project(career: dict, missing: list[str]) -> str:
    """Prefer the project that practises the most still-missing skills."""
    projects = career["projects"]
    gaps = [m.lower() for m in missing]
    best = max(projects, key=lambda p: sum(g in p.lower() for g in gaps))
    return best if any(g in best.lower() for g in gaps) else projects[0]


# --------------------------------------------------------------------------- #
# Career recommendations
# --------------------------------------------------------------------------- #
def generate_recommendations(user_profile: dict, career_catalog: list[dict] | None = None) -> list[dict]:
    catalog = career_catalog or CAREER_CATALOG
    profile = ProfileView(user_profile)
    idf = _idf_table(catalog)
    total = len(catalog)
    confidence_value, confidence_label = profile.confidence()
    results: list[dict] = []

    for career in catalog:
        required = career["required_skills"]
        recommended = career["recommended_skills"]

        req_matched, req_partial, req_missing = _classify(required, profile.credits, idf, total)
        rec_matched, rec_partial, rec_missing = _classify(recommended, profile.credits, idf, total)

        required_coverage = _weighted_coverage(required, profile.credits, idf, total)
        recommended_coverage = _weighted_coverage(recommended, profile.credits, idf, total)
        skills_score = REQUIRED_SHARE * required_coverage + (1 - REQUIRED_SHARE) * recommended_coverage

        interest_score = interest_alignment(
            profile.interest_text,
            [career["title"], *career.get("related_jobs", [])],
            " ".join([career["title"], career.get("category", ""), *career.get("related_jobs", [])]),
            " ".join(required + recommended),
        )
        components = {
            "skills": skills_score,
            "interest": interest_score,
            "experience": _experience_component(profile.years, profile.experience_text, career),
            "education": _education_component(profile.education_rank, profile.education_text, career),
        }
        raw_score, breakdown, skipped = _combine(components, CAREER_WEIGHTS)
        score = round(_clip(raw_score, 0.02, 0.98), 2)

        matched_all = list(dict.fromkeys(req_matched + rec_matched))
        partial_all = req_partial + [p for p in rec_partial if p["skill"] not in {x["skill"] for x in req_partial}]
        resume_matches = [s for s in required + recommended if _key(s) in profile.resume_keys]

        phases = career.get("roadmap_phases", [])
        total_weeks = sum(_week_midpoint(p.get("estimated_time", "")) for p in phases) or 12.0
        weeks_to_ready = 0 if required_coverage >= 0.98 else max(2, round(total_weeks * (1 - 0.85 * required_coverage)))

        readiness = _readiness(required_coverage)
        strengths = []
        if req_matched:
            strengths.append(
                f"You already cover {len(req_matched)} of {len(required)} core skills ({_join(req_matched)})"
            )
        if req_partial:
            top = req_partial[0]
            strengths.append(f"{top['skill']} is likely covered through your {top['via']} skills")
        goal_note = ""
        if interest_score is not None:
            if interest_score >= 0.8:
                goal_note = "It lines up with your stated career goal."
            elif interest_score < 0.3:
                goal_note = "It differs from your stated goal, so treat it as an adjacent option."
        explanation_parts = [f"{_pct(score)}% fit — {readiness}."]
        if strengths:
            explanation_parts.append("; ".join(strengths) + ".")
        else:
            explanation_parts.append("None of the core skills are on your profile yet, so this is a fresh start.")
        if req_missing:
            explanation_parts.append(f"Biggest gaps: {_join(req_missing, 2)}.")
        if goal_note:
            explanation_parts.append(goal_note)
        if weeks_to_ready:
            explanation_parts.append(f"Estimated {weeks_to_ready} weeks to become job-ready.")

        first_stage = req_missing[:3] or rec_missing[:3]
        partial_names = [p["skill"] for p in partial_all if p["coverage"] < 85]
        second_stage = partial_names[:3] + [s for s in rec_missing if s not in partial_names][:3]
        project = _pick_project(career, req_missing + rec_missing)
        steps = [
            {
                "title": "Phase 1: Close your core gaps",
                "description": (
                    f"Prioritise {_join(first_stage, 4)} — the highest-impact skills you're missing."
                    if first_stage
                    else f"Core skills covered. Keep {_join(required[:3])} sharp with a refresher project."
                ),
            },
            {
                "title": "Phase 2: Strengthen what you partly know",
                "description": (
                    f"Go deeper on {_join(second_stage[:4], 4)} with hands-on exercises."
                    if second_stage
                    else f"Practise production tooling: {_join(recommended[:3])}."
                ),
            },
            {
                "title": "Phase 3: Build a proof-of-skill project",
                "description": f"Ship and document: {project}.",
            },
            {
                "title": "Phase 4: Certify and get interview-ready",
                "description": (
                    f"Validate with {_join(career['certifications'], 2)}, then drill role-specific interview problems "
                    f"for {career['related_jobs'][0]} roles."
                ),
            },
        ]

        results.append(
            {
                "title": career["title"],
                "category": career.get("category", "Software & Web"),
                "salary_range": career.get("salary_range", "Competitive Market Rate"),
                "market_demand": career.get("market_demand", "🔥 High"),
                "demand": career.get("market_demand", "🔥 High"),
                "difficulty_level": career.get("difficulty_level", "Intermediate"),
                "description": career.get("description", ""),
                "score": score,
                "match_percentage": _pct(score),
                "readiness": readiness,
                "confidence": confidence_label,
                "required_coverage": _pct(required_coverage),
                "estimated_weeks_to_ready": weeks_to_ready,
                "score_breakdown": breakdown,
                "not_scored": skipped,
                "matching_skills": matched_all[:12],
                "partial_skills": partial_all[:8],
                "resume_matching_skills": resume_matches,
                "required_skills": required,
                "recommended_skills": recommended,
                "missing_skills": req_missing,
                "missing_recommended_skills": rec_missing,
                "explanation": " ".join(explanation_parts),
                "suggested_projects": [project] + [p for p in career["projects"] if p != project],
                "learning_resources": [
                    "Official documentation and interactive tutorials",
                    "Guided capstone projects and open-source contributions",
                    "Industry case studies and peer code reviews",
                ],
                "recommended_certifications": career["certifications"],
                "related_jobs": career["related_jobs"],
                "next_steps": [
                    f"Learn {_join(first_stage or required[:2], 3)}",
                    f"Build: {project}",
                    f"Target openings for {career['related_jobs'][0]}",
                ],
                "career_roadmap": steps,
                "roadmap_phases": phases,
                "_confidence_value": confidence_value,
            }
        )

    results.sort(key=lambda r: (-r["score"], -r["required_coverage"], r["title"]))
    for rank, item in enumerate(results, start=1):
        item["rank"] = rank
        item.pop("_confidence_value", None)
    return results


def build_insights(profile_dict: dict, recommendations: list[dict], top_n: int = 5) -> dict:
    """Cross-career view: which single skills unlock the most of the user's best matches?"""
    profile = ProfileView(profile_dict)
    value, label = profile.confidence()
    aggregate: dict[str, dict[str, Any]] = {}
    for rec in recommendations[:top_n]:
        for position, skill in enumerate(rec["missing_skills"]):
            entry = aggregate.setdefault(_key(skill), {"skill": skill, "unlocks": [], "impact": 0.0})
            entry["unlocks"].append(rec["title"])
            entry["impact"] += rec["score"] / (1 + 0.15 * position)
    ranked = sorted(aggregate.values(), key=lambda e: (-len(e["unlocks"]), -e["impact"], e["skill"]))
    best = recommendations[0] if recommendations else None
    return {
        "best_fit": best["title"] if best else None,
        "best_fit_score": best["match_percentage"] if best else None,
        "top_skills_to_learn": [
            {"skill": e["skill"], "unlocks": e["unlocks"], "impact": round(e["impact"], 2)} for e in ranked[:6]
        ],
        "profile_strength": {"score": _pct(value), "label": label, "tips": profile.tips()},
    }


# --------------------------------------------------------------------------- #
# Jobs
# --------------------------------------------------------------------------- #
def find_career_for_title(title: str, catalog: list[dict] | None = None) -> dict | None:
    """Closest catalog career for a free-text job title, or None if nothing is close."""
    catalog = catalog or CAREER_CATALOG
    target = _phrase(title)
    if not target:
        return None
    target_tokens = _tokens(title)
    best, best_score = None, 0.0
    for career in catalog:
        names = [career["title"], *career.get("related_jobs", [])]
        if any(_phrase(n) == target for n in names):
            return career
        tokens = _tokens(career["title"])
        for name in names[1:]:
            tokens |= _tokens(name) if _phrase(name) in target or target in _phrase(name) else set()
        if not tokens or not target_tokens:
            continue
        overlap = sum(_token_weight(t) for t in tokens & target_tokens)
        union = sum(_token_weight(t) for t in tokens | target_tokens)
        score = overlap / union if union else 0.0
        if score > best_score:
            best, best_score = career, score
    return best if best_score >= 0.4 else None


_EXP_RANGE = re.compile(r"(\d+)\s*(?:-|to|–)\s*(\d+)")
_EXP_MIN = re.compile(r"(\d+)\s*\+")


def _parse_experience_range(text: str | None) -> tuple[float, float | None] | None:
    t = (text or "").lower()
    if not t.strip():
        return None
    if any(w in t for w in ("fresher", "entry", "graduate", "intern")):
        return (0.0, 1.0)
    match = _EXP_RANGE.search(t)
    if match:
        return (float(match.group(1)), float(match.group(2)))
    match = _EXP_MIN.search(t)
    if match:
        return (float(match.group(1)), None)
    single = re.search(r"(\d+)", t)
    if single:
        return (float(single.group(1)), float(single.group(1)) + 1)
    return None


def _experience_fit(years: float, span: tuple[float, float | None] | None) -> tuple[float | None, str]:
    if span is None:
        return None, ""
    low, high = span
    label = f"{int(low)}-{int(high)} years" if high is not None else f"{int(low)}+ years"
    if years < low:
        gap = low - years
        return max(0.25, 1.0 - 0.3 * gap), f"Asks for {label}; you have about {years:g} — a stretch of {gap:g} year(s)"
    if high is not None and years > high + 2:
        return 0.8, f"Targets {label}; you're more senior, which is fine but may be under-leveled"
    return 1.0, f"Your experience fits the {label} range"


def _preference_fit(profile: ProfileView, job: dict) -> tuple[float | None, str]:
    parts: list[float] = []
    notes: list[str] = []
    job_mode = str(job.get("work_mode") or "").strip().lower()
    job_location = str(job.get("location") or "").strip().lower()
    if profile.work_mode and job_mode:
        if profile.work_mode in job_mode or job_mode in profile.work_mode:
            parts.append(1.0)
            notes.append(f"matches your preferred {job.get('work_mode')} work mode")
        else:
            parts.append(0.3)
    if profile.preferred_location:
        if "remote" in job_mode or "remote" in job_location or profile.preferred_location in job_location:
            parts.append(1.0)
            notes.append("fits your preferred location")
        else:
            parts.append(0.3)
    if not parts:
        return None, ""
    note = ("It " + " and ".join(notes)) if notes else ""
    return sum(parts) / len(parts), note


def score_job(
    job: dict,
    profile: ProfileView,
    career_scores: dict[str, float] | None = None,
    catalog: list[dict] | None = None,
) -> dict:
    """Score one job posting against a profile. ``job`` needs title/required_skills; rest optional."""
    catalog = catalog or CAREER_CATALOG
    idf = _idf_table(catalog)
    total = len(catalog)
    required = split_skill_list(job.get("required_skills"))
    preferred = [
        s for s in extract_skills_from_text(job.get("preferred_qualifications") or "")
        if _key(s) not in {_key(r) for r in required}
    ]
    matched, partial, missing = _classify(required, profile.credits, idf, total)
    pref_matched, _, pref_missing = _classify(preferred, profile.credits, idf, total)

    required_coverage = _weighted_coverage(required, profile.credits, idf, total) if required else 0.0
    preferred_coverage = _weighted_coverage(preferred, profile.credits, idf, total) if preferred else None

    career = find_career_for_title(job.get("title", ""), catalog)
    goal_alignment = interest_alignment(
        profile.interest_text, [job.get("title", "")], job.get("title", ""), " ".join(required)
    )
    role_parts = [v for v in (goal_alignment, (career_scores or {}).get(career["title"]) if career else None) if v is not None]
    role_score = max(role_parts) if role_parts else None

    exp_score, exp_note = _experience_fit(profile.years, _parse_experience_range(job.get("experience")))
    pref_score, pref_note = _preference_fit(profile, job)
    components = {
        "skills": required_coverage if required else None,
        "preferred": preferred_coverage,
        "role": role_score,
        "experience": exp_score,
        "preferences": pref_score,
    }
    raw, breakdown, skipped = _combine(components, JOB_WEIGHTS)
    score = round(_clip(raw, 0.02, 0.98), 2)

    resume_matched = [s for s in required if _key(s) in profile.resume_keys]
    reasons = []
    if required:
        reasons.append(f"Covers {len(matched)} of {len(required)} required skills ({_pct(required_coverage)}% weighted)")
    for item in partial[:2]:
        reasons.append(f"{item['skill']} likely covered via your {item['via']} skills")
    if missing:
        reasons.append(f"Skill gaps: {_join(missing, 3)}")
    if goal_alignment is not None and goal_alignment >= 0.8:
        reasons.append("Matches your stated career goal")
    if exp_note:
        reasons.append(exp_note)
    if pref_note:
        reasons.append(pref_note)

    return {
        "match_score": score,
        "match_percentage": _pct(score),
        "readiness": _readiness(required_coverage),
        "required_skills": required,
        "preferred_skills": preferred,
        "resume_matched_skills": resume_matched,
        "all_matched_skills": matched,
        "partial_skills": partial,
        "missing_skills": missing,
        "missing_preferred_skills": pref_missing,
        "preferred_matched_skills": pref_matched,
        "score_breakdown": breakdown,
        "not_scored": skipped,
        "reasons": reasons,
        "matched_career": career["title"] if career else None,
    }


def build_job_skill_roadmap(
    job_title: str,
    required_skills: str = "",
    user_skills: list[str] | None = None,
    profile: ProfileView | None = None,
) -> dict:
    """Personalised plan to qualify for a job/role. Pass ``profile`` for proficiency-aware gaps."""
    profile = profile or ProfileView({"skills": user_skills or []})
    idf = _idf_table(CAREER_CATALOG)
    total = len(CAREER_CATALOG)
    job_skills = split_skill_list(required_skills)
    matched, partial, missing = _classify(job_skills, profile.credits, idf, total)
    coverage = _weighted_coverage(job_skills, profile.credits, idf, total) if job_skills else 0.0

    career = find_career_for_title(job_title)
    projects = career["projects"] if career else [f"{job_title} capstone case study"]
    certifications = career["certifications"] if career else ["Professional industry certification for this field"]
    project = _pick_project(career, missing) if career else projects[0]

    weeks_core = max(1, math.ceil(len(missing) * 1.5))
    weeks_partial = max(1, math.ceil(len(partial) * 1.0))
    weeks_practice = 3 if missing else 2
    partial_names = [p["skill"] for p in partial]
    phases = [
        {
            "step": 1,
            "title": "Master missing prerequisites",
            "description": (
                f"Learn {_join(missing, 5)} first — ordered by how distinctive they are for this role."
                if missing
                else f"No hard gaps. Refresh {_join(matched[:3] or job_skills[:3])} to interview level."
            ),
            "estimated_timeline": f"{weeks_core}-{weeks_core + 2} weeks" if missing else "1 week",
        },
        {
            "step": 2,
            "title": "Solidify what you partly know",
            "description": (
                f"You likely have a base in {_join(partial_names, 4)}; confirm it with exercises."
                if partial_names
                else f"Build practical exercises combining {_join(job_skills[:4])} into reproducible workflows."
            ),
            "estimated_timeline": f"{weeks_partial}-{weeks_partial + 1} weeks" if partial_names else f"{weeks_practice}-{weeks_practice + 2} weeks",
        },
        {
            "step": 3,
            "title": "Build a job-winning portfolio project",
            "description": f"Ship a showcase project that exercises your new skills: {project}.",
            "estimated_timeline": "2-3 weeks",
        },
        {
            "step": 4,
            "title": "Certify and prepare for interviews",
            "description": f"Consider {_join(certifications, 2)} and practise role-specific technical problems.",
            "estimated_timeline": "1-2 weeks",
        },
    ]
    estimated_weeks = 0 if coverage >= 0.98 else weeks_core + weeks_partial + weeks_practice + 3 if missing or partial else 4
    return {
        "job_title": job_title,
        "fit_score": round(coverage, 2),
        "matched_skills": matched,
        "partial_skills": partial,
        "missing_skills": missing,
        "all_required_skills": job_skills,
        "suggested_projects": projects,
        "suggested_certifications": certifications,
        "estimated_weeks": estimated_weeks,
        "roadmap": phases,
    }
