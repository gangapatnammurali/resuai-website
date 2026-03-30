"""
Jobs Routes — /api/jobs
GET  /              → list all active jobs (with optional filters)
GET  /<id>          → get single job details
POST /apply/<id>    → apply to a job
GET  /applications  → get user's applications
PUT  /applications/<id>/status → update status (employer only)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Job, Application, Resume
from utils.parser import match_score

jobs_bp = Blueprint("jobs", __name__)


# ─── LIST ALL JOBS ────────────────────────────────────────────────────────────
@jobs_bp.route("/", methods=["GET"])
def list_jobs():
    # Query params for filtering
    search   = request.args.get("search", "").lower()
    location = request.args.get("location", "").lower()
    job_type = request.args.get("type", "").lower()
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))

    query = Job.query.filter_by(is_active=True)

    if search:
        query = query.filter(
            db.or_(
                Job.title.ilike(f"%{search}%"),
                Job.company.ilike(f"%{search}%"),
                Job.description.ilike(f"%{search}%")
            )
        )
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    if job_type:
        query = query.filter(Job.job_type.ilike(f"%{job_type}%"))

    query = query.order_by(Job.posted_at.desc())
    total  = query.count()
    jobs   = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        "jobs":       [j.to_dict() for j in jobs],
        "total":      total,
        "page":       page,
        "per_page":   per_page,
        "total_pages": (total + per_page - 1) // per_page
    }), 200


# ─── GET SINGLE JOB ───────────────────────────────────────────────────────────
@jobs_bp.route("/<int:job_id>", methods=["GET"])
def get_job(job_id):
    job = Job.query.get_or_404(job_id)
    return jsonify(job.to_dict()), 200


# ─── APPLY TO JOB ─────────────────────────────────────────────────────────────
@jobs_bp.route("/apply/<int:job_id>", methods=["POST"])
@jwt_required()
def apply_job(job_id):
    user_id = int(get_jwt_identity())
    job = Job.query.get_or_404(job_id)

    # Check if already applied
    existing = Application.query.filter_by(user_id=user_id, job_id=job_id).first()
    if existing:
        return jsonify({"error": "You have already applied to this job"}), 409

    # Get latest resume for match score
    resume = Resume.query.filter_by(user_id=user_id).order_by(Resume.uploaded_at.desc()).first()
    score = 0
    resume_id = None
    if resume:
        score = match_score(resume.skills or [], job)
        resume_id = resume.id

    application = Application(
        user_id     = user_id,
        job_id      = job_id,
        resume_id   = resume_id,
        match_score = score,
        status      = "applied"
    )
    db.session.add(application)
    db.session.commit()

    return jsonify({
        "message":     "Application submitted successfully!",
        "application": application.to_dict()
    }), 201


# ─── GET USER'S APPLICATIONS ──────────────────────────────────────────────────
@jobs_bp.route("/applications", methods=["GET"])
@jwt_required()
def get_applications():
    user_id = int(get_jwt_identity())
    apps = Application.query.filter_by(user_id=user_id).order_by(Application.applied_at.desc()).all()
    return jsonify([a.to_dict() for a in apps]), 200


# ─── UPDATE APPLICATION STATUS (employer) ────────────────────────────────────
@jobs_bp.route("/applications/<int:app_id>/status", methods=["PUT"])
@jwt_required()
def update_status(app_id):
    data = request.get_json()
    new_status = data.get("status")

    valid = ["applied", "screening", "interview", "offered", "rejected"]
    if new_status not in valid:
        return jsonify({"error": f"Status must be one of: {', '.join(valid)}"}), 400

    app = Application.query.get_or_404(app_id)
    app.status = new_status
    db.session.commit()

    return jsonify({"message": "Status updated", "application": app.to_dict()}), 200
