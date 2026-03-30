"""
Auth Routes — /api/auth
POST /register   → create account
POST /login      → get JWT token
GET  /me         → get current user profile
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db, bcrypt
from models import User

auth_bp = Blueprint("auth", __name__)


# ─── REGISTER ─────────────────────────────────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    # Validate required fields
    required = ["first_name", "last_name", "email", "password"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    # Check if email already exists
    if User.query.filter_by(email=data["email"].lower()).first():
        return jsonify({"error": "Email already registered. Please sign in."}), 409

    # Hash password
    hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

    user = User(
        first_name = data["first_name"].strip(),
        last_name  = data["last_name"].strip(),
        email      = data["email"].lower().strip(),
        phone      = data.get("phone", ""),
        password   = hashed_password,
        role       = data.get("role", "jobseeker"),
        domain     = data.get("domain", "")
    )

    db.session.add(user)
    db.session.commit()

    # Create access token immediately after register
    token = create_access_token(identity=str(user.id))

    return jsonify({
        "message": "Account created successfully!",
        "token":   token,
        "user":    user.to_dict()
    }), 201


# ─── LOGIN ────────────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=data["email"].lower().strip()).first()

    if not user or not bcrypt.check_password_hash(user.password, data["password"]):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_access_token(identity=str(user.id))

    return jsonify({
        "message": "Login successful",
        "token":   token,
        "user":    user.to_dict()
    }), 200


# ─── GET PROFILE ──────────────────────────────────────────────────────────────
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict()), 200


# ─── UPDATE PROFILE ───────────────────────────────────────────────────────────
@auth_bp.route("/me", methods=["PUT"])
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if "first_name" in data: user.first_name = data["first_name"]
    if "last_name"  in data: user.last_name  = data["last_name"]
    if "phone"      in data: user.phone      = data["phone"]
    if "domain"     in data: user.domain     = data["domain"]

    db.session.commit()
    return jsonify({"message": "Profile updated", "user": user.to_dict()}), 200


# ─── CHANGE PASSWORD ──────────────────────────────────────────────────────────
@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if not bcrypt.check_password_hash(user.password, data.get("current_password", "")):
        return jsonify({"error": "Current password is incorrect"}), 400

    new_pass = data.get("new_password", "")
    if len(new_pass) < 8:
        return jsonify({"error": "New password must be at least 8 characters"}), 400

    user.password = bcrypt.generate_password_hash(new_pass).decode("utf-8")
    db.session.commit()
    return jsonify({"message": "Password updated successfully"}), 200
