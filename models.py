"""
Database Models — ResuAI
Tables: User, Resume, Job, Application
"""

from app import db
from datetime import datetime


class User(db.Model):
    __tablename__ = "users"

    id           = db.Column(db.Integer, primary_key=True)
    first_name   = db.Column(db.String(50), nullable=False)
    last_name    = db.Column(db.String(50), nullable=False)
    email        = db.Column(db.String(120), unique=True, nullable=False)
    phone        = db.Column(db.String(20))
    password     = db.Column(db.String(200), nullable=False)   # bcrypt hash
    role         = db.Column(db.String(20), default="jobseeker") # jobseeker | employer
    domain       = db.Column(db.String(100))
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    resumes      = db.relationship("Resume", backref="user", lazy=True, cascade="all, delete-orphan")
    applications = db.relationship("Application", backref="user", lazy=True)

    def to_dict(self):
        return {
            "id":         self.id,
            "first_name": self.first_name,
            "last_name":  self.last_name,
            "email":      self.email,
            "phone":      self.phone,
            "role":       self.role,
            "domain":     self.domain,
            "created_at": self.created_at.isoformat()
        }


class Resume(db.Model):
    __tablename__ = "resumes"

    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    filename        = db.Column(db.String(200))
    raw_text        = db.Column(db.Text)                    # extracted plain text
    skills          = db.Column(db.JSON, default=list)      # ["SQL", "Python", ...]
    education       = db.Column(db.JSON, default=dict)      # {degree, university, year}
    experience_years= db.Column(db.Float, default=0)
    ai_score        = db.Column(db.Integer, default=0)      # 0–100
    missing_skills  = db.Column(db.JSON, default=list)
    suggestions     = db.Column(db.JSON, default=list)
    uploaded_at     = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":               self.id,
            "filename":         self.filename,
            "skills":           self.skills or [],
            "education":        self.education or {},
            "experience_years": self.experience_years,
            "ai_score":         self.ai_score,
            "missing_skills":   self.missing_skills or [],
            "suggestions":      self.suggestions or [],
            "uploaded_at":      self.uploaded_at.isoformat()
        }


class Job(db.Model):
    __tablename__ = "jobs"

    id           = db.Column(db.Integer, primary_key=True)
    title        = db.Column(db.String(100), nullable=False)
    company      = db.Column(db.String(100), nullable=False)
    location     = db.Column(db.String(100))
    job_type     = db.Column(db.String(50))    # Full Time | Remote | Internship
    salary       = db.Column(db.String(60))
    description  = db.Column(db.Text)
    required_skills = db.Column(db.JSON, default=list)
    experience_req  = db.Column(db.Float, default=0)
    is_active    = db.Column(db.Boolean, default=True)
    posted_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    applications = db.relationship("Application", backref="job", lazy=True)

    def to_dict(self):
        return {
            "id":               self.id,
            "title":            self.title,
            "company":          self.company,
            "location":         self.location,
            "job_type":         self.job_type,
            "salary":           self.salary,
            "description":      self.description,
            "required_skills":  self.required_skills or [],
            "experience_req":   self.experience_req,
            "is_active":        self.is_active,
            "posted_at":        self.posted_at.isoformat()
        }


class Application(db.Model):
    __tablename__ = "applications"

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    job_id       = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    resume_id    = db.Column(db.Integer, db.ForeignKey("resumes.id"))
    match_score  = db.Column(db.Integer, default=0)
    status       = db.Column(db.String(30), default="applied")
    # applied | screening | interview | offered | rejected
    applied_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":          self.id,
            "user_id":     self.user_id,
            "job_id":      self.job_id,
            "match_score": self.match_score,
            "status":      self.status,
            "applied_at":  self.applied_at.isoformat(),
            "job":         self.job.to_dict() if self.job else None
        }
