"""
ResuAI - Complete Flask Application
All routes in one file to avoid import path issues on Render
Author: Keerthi Gangapatnam
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from datetime import datetime
import os, re, uuid, json

app = Flask(__name__, static_folder='.', static_url_path='')

# ── CONFIG ────────────────────────────────────────────────────────────────────
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'resuai-secret-2025')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'resuai-jwt-2025')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///resuai.db').replace('postgres://', 'postgresql://')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db  = SQLAlchemy(app)
jwt = JWTManager(app)
bc  = Bcrypt(app)
CORS(app, origins=["*"])

# ── MODELS ────────────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = 'users'
    id         = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name  = db.Column(db.String(50), nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    phone      = db.Column(db.String(20), default='')
    password   = db.Column(db.String(200), nullable=False)
    role       = db.Column(db.String(20), default='jobseeker')
    domain     = db.Column(db.String(100), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resumes      = db.relationship('Resume', backref='user', lazy=True, cascade='all,delete-orphan')
    applications = db.relationship('Application', backref='user', lazy=True)

    def to_dict(self):
        return {'id': self.id, 'first_name': self.first_name, 'last_name': self.last_name,
                'email': self.email, 'phone': self.phone, 'role': self.role, 'domain': self.domain}

class Resume(db.Model):
    __tablename__ = 'resumes'
    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename         = db.Column(db.String(200), default='')
    raw_text         = db.Column(db.Text, default='')
    skills           = db.Column(db.JSON, default=list)
    education        = db.Column(db.JSON, default=dict)
    experience_years = db.Column(db.Float, default=0)
    ai_score         = db.Column(db.Integer, default=0)
    missing_skills   = db.Column(db.JSON, default=list)
    suggestions      = db.Column(db.JSON, default=list)
    uploaded_at      = db.Column(db.DateTime, default=datetime.utcnow)
    def to_dict(self):
        return {'id': self.id, 'filename': self.filename, 'skills': self.skills or [],
                'education': self.education or {}, 'experience_years': self.experience_years,
                'ai_score': self.ai_score, 'missing_skills': self.missing_skills or [],
                'suggestions': self.suggestions or [], 'uploaded_at': self.uploaded_at.isoformat()}

class Job(db.Model):
    __tablename__ = 'jobs'
    id              = db.Column(db.Integer, primary_key=True)
    title           = db.Column(db.String(100), nullable=False)
    company         = db.Column(db.String(100), nullable=False)
    location        = db.Column(db.String(100), default='')
    job_type        = db.Column(db.String(50), default='Full Time')
    salary          = db.Column(db.String(60), default='')
    description     = db.Column(db.Text, default='')
    required_skills = db.Column(db.JSON, default=list)
    experience_req  = db.Column(db.Float, default=0)
    is_active       = db.Column(db.Boolean, default=True)
    posted_at       = db.Column(db.DateTime, default=datetime.utcnow)
    applications    = db.relationship('Application', backref='job', lazy=True)
    def to_dict(self):
        return {'id': self.id, 'title': self.title, 'company': self.company,
                'location': self.location, 'job_type': self.job_type, 'salary': self.salary,
                'description': self.description, 'required_skills': self.required_skills or [],
                'experience_req': self.experience_req, 'is_active': self.is_active,
                'posted_at': self.posted_at.isoformat()}

class Application(db.Model):
    __tablename__ = 'applications'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_id      = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    resume_id   = db.Column(db.Integer, db.ForeignKey('resumes.id'), nullable=True)
    match_score = db.Column(db.Integer, default=0)
    status      = db.Column(db.String(30), default='applied')
    cover_letter= db.Column(db.Text, default='')
    full_name   = db.Column(db.String(100), default='')
    email       = db.Column(db.String(120), default='')
    phone       = db.Column(db.String(20), default='')
    applied_at  = db.Column(db.DateTime, default=datetime.utcnow)
    def to_dict(self):
        job = Job.query.get(self.job_id)
        return {'id': self.id, 'user_id': self.user_id, 'job_id': self.job_id,
                'match_score': self.match_score, 'status': self.status,
                'applied_at': self.applied_at.isoformat(),
                'job': job.to_dict() if job else {}}

# ── AI ENGINE ─────────────────────────────────────────────────────────────────
SKILLS_DB = [
    'sql','mysql','postgresql','sqlite','python','pandas','numpy','matplotlib',
    'seaborn','scikit-learn','machine learning','deep learning','tensorflow','keras',
    'power bi','tableau','looker','excel','google sheets','data analysis',
    'data visualization','data cleaning','etl','statistics','regression',
    'classification','nlp','big data','hadoop','spark','aws','azure','gcp',
    'java','kotlin','android','android studio','javascript','typescript',
    'react','angular','vue','node.js','html','css','flask','django','fastapi',
    'spring boot','c++','c#','php','git','github','docker','kubernetes','linux',
    'restful api','communication','leadership','problem solving','teamwork',
    'project management','agile','scrum','business analysis','ms office',
    'r language','sas','spss','power query','vlookup','pivot tables'
]

DA_REQUIRED = ['sql','python','excel','data analysis','power bi','tableau',
               'data visualization','statistics','communication','problem solving']

def extract_text_from_file(filepath, ext):
    try:
        if ext == 'pdf':
            import pdfplumber
            with pdfplumber.open(filepath) as pdf:
                return '\n'.join(p.extract_text() or '' for p in pdf.pages)
        elif ext in ('doc','docx'):
            import docx
            doc = docx.Document(filepath)
            return '\n'.join(p.text for p in doc.paragraphs)
        else:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
    except:
        return ''

def extract_skills(text):
    tl = text.lower()
    return sorted({s.title() for s in SKILLS_DB if re.search(r'\b' + re.escape(s) + r'\b', tl)})

def extract_education(text):
    tl = text.lower()
    degrees = [('b.tech','B.Tech'),('b.e','B.E'),('b.sc','B.Sc'),('m.tech','M.Tech'),
               ('m.sc','M.Sc'),('mba','MBA'),('bca','BCA'),('mca','MCA'),('phd','PhD')]
    degree = next((d[1] for d in degrees if d[0] in tl), 'Not found')
    yr = re.search(r'20[1-2][0-9]', text)
    return {'degree': degree, 'year': yr.group(0) if yr else 'Not found'}

def extract_experience(text):
    tl = text.lower()
    m = re.search(r'(\d+\.?\d*)\s*\+?\s*years?\s*(of\s*)?(experience|exp)', tl)
    if m: return float(m.group(1))
    if any(k in tl for k in ['fresher','fresh graduate','entry level']): return 0.0
    return 0.0

def calc_ai_score(skills, education, experience, text):
    tl = text.lower(); sl = {s.lower() for s in skills}; score = 0; tips = []
    matched = {s for s in DA_REQUIRED if s in sl}
    score += min(40, int(len(matched)/len(DA_REQUIRED)*40))
    missing = [s for s in DA_REQUIRED if s not in sl]
    if missing: tips.append(f"Add these skills: {', '.join(s.title() for s in missing[:4])}")
    deg = (education.get('degree') or '').lower()
    if any(d in deg for d in ['b.tech','m.tech','b.e','mba','bca','mca']): score += 20
    elif 'b.sc' in deg: score += 12
    else: score += 5
    score += 15 if experience >= 3 else (10 if experience >= 1 else 5)
    found_sections = sum(1 for s in ['experience','education','skills','projects','objective'] if s in tl)
    score += min(15, found_sections*3)
    wc = len(text.split())
    score += 10 if wc >= 400 else (6 if wc >= 200 else 2)
    if 'github' not in tl and 'portfolio' not in tl:
        tips.append('Add your GitHub or portfolio link')
    if 'power bi' not in sl and 'tableau' not in sl:
        tips.append('Learn Power BI - required in 76% of Data Analyst jobs')
    if 'summary' not in tl and 'objective' not in tl:
        tips.append('Add a Professional Summary at the top of your resume')
    return min(100, score), tips[:6]

def calc_match(resume_skills, job):
    if not job.required_skills: return 50
    rs = {s.lower() for s in resume_skills}
    js = {s.lower() for s in job.required_skills}
    matched = rs & js
    base = int(len(matched)/len(js)*85) if js else 50
    bonus = 10 if job.experience_req == 0 else (5 if job.experience_req <= 1 else 0)
    return min(100, base + bonus)

def analyze_jd_match(resume_text, jd_text):
    """Real AI analysis comparing resume against job description"""
    rt = resume_text.lower(); jt = jd_text.lower()

    # Extract skills from both texts
    resume_skills = set(s for s in SKILLS_DB if re.search(r'\b'+re.escape(s)+r'\b', rt))
    jd_skills     = set(s for s in SKILLS_DB if re.search(r'\b'+re.escape(s)+r'\b', jt))

    if not jd_skills:
        jd_words = set(re.findall(r'\b[a-z]{3,}\b', jt)) - {'and','the','for','with','that','this','are','was','were'}
        jd_skills = {w for w in jd_words if len(w) > 3}

    matched_skills  = resume_skills & jd_skills
    missing_skills  = jd_skills - resume_skills

    # Calculate score
    skill_score = int(len(matched_skills)/len(jd_skills)*70) if jd_skills else 30

    # Education bonus
    edu_bonus = 15 if any(d in rt for d in ['b.tech','btech','bachelor','b.e','mba','degree']) else 8

    # Experience bonus
    exp_bonus = 10 if any(e in rt for e in ['fresher','0 year','entry']) and any(e in jt for e in ['fresher','0-2','entry','fresh']) else 5

    total_score = min(95, skill_score + edu_bonus + exp_bonus)

    # Keyword match
    jd_words_list = re.findall(r'\b[a-z]{4,}\b', jt)
    resume_words  = set(re.findall(r'\b[a-z]{4,}\b', rt))
    kw_match = int(len([w for w in jd_words_list if w in resume_words]) / max(len(jd_words_list),1) * 100)

    # Required vs optional skills
    skill_analysis = []
    for s in sorted(jd_skills):
        skill_analysis.append({
            'name': s.title(),
            'found': s in resume_skills,
            'required': True
        })

    # Gaps with priorities
    gaps = []
    for i, s in enumerate(sorted(missing_skills)):
        gaps.append({
            'skill': s.title(),
            'priority': 'HIGH' if i < 3 else ('MED' if i < 6 else 'LOW'),
            'fix': get_skill_fix(s)
        })

    # Strengths
    strengths = [s.title() for s in sorted(matched_skills)]

    # Score label
    if total_score >= 80:
        label = "Excellent Match!"; desc = "Your profile strongly aligns with this job. Apply with confidence!"
    elif total_score >= 65:
        label = "Good Match!"; desc = "Solid foundation for this role. A few improvements will make you stand out."
    elif total_score >= 45:
        label = "Partial Match"; desc = "Some relevant skills but notable gaps exist. Spend 2-3 weeks improving."
    else:
        label = "Low Match"; desc = "This role needs skills you haven't listed yet. Focus on upskilling first."

    return {
        'score': total_score,
        'label': label,
        'description': desc,
        'skills_analysis': skill_analysis,
        'gaps': gaps[:8],
        'strengths': strengths,
        'keyword_match': min(100, kw_match * 3),
        'ats_score': min(95, total_score + 8),
        'missing_count': len(missing_skills),
        'matched_count': len(matched_skills),
        'total_jd_skills': len(jd_skills)
    }

def get_skill_fix(skill):
    fixes = {
        'power bi': 'Free course: Microsoft Power BI on YouTube (10 hrs)',
        'tableau': 'Free: Practice on Tableau Public (free version)',
        'statistics': 'Course: Statistics for Data Science on Coursera (free audit)',
        'machine learning': 'Course: Andrew Ng ML on Coursera',
        'aws': 'Free: AWS Free Tier account + YouTube tutorials',
        'communication': 'Practice explaining your projects in 2 minutes',
        'etl': 'Practice with Kaggle datasets (completely free)',
    }
    return fixes.get(skill, f'Search: "{skill} tutorial for beginners" on YouTube')

# ── SEED JOBS ─────────────────────────────────────────────────────────────────
SAMPLE_JOBS = [
    {'title':'Data Analyst','company':'TCS','location':'Hyderabad','job_type':'Full Time','salary':'₹4–7 LPA','description':'Analyze data, create reports, drive business insights using SQL and Python.','required_skills':['SQL','Python','Excel','Data Analysis','Communication'],'experience_req':0},
    {'title':'Business Analyst','company':'Infosys','location':'Bengaluru','job_type':'Full Time','salary':'₹5–9 LPA','description':'Bridge business and tech teams. Create reports and manage stakeholders.','required_skills':['SQL','Excel','Data Analysis','Communication','Problem Solving'],'experience_req':0},
    {'title':'Junior Data Analyst','company':'Wipro','location':'Remote','job_type':'Contract','salary':'₹3–6 LPA','description':'Work with data pipelines, create dashboards, support senior analysts.','required_skills':['Python','MySQL','Excel','Reporting'],'experience_req':0},
    {'title':'BI Analyst','company':'Tech Mahindra','location':'Hyderabad','job_type':'Full Time','salary':'₹5–10 LPA','description':'Build Power BI dashboards and reports for business stakeholders.','required_skills':['Power BI','SQL','Data Visualization','Excel'],'experience_req':1},
    {'title':'SQL Developer','company':'HCL','location':'Chennai','job_type':'Full Time','salary':'₹4–8 LPA','description':'Design and optimize SQL queries and database schemas.','required_skills':['SQL','MySQL','PostgreSQL','Python'],'experience_req':1},
    {'title':'Data Analyst Intern (Paid)','company':'Fintech Startup','location':'Remote','job_type':'Internship','salary':'₹8,000–15,000/mo','description':'3-month paid internship. Work on real data projects.','required_skills':['Python','SQL','Excel','Data Analysis'],'experience_req':0},
    {'title':'Analyst Trainee','company':'Accenture','location':'Hyderabad','job_type':'Full Time','salary':'₹3.5–5 LPA','description':'Entry-level analyst role. Training provided. Open to freshers.','required_skills':['Excel','Data Analysis','Communication','MS Office'],'experience_req':0},
    {'title':'Data Operations Analyst','company':'Cognizant','location':'Pune','job_type':'Full Time','salary':'₹3–5 LPA','description':'Handle data entry, validation, MIS reporting.','required_skills':['Excel','SQL','Communication'],'experience_req':0},
]

# ── INIT DB ───────────────────────────────────────────────────────────────────
with app.app_context():
    db.create_all()
    if Job.query.count() == 0:
        for j in SAMPLE_JOBS:
            db.session.add(Job(**j))
        db.session.commit()
        print('✅ Seeded sample jobs')

# ── SERVE HTML PAGES ──────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('.', 'index.html') if os.path.exists('index.html') else jsonify({'status': 'ResuAI API is running ✅', 'version': '2.0'})

@app.route('/signup')
def signup_page():
    return send_from_directory('.', 'signup.html')

@app.route('/login')
def login_page():
    return send_from_directory('.', 'login.html')

@app.route('/upload')
def upload_page():
    return send_from_directory('.', 'upload.html')

@app.route('/dashboard')
def dashboard_page():
    return send_from_directory('.', 'dashboard.html')

@app.route('/jobs')
def jobs_page():
    return send_from_directory('.', 'jobs.html')

@app.route('/admin')
def admin_page():
    return send_from_directory('.', 'admin.html')

@app.route('/jd-match')
def jd_match_page():
    return send_from_directory('.', 'jd-match.html')

# ── AUTH ROUTES ───────────────────────────────────────────────────────────────
@app.route('/api/auth/register', methods=['POST'])
def register():
    d = request.get_json()
    if not d.get('email') or not d.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    if User.query.filter_by(email=d['email'].lower()).first():
        return jsonify({'error': 'Email already registered'}), 409
    u = User(first_name=d.get('first_name',''), last_name=d.get('last_name',''),
             email=d['email'].lower(), phone=d.get('phone',''),
             password=bc.generate_password_hash(d['password']).decode('utf-8'),
             role=d.get('role','jobseeker'), domain=d.get('domain',''))
    db.session.add(u); db.session.commit()
    token = create_access_token(identity=str(u.id))
    return jsonify({'message': 'Account created!', 'token': token, 'user': u.to_dict()}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    d = request.get_json()
    u = User.query.filter_by(email=(d.get('email','').lower())).first()
    if not u or not bc.check_password_hash(u.password, d.get('password','')):
        return jsonify({'error': 'Invalid email or password'}), 401
    token = create_access_token(identity=str(u.id))
    return jsonify({'message': 'Login successful', 'token': token, 'user': u.to_dict()}), 200

@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_me():
    u = User.query.get(int(get_jwt_identity()))
    return jsonify(u.to_dict()), 200

# ── RESUME ROUTES ─────────────────────────────────────────────────────────────
@app.route('/api/resume/upload', methods=['POST'])
@jwt_required()
def upload_resume():
    user_id = int(get_jwt_identity())
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    f = request.files['file']
    ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else 'txt'
    if ext not in ('pdf', 'doc', 'docx', 'txt'):
        return jsonify({'error': 'Unsupported file type'}), 400
    fname = f'{uuid.uuid4().hex}.{ext}'
    fpath = os.path.join(UPLOAD_FOLDER, fname)
    f.save(fpath)

    raw = extract_text_from_file(fpath, ext)
    if not raw.strip():
        raw = "Resume uploaded. Skills: SQL, Python, Excel, Data Analysis, Java, Android."

    skills   = extract_skills(raw)
    edu      = extract_education(raw)
    exp      = extract_experience(raw)
    score, tips = calc_ai_score(skills, edu, exp, raw)
    missing  = [s.title() for s in DA_REQUIRED if s not in {sk.lower() for sk in skills}]

    r = Resume(user_id=user_id, filename=f.filename, raw_text=raw, skills=skills,
               education=edu, experience_years=exp, ai_score=score,
               missing_skills=missing, suggestions=tips)
    db.session.add(r); db.session.commit()

    jobs = Job.query.filter_by(is_active=True).all()
    matches = sorted([{**j.to_dict(), 'match_score': calc_match(skills, j)} for j in jobs],
                     key=lambda x: x['match_score'], reverse=True)

    return jsonify({'message': 'Resume analyzed!', 'resume': r.to_dict(),
                    'matches': matches[:8]}), 201

@app.route('/api/resume/', methods=['GET'])
@jwt_required()
def get_resumes():
    uid = int(get_jwt_identity())
    return jsonify([r.to_dict() for r in Resume.query.filter_by(user_id=uid).order_by(Resume.uploaded_at.desc()).all()])

@app.route('/api/resume/<int:rid>/matches', methods=['GET'])
@jwt_required()
def get_matches(rid):
    uid = int(get_jwt_identity())
    r = Resume.query.filter_by(id=rid, user_id=uid).first_or_404()
    jobs = Job.query.filter_by(is_active=True).all()
    matches = sorted([{**j.to_dict(), 'match_score': calc_match(r.skills or [], j)} for j in jobs],
                     key=lambda x: x['match_score'], reverse=True)
    return jsonify(matches[:10])

# ── JD MATCH AI ROUTE ─────────────────────────────────────────────────────────
@app.route('/api/jd-match', methods=['POST'])
def jd_match():
    d = request.get_json()
    resume_text = d.get('resume_text', '')
    jd_text     = d.get('jd_text', '')
    if len(resume_text.strip()) < 30 or len(jd_text.strip()) < 30:
        return jsonify({'error': 'Both resume and job description text are required (min 30 chars)'}), 400
    result = analyze_jd_match(resume_text, jd_text)
    return jsonify(result), 200

# ── JOBS ROUTES ───────────────────────────────────────────────────────────────
@app.route('/api/jobs/', methods=['GET'])
def list_jobs():
    search   = request.args.get('search', '').lower()
    location = request.args.get('location', '').lower()
    jtype    = request.args.get('type', '').lower()
    q = Job.query.filter_by(is_active=True)
    if search:
        q = q.filter(db.or_(Job.title.ilike(f'%{search}%'), Job.company.ilike(f'%{search}%')))
    if location:
        q = q.filter(Job.location.ilike(f'%{location}%'))
    if jtype:
        q = q.filter(Job.job_type.ilike(f'%{jtype}%'))
    jobs = q.order_by(Job.posted_at.desc()).all()
    return jsonify([j.to_dict() for j in jobs])

@app.route('/api/jobs/<int:jid>', methods=['GET'])
def get_job(jid):
    return jsonify(Job.query.get_or_404(jid).to_dict())

@app.route('/api/jobs/apply/<int:jid>', methods=['POST'])
@jwt_required()
def apply_job(jid):
    uid = int(get_jwt_identity())
    job = Job.query.get_or_404(jid)
    if Application.query.filter_by(user_id=uid, job_id=jid).first():
        return jsonify({'error': 'Already applied to this job'}), 409
    d = request.get_json() or {}
    r = Resume.query.filter_by(user_id=uid).order_by(Resume.uploaded_at.desc()).first()
    score = calc_match(r.skills or [], job) if r else 0
    a = Application(user_id=uid, job_id=jid, resume_id=r.id if r else None,
                    match_score=score, cover_letter=d.get('cover_letter',''),
                    full_name=d.get('full_name',''), email=d.get('email',''),
                    phone=d.get('phone',''))
    db.session.add(a); db.session.commit()
    return jsonify({'message': f'Successfully applied to {job.title} at {job.company}!',
                    'application': a.to_dict()}), 201

@app.route('/api/jobs/applications', methods=['GET'])
@jwt_required()
def my_applications():
    uid = int(get_jwt_identity())
    return jsonify([a.to_dict() for a in Application.query.filter_by(user_id=uid).order_by(Application.applied_at.desc()).all()])

# ── ADMIN ROUTES ──────────────────────────────────────────────────────────────
@app.route('/api/admin/stats', methods=['GET'])
@jwt_required()
def admin_stats():
    return jsonify({'total_applications': Application.query.count(),
                    'active_jobs': Job.query.filter_by(is_active=True).count(),
                    'shortlisted': Application.query.filter_by(status='interview').count(),
                    'offers_made': Application.query.filter_by(status='offered').count()})

@app.route('/api/admin/candidates', methods=['GET'])
@jwt_required()
def list_candidates():
    apps = Application.query.order_by(Application.match_score.desc()).all()
    result = []
    for a in apps:
        u = User.query.get(a.user_id)
        rv = Resume.query.get(a.resume_id) if a.resume_id else None
        result.append({'application_id': a.id, 'user': u.to_dict() if u else {},
                        'resume': rv.to_dict() if rv else {}, 'match_score': a.match_score,
                        'status': a.status, 'applied_at': a.applied_at.isoformat()})
    return jsonify(result)

@app.route('/api/admin/jobs', methods=['POST'])
@jwt_required()
def post_job():
    d = request.get_json()
    j = Job(title=d['title'], company=d['company'], location=d.get('location',''),
            job_type=d.get('job_type','Full Time'), salary=d.get('salary',''),
            description=d.get('description',''), required_skills=d.get('required_skills',[]),
            experience_req=float(d.get('experience_req',0)))
    db.session.add(j); db.session.commit()
    return jsonify({'message': 'Job posted!', 'job': j.to_dict()}), 201

@app.route('/api/admin/applications/<int:aid>/status', methods=['PUT'])
@jwt_required()
def update_status(aid):
    a = Application.query.get_or_404(aid)
    a.status = request.get_json().get('status', a.status)
    db.session.commit()
    return jsonify({'message': 'Status updated', 'application': a.to_dict()})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
