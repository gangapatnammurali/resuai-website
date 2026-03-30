"""
ResuAI — AI Resume Parser
Uses: pdfplumber (PDF), python-docx (DOCX), spaCy NLP, skill matching
"""

import re
import os
import json
import pdfplumber
import docx
import spacy

# Load spaCy English model (run: python -m spacy download en_core_web_sm)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("⚠️  spaCy model not found. Run: python -m spacy download en_core_web_sm")
    nlp = None


# ─── Master Skills Database ──────────────────────────────────────────────────
SKILLS_DB = {
    # Data & Analytics
    "sql", "mysql", "postgresql", "sqlite", "nosql", "mongodb",
    "python", "pandas", "numpy", "matplotlib", "seaborn", "scipy",
    "power bi", "tableau", "looker", "qlik", "excel", "google sheets",
    "data analysis", "data visualization", "data cleaning", "etl",
    "machine learning", "deep learning", "scikit-learn", "tensorflow", "keras",
    "r", "sas", "spss", "statistics", "regression", "classification",
    "nlp", "natural language processing", "computer vision",
    "big data", "hadoop", "spark", "hive", "kafka",
    "aws", "azure", "gcp", "cloud computing",
    "airflow", "dbt", "snowflake", "databricks",

    # Software Development
    "java", "kotlin", "android", "android studio", "xml",
    "javascript", "typescript", "react", "angular", "vue", "node.js",
    "html", "css", "flask", "django", "fastapi", "spring boot",
    "c", "c++", "c#", ".net", "php", "ruby",
    "git", "github", "docker", "kubernetes", "ci/cd", "linux",
    "restful api", "graphql", "microservices",

    # Business & Soft Skills
    "communication", "leadership", "problem solving", "teamwork",
    "project management", "agile", "scrum", "jira", "business analysis",
    "ms office", "powerpoint", "word",
}

# Skills that Data Analyst roles specifically need
DA_REQUIRED_SKILLS = {
    "sql", "python", "excel", "data analysis", "power bi", "tableau",
    "data visualization", "statistics", "communication", "problem solving"
}


# ─── TEXT EXTRACTION ──────────────────────────────────────────────────────────

def extract_text(filepath: str) -> str:
    """Extract raw text from PDF, DOCX, or TXT file."""
    ext = filepath.rsplit(".", 1)[-1].lower()

    if ext == "pdf":
        return _extract_pdf(filepath)
    elif ext in ("doc", "docx"):
        return _extract_docx(filepath)
    elif ext == "txt":
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file type: .{ext}")


def _extract_pdf(filepath: str) -> str:
    text = ""
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()


def _extract_docx(filepath: str) -> str:
    doc = docx.Document(filepath)
    return "\n".join(para.text for para in doc.paragraphs).strip()


# ─── SKILL EXTRACTION ─────────────────────────────────────────────────────────

def extract_skills(text: str) -> list:
    """Find all matching skills in resume text."""
    text_lower = text.lower()
    found = set()

    for skill in SKILLS_DB:
        # Match whole words/phrases
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.add(skill.title())

    return sorted(found)


# ─── EDUCATION EXTRACTION ─────────────────────────────────────────────────────

DEGREE_PATTERNS = [
    r"(b\.?tech|bachelor of technology)",
    r"(b\.?e|bachelor of engineering)",
    r"(b\.?sc|bachelor of science)",
    r"(m\.?tech|master of technology)",
    r"(m\.?sc|master of science)",
    r"(mba|master of business)",
    r"(bca|bachelor of computer applications)",
    r"(mca|master of computer applications)",
    r"(ph\.?d|doctorate)",
    r"(12th|intermediate|hsc)",
    r"(10th|ssc|matriculation)",
]

def extract_education(text: str) -> dict:
    """Extract degree and university info from resume."""
    text_lower = text.lower()
    degree_found = None

    for pattern in DEGREE_PATTERNS:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            degree_found = match.group(0).upper()
            break

    # Try to find university name using spaCy ORG entities
    university = None
    if nlp:
        doc = nlp(text[:2000])  # Only first 2000 chars for speed
        for ent in doc.ents:
            if ent.label_ == "ORG" and any(
                kw in ent.text.lower()
                for kw in ["university", "college", "institute", "iit", "nit", "bits"]
            ):
                university = ent.text
                break

    # Try to find graduation year
    year_match = re.search(r"(20[1-2][0-9]|19[9-9][0-9])", text)
    year = year_match.group(0) if year_match else None

    return {
        "degree":     degree_found or "Not found",
        "university": university or "Not detected",
        "year":       year or "Not found"
    }


# ─── EXPERIENCE EXTRACTION ────────────────────────────────────────────────────

def extract_experience(text: str) -> float:
    """Estimate years of experience from resume text."""
    text_lower = text.lower()

    # Look for "X years of experience" patterns
    patterns = [
        r"(\d+\.?\d*)\s*\+?\s*years?\s*(of\s*)?(experience|exp)",
        r"experience[:\s]+(\d+\.?\d*)\s*years?",
        r"(\d+\.?\d*)\s*years?\s*experience",
    ]
    for p in patterns:
        match = re.search(p, text_lower)
        if match:
            return float(match.group(1))

    # Check for fresher/entry-level keywords
    fresher_kw = ["fresher", "fresh graduate", "entry level", "0 years", "no experience"]
    if any(kw in text_lower for kw in fresher_kw):
        return 0.0

    # Count date ranges like "Jun 2022 – Present"
    ranges = re.findall(
        r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+20\d{2}",
        text_lower
    )
    if len(ranges) >= 2:
        return round(len(ranges) / 2 * 0.5, 1)  # Rough estimate

    return 0.0


# ─── CONTACT EXTRACTION ───────────────────────────────────────────────────────

def extract_contact(text: str) -> dict:
    email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    phone_match = re.search(r"(\+91[\s\-]?)?[6-9]\d{9}", text)

    return {
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0) if phone_match else None
    }


# ─── AI SCORE CALCULATION ─────────────────────────────────────────────────────

def calculate_ai_score(skills: list, education: dict, experience: float, text: str) -> dict:
    """
    Score the resume 0–100 based on:
    - Skills completeness    (40 pts)
    - Education              (20 pts)
    - Experience             (15 pts)
    - Resume structure       (15 pts)
    - Content quality        (10 pts)
    """
    score = 0
    tips = []
    skills_lower = {s.lower() for s in skills}

    # 1. Skills (40 pts)
    matched_da_skills = DA_REQUIRED_SKILLS & skills_lower
    skill_score = min(40, int((len(matched_da_skills) / len(DA_REQUIRED_SKILLS)) * 40))
    score += skill_score

    missing = sorted(DA_REQUIRED_SKILLS - skills_lower)
    if missing:
        tips.append(f"Add missing skills to resume: {', '.join(s.title() for s in missing[:4])}")

    # 2. Education (20 pts)
    edu_text = (education.get("degree") or "").lower()
    if any(d in edu_text for d in ["b.tech", "m.tech", "b.e", "m.sc", "mba", "bca", "mca"]):
        score += 20
    elif any(d in edu_text for d in ["b.sc", "12th"]):
        score += 12
    else:
        score += 5
        tips.append("Mention your degree clearly at the top of your resume")

    # 3. Experience (15 pts)
    if experience >= 3:
        score += 15
    elif experience >= 1:
        score += 10
    elif experience == 0:
        score += 5
        tips.append("Add internships, projects, or freelance work under Experience section")

    # 4. Resume structure (15 pts)
    text_lower = text.lower()
    sections = ["experience", "education", "skills", "projects", "objective"]
    found_sections = sum(1 for s in sections if s in text_lower)
    score += min(15, found_sections * 3)

    if "summary" not in text_lower and "objective" not in text_lower:
        tips.append("Add a Professional Summary (2–3 sentences) at the top of your resume")

    if "project" not in text_lower:
        tips.append("Add a Projects section to showcase your work — very important for freshers")

    # 5. Content quality (10 pts)
    word_count = len(text.split())
    if word_count >= 400:
        score += 10
    elif word_count >= 200:
        score += 6
        tips.append("Expand your resume — aim for 400+ words to fully describe your experience")
    else:
        score += 2
        tips.append("Resume is too short. Add more details about your projects and skills")

    # Add general tips
    if "github" not in text_lower and "portfolio" not in text_lower:
        tips.append("Add your GitHub profile or portfolio link — recruiters look for this")

    if "power bi" not in skills_lower and "tableau" not in skills_lower:
        tips.append("Learn Power BI (free) — required in 76% of Data Analyst job postings")

    return {
        "score": min(100, score),
        "tips":  tips[:6]  # Max 6 tips
    }


# ─── JOB MATCHING ─────────────────────────────────────────────────────────────

def match_score(resume_skills: list, job: object) -> int:
    """
    Calculate how well a resume matches a job posting.
    Returns match percentage 0–100.
    """
    if not job.required_skills:
        return 50

    resume_set = {s.lower() for s in resume_skills}
    job_set    = {s.lower() for s in job.required_skills}

    matched = resume_set & job_set
    if not job_set:
        return 50

    base = int((len(matched) / len(job_set)) * 85)

    # Bonus for experience
    bonus = 0
    if hasattr(job, "experience_req"):
        if job.experience_req == 0:
            bonus = 10  # Fresher roles give full bonus
        elif job.experience_req <= 1:
            bonus = 5

    return min(100, base + bonus)


# ─── MAIN PARSE FUNCTION ──────────────────────────────────────────────────────

def parse_resume(filepath: str) -> dict:
    """
    Full pipeline:
    1. Extract text
    2. Extract skills, education, experience, contact
    3. Calculate AI score
    Returns a dict ready to save to Resume model
    """
    raw_text   = extract_text(filepath)
    skills     = extract_skills(raw_text)
    education  = extract_education(raw_text)
    experience = extract_experience(raw_text)
    contact    = extract_contact(raw_text)
    scoring    = calculate_ai_score(skills, education, experience, raw_text)

    missing = [
        s.title() for s in DA_REQUIRED_SKILLS
        if s not in {sk.lower() for sk in skills}
    ]

    return {
        "raw_text":        raw_text,
        "skills":          skills,
        "education":       education,
        "experience_years":experience,
        "contact":         contact,
        "ai_score":        scoring["score"],
        "suggestions":     scoring["tips"],
        "missing_skills":  missing[:5]
    }
