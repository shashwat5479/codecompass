"""Skill intelligence: normalisation, aliases, implied/related skills, text extraction.

The recommendation engine never compares raw strings. Every skill is first reduced to a
canonical key (``normalize_skill_name``) and then looked up in a small knowledge graph:

* IMPLIED  - knowing X is strong evidence for Y (React -> JavaScript, PostgreSQL -> SQL)
* RELATED  - X is a transferable neighbour of Y (PyTorch <-> TensorFlow, Power BI <-> Tableau)

This gives partial credit instead of the all-or-nothing matching of a plain keyword filter.
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Iterable

from app.catalog import CAREER_CATALOG

SYNONYM_MAP = {
    "reactjs": "react",
    "react.js": "react",
    "nodejs": "node.js",
    "node": "node.js",
    "expressjs": "express",
    "express.js": "express",
    "nextjs": "next.js",
    "next.js": "next.js",
    "vuejs": "vue",
    "vue.js": "vue",
    "angularjs": "angular",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "mongo": "mongodb",
    "mongodb": "mongodb",
    "k8s": "kubernetes",
    "kubernetes": "kubernetes",
    "ml": "machine learning",
    "machine learning": "machine learning",
    "ai": "artificial intelligence",
    "artificial intelligence": "artificial intelligence",
    "dl": "deep learning",
    "deep learning": "deep learning",
    "nlp": "nlp",
    "natural language processing": "nlp",
    "cv": "computer vision",
    "computer vision": "computer vision",
    "dsa": "data structures",
    "data structures": "data structures",
    "algorithms": "algorithms",
    "restful api": "rest apis",
    "restful apis": "rest apis",
    "rest api": "rest apis",
    "rest apis": "rest apis",
    "apis": "rest apis",
    "ci/cd": "ci/cd",
    "cicd": "ci/cd",
    "ci-cd": "ci/cd",
    "continuous integration": "ci/cd",
    "powerbi": "power bi",
    "power bi": "power bi",
    "tailwind": "tailwind css",
    "tailwindcss": "tailwind css",
    "tailwind css": "tailwind css",
    "js": "javascript",
    "javascript": "javascript",
    "ts": "typescript",
    "typescript": "typescript",
    "py": "python",
    "python": "python",
    "aws cloud": "aws",
    "amazon web services": "aws",
    "azure cloud": "azure",
    "microsoft azure": "azure",
    "gcp": "google cloud",
    "google cloud platform": "google cloud",
    "docker containers": "docker",
    "ui/ux": "ui/ux",
    "ui ux": "ui/ux",
    "ui/ux design": "ui/ux",
    "user research": "user research",
    "wireframing": "wireframing",
    "prototyping": "prototyping",
    "figma": "figma",
    "sql": "sql",
    "structured query language": "sql",
    "test automation": "test automation",
    "qa": "quality assurance",
    "quality assurance": "quality assurance",
    "cyber security": "security",
    "cybersecurity": "security",
    "network security": "network security",
    "networking": "networking",
}

SYNONYM_MAP.update({
    "html5": "html",
    "css3": "css",
    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "scikitlearn": "scikit-learn",
    "ms excel": "excel",
    "microsoft excel": "excel",
    "data viz": "data visualization",
    "data visualisation": "data visualization",
    "object oriented programming": "oop",
    "object-oriented programming": "oop",
    "mlops": "mlops",
    "ml ops": "mlops",
    "github action": "github actions",
    "gh actions": "github actions",
    "c plus plus": "c++",
    "cpp": "c++",
    "restful": "rest apis",
    "graphql api": "graphql",
    "unit testing": "testing",
    "software testing": "testing",
    "manual testing": "testing",
    "ux": "ui/ux",
    "ui": "ui/ux",
    "product mgmt": "product management",
    "a/b test": "a/b testing",
    "ab testing": "a/b testing",
    "bash scripting": "bash",
    "shell scripting": "bash",
    "react native app": "react native",
    "huggingface": "hugging face",
    "data analytics": "data analysis",
    "data analysis": "data analysis",
    "iam": "iam security",
    "web development": "html",
})


# --------------------------------------------------------------------------- #
# Knowledge graph
# --------------------------------------------------------------------------- #
# source skill -> {implied skill: credit 0..1}.  Directional.
IMPLIED: dict[str, dict[str, float]] = {
    "react": {"javascript": 0.8, "html": 0.5, "css": 0.4},
    "next.js": {"react": 0.9, "javascript": 0.8, "html": 0.4, "css": 0.4},
    "redux": {"react": 0.6, "javascript": 0.6},
    "typescript": {"javascript": 0.9},
    "vue": {"javascript": 0.8, "html": 0.5, "css": 0.4},
    "angular": {"javascript": 0.7, "typescript": 0.7, "html": 0.5, "css": 0.4},
    "tailwind css": {"css": 0.8, "html": 0.4},
    "vite": {"javascript": 0.4},
    "node.js": {"javascript": 0.85},
    "express": {"node.js": 0.8, "javascript": 0.7, "rest apis": 0.5},
    "fastapi": {"python": 0.9, "rest apis": 0.7},
    "django": {"python": 0.9, "rest apis": 0.4, "sql": 0.3, "databases": 0.4},
    "flask": {"python": 0.9, "rest apis": 0.5},
    "postgresql": {"sql": 0.9, "databases": 0.9},
    "mysql": {"sql": 0.9, "databases": 0.9},
    "mongodb": {"databases": 0.8},
    "redis": {"databases": 0.4},
    "sql": {"databases": 0.7},
    "pandas": {"python": 0.9, "data cleaning": 0.5, "numpy": 0.4, "data analysis": 0.5},
    "numpy": {"python": 0.8},
    "scikit-learn": {"python": 0.9, "machine learning": 0.8},
    "tensorflow": {"python": 0.8, "deep learning": 0.8, "machine learning": 0.7},
    "pytorch": {"python": 0.8, "deep learning": 0.8, "machine learning": 0.7},
    "hugging face": {"python": 0.6, "deep learning": 0.5, "nlp": 0.6},
    "deep learning": {"machine learning": 0.9},
    "nlp": {"machine learning": 0.5},
    "computer vision": {"deep learning": 0.6, "machine learning": 0.5},
    "kubernetes": {"docker": 0.7, "linux": 0.3},
    "docker": {"linux": 0.3},
    "terraform": {"cloud": 0.6},
    "aws": {"cloud": 0.9},
    "azure": {"cloud": 0.9},
    "google cloud": {"cloud": 0.9},
    "github actions": {"ci/cd": 0.9, "git": 0.7},
    "jenkins": {"ci/cd": 0.9},
    "gitlab ci": {"ci/cd": 0.9, "git": 0.6},
    "ansible": {"linux": 0.3},
    "git": {},
    "figma": {"ui/ux": 0.5, "prototyping": 0.7, "wireframing": 0.6},
    "ui/ux": {"wireframing": 0.5, "prototyping": 0.4},
    "power bi": {"data visualization": 0.9, "business intelligence": 0.8},
    "tableau": {"data visualization": 0.9, "business intelligence": 0.8},
    "excel": {"data analysis": 0.4},
    "data analysis": {"statistics": 0.3},
    "selenium": {"test automation": 0.9, "quality assurance": 0.5, "testing": 0.7},
    "cypress": {"test automation": 0.9, "javascript": 0.5, "testing": 0.7},
    "playwright": {"test automation": 0.9, "testing": 0.7},
    "pytest": {"python": 0.7, "test automation": 0.6, "testing": 0.7},
    "postman": {"rest apis": 0.7, "test automation": 0.3, "testing": 0.4},
    "jest": {"javascript": 0.6, "testing": 0.7},
    "test automation": {"testing": 0.8},
    "java": {"oop": 0.7},
    "c++": {"oop": 0.6, "data structures": 0.3},
    "python": {"oop": 0.3},
    "flutter": {"dart": 0.9, "mobile development": 0.9},
    "dart": {"mobile development": 0.3},
    "react native": {"react": 0.7, "javascript": 0.8, "mobile development": 0.9},
    "kotlin": {"mobile development": 0.6},
    "swift": {"mobile development": 0.6},
    "firebase": {"databases": 0.3},
    "wireshark": {"networking": 0.7, "network security": 0.5},
    "nmap": {"networking": 0.6, "security": 0.6, "vulnerability assessment": 0.6},
    "splunk": {"siem": 0.8},
    "siem": {"security": 0.6},
    "ethical hacking": {"security": 0.9, "vulnerability assessment": 0.6, "networking": 0.4},
    "incident response": {"security": 0.5},
    "network security": {"networking": 0.8, "security": 0.8},
    "firewalls": {"networking": 0.5, "security": 0.5},
    "cryptography": {"security": 0.6},
    "agile": {"scrum": 0.6},
    "scrum": {"agile": 0.9},
    "jira": {"agile": 0.4},
    "product strategy": {"product management": 0.6, "roadmapping": 0.4},
    "roadmapping": {"product management": 0.5},
    "a/b testing": {"statistics": 0.4, "data analysis": 0.4},
    "statistics": {},
    "algorithms": {"data structures": 0.5},
    "data structures": {"algorithms": 0.5},
    "system design": {"microservices": 0.4},
    "microservices": {"system design": 0.4, "rest apis": 0.4},
    "iam security": {"security": 0.5, "cloud": 0.4},
}

# Symmetric transferable-skill pairs.  (a, b, credit)
_RELATED_PAIRS: list[tuple[str, str, float]] = [
    ("react", "vue", 0.55), ("react", "angular", 0.45), ("vue", "angular", 0.5),
    ("pytorch", "tensorflow", 0.75), ("postgresql", "mysql", 0.8),
    ("postgresql", "mongodb", 0.3), ("mysql", "mongodb", 0.3),
    ("aws", "azure", 0.65), ("aws", "google cloud", 0.65), ("azure", "google cloud", 0.65),
    ("power bi", "tableau", 0.75), ("excel", "power bi", 0.35), ("excel", "tableau", 0.3),
    ("selenium", "playwright", 0.7), ("selenium", "cypress", 0.65), ("cypress", "playwright", 0.8),
    ("flutter", "react native", 0.5), ("kotlin", "swift", 0.4),
    ("java", "c++", 0.4), ("python", "java", 0.3), ("javascript", "python", 0.2),
    ("django", "fastapi", 0.6), ("django", "flask", 0.7), ("flask", "fastapi", 0.7),
    ("docker", "kubernetes", 0.5), ("terraform", "ansible", 0.5),
    ("jenkins", "github actions", 0.75), ("gitlab ci", "github actions", 0.8),
    ("prometheus", "grafana", 0.6), ("splunk", "siem", 0.7),
    ("nlp", "deep learning", 0.4), ("computer vision", "deep learning", 0.5),
    ("express", "fastapi", 0.35), ("node.js", "python", 0.2),
    ("statistics", "machine learning", 0.4), ("statistics", "data analysis", 0.5),
    ("pandas", "excel", 0.3), ("figma", "ui/ux", 0.5),
    ("scrum", "jira", 0.4), ("postman", "pytest", 0.3),
]

RELATED: dict[str, dict[str, float]] = {}
for _a, _b, _w in _RELATED_PAIRS:
    RELATED.setdefault(_a, {})[_b] = max(_w, RELATED.get(_a, {}).get(_b, 0.0))
    RELATED.setdefault(_b, {})[_a] = max(_w, RELATED.get(_b, {}).get(_a, 0.0))


# --------------------------------------------------------------------------- #
# Normalisation
# --------------------------------------------------------------------------- #
_TRAILING_NOISE = re.compile(r"[\s,;:()\[\]]+$")
_LEADING_NOISE = re.compile(r"^[\s,;:()\[\]\-\u2022*]+")


def normalize_skill_name(name: str) -> str:
    """Return the canonical lower-case key for a skill (``"ReactJS "`` -> ``"react"``)."""
    cleaned = " ".join(str(name or "").strip().lower().split())
    cleaned = _LEADING_NOISE.sub("", cleaned)
    cleaned = _TRAILING_NOISE.sub("", cleaned)
    if cleaned in SYNONYM_MAP:
        return SYNONYM_MAP[cleaned]
    # "node js" / "next js" / "react js" style spellings
    squashed = re.sub(r"\s*\.?\s*js$", ".js", cleaned) if cleaned.endswith("js") else cleaned
    return SYNONYM_MAP.get(squashed, squashed)


def _build_display_names() -> dict[str, str]:
    names: dict[str, str] = {}
    for career in CAREER_CATALOG:
        for skill in career["required_skills"] + career["recommended_skills"]:
            names.setdefault(normalize_skill_name(skill), skill)
    for skill in (
        "Excel", "Power BI", "Tableau", "Communication", "Data Analysis", "HTML", "CSS",
        "JavaScript", "TypeScript", "React", "Git", "AWS", "Azure", "Docker", "Kubernetes",
        "Leadership", "Figma", "UI/UX", "User Research", "Wireframing", "Product Management",
        "Agile", "Scrum", "Flutter", "React Native", "Swift", "Kotlin", "Selenium", "Cypress",
        "Playwright", "Postman", "PostgreSQL", "MongoDB", "Redis", "TensorFlow", "PyTorch",
        "Linux", "MySQL", "Flask", "Django", "FastAPI", "Vue", "Angular", "GraphQL", "Java",
        "C++", "Python", "SQL", "Pandas", "NumPy", "Jenkins", "GitLab CI", "Ansible",
    ):
        names.setdefault(normalize_skill_name(skill), skill)
    return names


DISPLAY_NAMES: dict[str, str] = _build_display_names()


def display_name(skill: str) -> str:
    return DISPLAY_NAMES.get(normalize_skill_name(skill), skill.strip())


def split_skill_list(raw: str | Iterable[str] | None) -> list[str]:
    """Split a comma / semicolon / newline separated skills string; de-duplicates."""
    if raw is None:
        return []
    items = re.split(r"[,;\n|]", raw) if isinstance(raw, str) else list(raw)
    seen: dict[str, str] = {}
    for item in items:
        cleaned = str(item).strip()
        if cleaned:
            seen.setdefault(normalize_skill_name(cleaned), cleaned)
    return list(seen.values())


# --------------------------------------------------------------------------- #
# Extraction from free text (resumes, project descriptions, job text)
# --------------------------------------------------------------------------- #
# Aliases short enough to cause false positives in running prose are never matched.
_UNSAFE_ALIASES = {"ai", "ml", "dl", "cv", "ui", "ux", "js", "ts", "py", "qa", "iam", "node", "tf"}


@lru_cache(maxsize=1)
def _extraction_patterns() -> tuple[tuple[str, re.Pattern[str]], ...]:
    terms: dict[str, set[str]] = {}
    for key, shown in DISPLAY_NAMES.items():
        terms.setdefault(key, set()).add(shown.lower())
    for alias, canonical in SYNONYM_MAP.items():
        if alias in _UNSAFE_ALIASES or len(alias) < 3 or canonical not in DISPLAY_NAMES:
            continue
        terms.setdefault(canonical, set()).add(alias)
    patterns = []
    for key, variants in terms.items():
        alternation = "|".join(re.escape(v) for v in sorted(variants, key=len, reverse=True))
        patterns.append((key, re.compile(rf"(?<![\w.+#]){'(?:' + alternation + ')'}(?![\w+#])", re.IGNORECASE)))
    return tuple(patterns)


def extract_skills_from_text(text: str) -> list[str]:
    """Find every known skill mentioned in ``text``; returns display names, sorted."""
    if not text:
        return []
    found = [DISPLAY_NAMES[key] for key, pattern in _extraction_patterns() if pattern.search(text)]
    return sorted(set(found), key=str.casefold)


# --------------------------------------------------------------------------- #
# Skill expansion with partial credit
# --------------------------------------------------------------------------- #
class Credit:
    """How well a user covers one target skill."""

    __slots__ = ("value", "kind", "via")

    def __init__(self, value: float = 0.0, kind: str = "none", via: str | None = None):
        self.value = value
        self.kind = kind  # direct | implied | related | none
        self.via = via

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Credit({self.value:.2f}, {self.kind}, via={self.via})"


def expand_skills(skill_levels: dict[str, float]) -> dict[str, Credit]:
    """Turn ``{normalized skill: strength 0..1}`` into credits for every reachable skill.

    Direct skills keep their own strength. Implied/related skills inherit
    ``strength * edge_weight`` and never beat a direct skill the user actually listed.
    """
    expanded: dict[str, Credit] = {}
    for skill, strength in skill_levels.items():
        expanded[skill] = Credit(min(1.0, strength), "direct", None)
    for skill, strength in skill_levels.items():
        for kind, graph in (("implied", IMPLIED), ("related", RELATED)):
            for target, weight in graph.get(skill, {}).items():
                value = min(1.0, strength) * weight
                current = expanded.get(target)
                if current is None or (current.kind != "direct" and value > current.value):
                    expanded[target] = Credit(value, kind, DISPLAY_NAMES.get(skill, skill))
    return expanded
