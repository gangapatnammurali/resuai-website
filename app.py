"""
ResuAI - Main Flask Application
Author: Keerthi Gangapatnam
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from config import Config

db = SQLAlchemy()
jwt = JWTManager()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Init extensions
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    CORS(app, origins=["*"])

    # Register blueprints (route groups)
    from routes.auth import auth_bp
    from routes.resume import resume_bp
    from routes.jobs import jobs_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp,   url_prefix="/api/auth")
    app.register_blueprint(resume_bp, url_prefix="/api/resume")
    app.register_blueprint(jobs_bp,   url_prefix="/api/jobs")
    app.register_blueprint(admin_bp,  url_prefix="/api/admin")

    # Create all tables on first run
    with app.app_context():
        db.create_all()
        from utils.seed import seed_jobs
        seed_jobs()

    @app.route("/")
    def health():
        return {"status": "ResuAI API is running ✅", "version": "1.0.0"}

    return app

    app = create_app()
if __name__ == "__main__":
   
    app.run(debug=True, port=5000)
