"""
Admin Routes — /api/admin  (Employer side)
GET  /stats               → dashboard stats
GET  /candidates          → list all applicants with AI scores
GET  /candidates/<id>     → view single candidate resume
POST /jobs                → post a new job
GET  /jobs                → list employer's job postings
DELETE /jobs/<id>         → remove job posting
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Job, Application, User, Resume
from utils.parser import match_score

admin_bp = Blueprint("admin", __name__)


def require_employer(user_id):
    user = User.query.get(user_id)
    if not user or user.role != "employer":
        return False
    return True


# ─── DASHBOARD STATS ──────────────────────────────────────────────────────────
@admin_bp.route("/stats", methods=["GET"])
@jwt_required()
def stats():
    total_applications = Application.query.count()
    total_jobs         = Job.query.filter_by(is_active=True).count()
    shortlisted        = Application.query.filter_by(status="interview").count()
    offers_made        = Application.query.filter_by(status="offered").count()

    return jsonify({
        "total_applications": total_applications,
        "active_jobs":        total_jobs,
        "shortlisted":        shortlisted,
        "offers_made":        offers_made
    }), 200


# ─── LIST ALL CANDIDATES ──────────────────────────────────────────────────────
@admin_bp.route("/candidates", methods=["GET"])
@jwt_required()
def list_candidates():
    job_id = request.args.get("job_id", type=int)

    if job_id:
        apps = Application.query.filter_by(job_id=job_id).order_by(Application.match_score.desc()).all()
    else:
        apps = Application.query.order_by(Application.match_score.desc()).all()

    result = []
    for app in apps:
        user = User.query.get(app.user_id)
        resume = Resume.query.get(app.resume_id) if app.resume_id else None
        result.append({
            "application_id": app.id,
            "user": user.to_dict() if user else {},
            "resume": resume.to_dict() if resume else {},
            "match_score": app.match_score,
            "status": app.status,
            "applied_at": app.applied_at.isoformat()
        })

    return jsonify(result), 200


# ─── VIEW CANDIDATE RESUME ────────────────────────────────────────────────────
@admin_bp.route("/candidates/<int:user_id>/resume", methods=["GET"])
@jwt_required()
def view_candidate_resume(user_id):
    resume = Resume.query.filter_by(user_id=user_id).order_by(Resume.uploaded_at.desc()).first_or_404()
    user = User.query.get_or_404(user_id)
    return jsonify({
        "user":   user.to_dict(),
        "resume": resume.to_dict()
    }), 200


# ─── POST A JOB ───────────────────────────────────────────────────────────────
@admin_bp.route("/jobs", methods=["POST"])
@jwt_required()
def post_job():
    data = request.get_json()

    required = ["title", "company", "location", "job_type"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    job = Job(
        title           = data["title"],
        company         = data["company"],
        location        = data["location"],
        job_type        = data["job_type"],
        salary          = data.get("salary", ""),
        description     = data.get("description", ""),
        required_skills = data.get("required_skills", []),
        experience_req  = float(data.get("experience_req", 0)),
        is_active       = True
    )
    db.session.add(job)
    db.session.commit()

    return jsonify({
        "message": "Job posted successfully!",
        "job": job.to_dict()
    }), 201


# ─── LIST JOBS ────────────────────────────────────────────────────────────────
@admin_bp.route("/jobs", methods=["GET"])
@jwt_required()
def admin_list_jobs():
    jobs = Job.query.order_by(Job.posted_at.desc()).all()
    result = []
    for job in jobs:
        applicant_count = Application.query.filter_by(job_id=job.id).count()
        result.append({**job.to_dict(), "applicant_count": applicant_count})
    return jsonify(result), 200


# ─── DELETE JOB ───────────────────────────────────────────────────────────────
@admin_bp.route("/jobs/<int:job_id>", methods=["DELETE"])
@jwt_required()
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    job.is_active = False  # Soft delete
    db.session.commit()
    return jsonify({"message": "Job removed from listings"}), 200
