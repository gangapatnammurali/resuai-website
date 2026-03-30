"""
Resume Routes — /api/resume
POST /upload         → upload & parse resume (AI analysis)
GET  /               → get all resumes for logged-in user
GET  /<id>           → get single resume details
GET  /<id>/matches   → get AI-matched jobs for this resume
DELETE /<id>         → delete a resume
"""

import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app import db
from models import Resume, Job, Application
from utils.parser import parse_resume, match_score

resume_bp = Blueprint("resume", __name__)


def allowed_file(filename):
    allowed = current_app.config["ALLOWED_EXTENSIONS"]
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


# ─── UPLOAD & PARSE ───────────────────────────────────────────────────────────
@resume_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_resume():
    user_id = int(get_jwt_identity())

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type. Use PDF, DOCX, or TXT"}), 400

    # Save file with unique name
    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, unique_name)
    file.save(filepath)

    # Run AI parser
    try:
        parsed = parse_resume(filepath)
    except Exception as e:
        os.remove(filepath)
        return jsonify({"error": f"Could not parse resume: {str(e)}"}), 422

    # Save to database
    resume = Resume(
        user_id          = user_id,
        filename         = secure_filename(file.filename),
        raw_text         = parsed["raw_text"],
        skills           = parsed["skills"],
        education        = parsed["education"],
        experience_years = parsed["experience_years"],
        ai_score         = parsed["ai_score"],
        missing_skills   = parsed["missing_skills"],
        suggestions      = parsed["suggestions"]
    )
    db.session.add(resume)
    db.session.commit()

    # Get job matches right away
    jobs = Job.query.filter_by(is_active=True).all()
    matches = []
    for job in jobs:
        score = match_score(parsed["skills"], job)
        if score >= 50:
            matches.append({**job.to_dict(), "match_score": score})

    matches.sort(key=lambda x: x["match_score"], reverse=True)

    return jsonify({
        "message":  "Resume uploaded and analyzed successfully!",
        "resume":   resume.to_dict(),
        "contact":  parsed.get("contact", {}),
        "matches":  matches[:10]
    }), 201


# ─── GET ALL RESUMES ──────────────────────────────────────────────────────────
@resume_bp.route("/", methods=["GET"])
@jwt_required()
def get_resumes():
    user_id = int(get_jwt_identity())
    resumes = Resume.query.filter_by(user_id=user_id).order_by(Resume.uploaded_at.desc()).all()
    return jsonify([r.to_dict() for r in resumes]), 200


# ─── GET SINGLE RESUME ────────────────────────────────────────────────────────
@resume_bp.route("/<int:resume_id>", methods=["GET"])
@jwt_required()
def get_resume(resume_id):
    user_id = int(get_jwt_identity())
    resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first_or_404()
    return jsonify(resume.to_dict()), 200


# ─── GET JOB MATCHES FOR RESUME ───────────────────────────────────────────────
@resume_bp.route("/<int:resume_id>/matches", methods=["GET"])
@jwt_required()
def get_matches(resume_id):
    user_id = int(get_jwt_identity())
    resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first_or_404()

    jobs = Job.query.filter_by(is_active=True).all()
    matches = []
    for job in jobs:
        score = match_score(resume.skills or [], job)
        if score >= 45:
            matches.append({**job.to_dict(), "match_score": score})

    matches.sort(key=lambda x: x["match_score"], reverse=True)
    return jsonify(matches[:15]), 200


# ─── DELETE RESUME ────────────────────────────────────────────────────────────
@resume_bp.route("/<int:resume_id>", methods=["DELETE"])
@jwt_required()
def delete_resume(resume_id):
    user_id = int(get_jwt_identity())
    resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first_or_404()
    db.session.delete(resume)
    db.session.commit()
    return jsonify({"message": "Resume deleted"}), 200
