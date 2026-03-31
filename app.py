from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import os

db = SQLAlchemy()
jwt = JWTManager()
bcrypt = Bcrypt()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'resuai-secret-key')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'resuai-jwt-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///resuai.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

db.init_app(app)
jwt.init_app(app)
bcrypt.init_app(app)
CORS(app)

with app.app_context():
    db.create_all()

@app.route('/')
def health():
    return {'status': 'ResuAI is live!'}

if __name__ == '__main__':
    app.run(debug=True)
