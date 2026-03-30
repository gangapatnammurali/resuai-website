# 🤖 ResuAI — Backend Setup & Deployment Guide
**Author: Keerthi Gangapatnam**

---

## 📁 Project Structure

```
resuai-backend/
├── app.py              ← Main Flask app (entry point)
├── config.py           ← Settings (database, JWT, uploads)
├── models.py           ← Database tables (User, Resume, Job, Application)
├── requirements.txt    ← Python libraries to install
├── Procfile            ← For Render deployment
├── render.yaml         ← Render auto-deploy config
├── routes/
│   ├── auth.py         ← Register / Login / Profile
│   ├── resume.py       ← Upload + AI parse resume
│   ├── jobs.py         ← Browse jobs + Apply
│   └── admin.py        ← Employer dashboard
└── utils/
    ├── parser.py        ← ⭐ AI Resume Parser (core engine)
    └── seed.py          ← Auto-fills sample jobs on first run
```

---

## ✅ STEP 1 — Install Python

Make sure Python 3.10+ is installed.

```bash
python --version
# Should show: Python 3.10.x or higher
```

Download Python: https://www.python.org/downloads/

---

## ✅ STEP 2 — Create Virtual Environment

```bash
# Navigate to project folder
cd resuai-backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

You should see `(venv)` in your terminal.

---

## ✅ STEP 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

This installs: Flask, SQLAlchemy, JWT, spaCy, pdfplumber, python-docx, bcrypt etc.

---

## ✅ STEP 4 — Download spaCy Language Model

```bash
python -m spacy download en_core_web_sm
```

This is the AI model that reads resume text (NLP).

---

## ✅ STEP 5 — Create .env File

Create a file called `.env` in the project root:

```
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
```

> Note: For local development these can be anything. For production, use long random strings.

---

## ✅ STEP 6 — Run the Backend Locally

```bash
python app.py
```

You should see:
```
* Running on http://127.0.0.1:5000
```

The database (`resuai.db`) is created automatically on first run.
Sample jobs are seeded automatically.

---

## 🧪 STEP 7 — Test the API

Open your browser or use Postman/Thunder Client (free VSCode extension).

### Test: Health Check
```
GET http://localhost:5000/
```
Expected: `{"status": "ResuAI API is running ✅"}`

### Test: Register
```
POST http://localhost:5000/api/auth/register
Content-Type: application/json

{
  "first_name": "Keerthi",
  "last_name": "Gangapatnam",
  "email": "keerthi@example.com",
  "password": "Test@1234",
  "role": "jobseeker",
  "domain": "Data Analytics"
}
```

### Test: Login
```
POST http://localhost:5000/api/auth/login
Content-Type: application/json

{
  "email": "keerthi@example.com",
  "password": "Test@1234"
}
```
Copy the `token` from response. Use it in Authorization header for other requests.

### Test: Get Jobs
```
GET http://localhost:5000/api/jobs/
```

### Test: Upload Resume
```
POST http://localhost:5000/api/resume/upload
Authorization: Bearer <your_token>
Content-Type: multipart/form-data
Body: file = your_resume.pdf
```

---

## 🌐 API Reference (All Endpoints)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET    | `/` | No | Health check |
| POST   | `/api/auth/register` | No | Create account |
| POST   | `/api/auth/login` | No | Login + get token |
| GET    | `/api/auth/me` | Yes | Get profile |
| PUT    | `/api/auth/me` | Yes | Update profile |
| GET    | `/api/jobs/` | No | List all jobs |
| GET    | `/api/jobs/<id>` | No | Job details |
| POST   | `/api/jobs/apply/<id>` | Yes | Apply to job |
| GET    | `/api/jobs/applications` | Yes | My applications |
| POST   | `/api/resume/upload` | Yes | Upload & parse resume |
| GET    | `/api/resume/` | Yes | My resumes |
| GET    | `/api/resume/<id>/matches` | Yes | AI job matches |
| GET    | `/api/admin/stats` | Yes | Employer stats |
| GET    | `/api/admin/candidates` | Yes | All candidates |
| POST   | `/api/admin/jobs` | Yes | Post new job |

---

## 🚀 DEPLOY TO RENDER (Free Hosting)

### Step 1: Push to GitHub
```bash
git init
git add .
git commit -m "Initial ResuAI backend"
git remote add origin https://github.com/yourusername/resuai-backend.git
git push -u origin main
```

### Step 2: Create Render Account
Go to: https://render.com → Sign up free (use GitHub login)

### Step 3: Create New Web Service
1. Click **New +** → **Web Service**
2. Connect your GitHub repo
3. Render auto-detects `render.yaml` → click **Apply**
4. Wait 3–5 minutes for build

### Step 4: Get Your Live URL
Render gives you a URL like:
```
https://resuai-backend.onrender.com
```

### Step 5: Connect Frontend to Backend
In your HTML files, replace `http://localhost:5000` with your Render URL.

---

## 🔗 Connect Frontend HTML to Backend

Add this to your frontend HTML files (dashboard.html, upload.html etc):

```javascript
const API_BASE = "https://resuai-backend.onrender.com"; // Your Render URL

// Example: Login
async function login(email, password) {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  const data = await res.json();
  if (data.token) {
    localStorage.setItem("token", data.token);
    window.location.href = "dashboard.html";
  }
}

// Example: Upload Resume
async function uploadResume(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/api/resume/upload`, {
    method: "POST",
    headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` },
    body: formData
  });
  return await res.json();
}

// Example: Get Jobs
async function getJobs() {
  const res = await fetch(`${API_BASE}/api/jobs/`);
  return await res.json();
}
```

---

## 🛡️ Notes

- **SQLite** is used locally (no setup needed)
- **PostgreSQL** is used on Render (auto-configured via `render.yaml`)
- Uploaded resumes are stored in the `uploads/` folder
- JWT tokens expire in 24 hours
- Free Render tier sleeps after 15 min inactivity (wakes up in ~30 sec)

---

## 📞 Need Help?

If you get any error:
1. Check that `venv` is activated
2. Check `pip install -r requirements.txt` ran successfully
3. Run `python -m spacy download en_core_web_sm` separately
4. Make sure `.env` file exists

Good luck with your project, Keerthi! 🚀
