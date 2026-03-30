"""
Seed — Pre-populate database with sample jobs
Runs once on first app start if jobs table is empty
"""

from models import Job
from app import db


SAMPLE_JOBS = [
    {
        "title": "Data Analyst",
        "company": "TCS",
        "location": "Hyderabad",
        "job_type": "Full Time",
        "salary": "₹4–7 LPA",
        "description": "Analyze large datasets to drive business insights. Work with SQL, Python and Excel daily.",
        "required_skills": ["SQL", "Python", "Excel", "Data Analysis", "Communication"],
        "experience_req": 0
    },
    {
        "title": "Business Analyst",
        "company": "Infosys",
        "location": "Bengaluru",
        "job_type": "Full Time",
        "salary": "₹5–9 LPA",
        "description": "Bridge business and tech teams. Analyze requirements, create reports, manage stakeholders.",
        "required_skills": ["SQL", "Excel", "Data Analysis", "Communication", "Problem Solving"],
        "experience_req": 0
    },
    {
        "title": "Junior Data Analyst",
        "company": "Wipro",
        "location": "Remote",
        "job_type": "Contract",
        "salary": "₹3–6 LPA",
        "description": "Work with data pipelines, create dashboards, and support senior analysts.",
        "required_skills": ["Python", "MySQL", "Excel", "Reporting"],
        "experience_req": 0
    },
    {
        "title": "BI Analyst",
        "company": "Tech Mahindra",
        "location": "Hyderabad",
        "job_type": "Full Time",
        "salary": "₹5–10 LPA",
        "description": "Build Power BI dashboards and reports for business stakeholders.",
        "required_skills": ["Power BI", "SQL", "DAX", "Data Visualization"],
        "experience_req": 1
    },
    {
        "title": "SQL Developer",
        "company": "HCL",
        "location": "Chennai",
        "job_type": "Full Time",
        "salary": "₹4–8 LPA",
        "description": "Design and optimize SQL queries, stored procedures, and database schemas.",
        "required_skills": ["SQL", "MySQL", "PostgreSQL", "Python"],
        "experience_req": 1
    },
    {
        "title": "Data Analyst Intern",
        "company": "Fintech Startup",
        "location": "Remote",
        "job_type": "Internship",
        "salary": "₹8,000–15,000/month",
        "description": "3-month paid internship. Work on real data projects using Python and SQL.",
        "required_skills": ["Python", "SQL", "Excel", "Data Analysis"],
        "experience_req": 0
    },
    {
        "title": "Analyst Trainee",
        "company": "Accenture",
        "location": "Hyderabad",
        "job_type": "Full Time",
        "salary": "₹3.5–5 LPA",
        "description": "Entry-level analyst role. Training provided. Open to fresh graduates.",
        "required_skills": ["Excel", "Data Analysis", "Communication", "MS Office"],
        "experience_req": 0
    },
    {
        "title": "Data Operations Analyst",
        "company": "Cognizant",
        "location": "Pune",
        "job_type": "Full Time",
        "salary": "₹3–5 LPA",
        "description": "Handle data entry, data validation, MIS reporting and process optimization.",
        "required_skills": ["Excel", "SQL", "Communication"],
        "experience_req": 0
    },
]


def seed_jobs():
    """Only seeds if jobs table is empty."""
    if Job.query.count() == 0:
        for job_data in SAMPLE_JOBS:
            job = Job(**job_data)
            db.session.add(job)
        db.session.commit()
        print(f"✅ Seeded {len(SAMPLE_JOBS)} sample jobs")
    else:
        print("ℹ️  Jobs already seeded, skipping.")
