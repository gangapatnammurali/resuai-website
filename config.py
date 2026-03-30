"""
Configuration settings for ResuAI Flask app
"""

import os
from datetime import timedelta

class Config:
    # ─── Security ─────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "resuai-dev-secret-key-change-in-production")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "resuai-jwt-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

    # ─── Database ─────────────────────────────────────
    # Uses SQLite locally, PostgreSQL on Render (set DATABASE_URL env var)
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///resuai.db")

    # Render gives postgres://, SQLAlchemy needs postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ─── File Uploads ─────────────────────────────────
    UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max
    ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "txt"}

    # ─── CORS ─────────────────────────────────────────
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
