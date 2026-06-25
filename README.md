# ADA-1 Asset Register

A clearance-based secure asset register built with Python and Flask, developed as part of the L6M5 Software Engineering and DevOps module (BSc Digital and Technology Solutions, University of Roehampton).

---

## Demo credentials (live deployment)

| Username | Password | Clearance | Role |
|---|---|---|---|
| `admin` | `Admin1234!` | 5 (full access) | Admin |
| `bob.researcher` | `Research99` | 2 (limited access) | Regular |

The startup passphrase (boot screen) is: **only at the blind**

---

## Tech stack

- Python 3.11 / Flask 3.1
- SQLAlchemy + SQLite
- Flask-WTF (CSRF protection)
- Flask-Login (session management)
- Werkzeug (password hashing)
- pytest + GitHub Actions (CI)
- Gunicorn (production server)

---

## Run locally

```bash
git clone https://github.com/YOUR_USERNAME/ada1_project.git
cd ada1_project

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env and set a SECRET_KEY value

python seed.py                  # creates and seeds the database
python run.py                   # starts on http://localhost:5050
```

---

## Deploy to Render (free tier)

### Step 1 — Push to GitHub

Make sure all files (including `render.yaml`, `start.sh`, and `seed.py`) are committed and pushed to your GitHub repository:

```bash
git add .
git commit -m "Add deployment files"
git push origin main
```

### Step 2 — Create a Render account

Go to [https://render.com](https://render.com) and sign up with your GitHub account (free, no credit card needed).

### Step 3 — Deploy via Blueprint (easiest)

1. In the Render dashboard, click **New → Blueprint**.
2. Connect your GitHub repository when prompted.
3. Render will detect `render.yaml` and pre-fill everything — click **Apply**.
4. Wait for the build to finish (usually 2–3 minutes on first deploy).
5. Your app will be live at `https://ada1-asset-register.onrender.com` (or similar).

### Step 4 — Manual setup (alternative to Blueprint)

If you prefer to configure manually:

1. Click **New → Web Service**.
2. Connect your GitHub repo.
3. Set:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `bash start.sh`
4. Under **Environment**, add:
   - `SECRET_KEY` → click "Generate" for a secure random value
   - `PYTHON_VERSION` → `3.11.0`
5. Click **Create Web Service**.

### Step 5 — Verify the deployment

Once live, visit the URL Render gives you. The app will run through the boot sequence — enter `only at the blind` to reach the login page.

> **Note on cold starts:** Render's free tier spins down after 15 minutes of inactivity. The first request after that takes ~60 seconds to wake up. This is normal on the free tier. If the examiner clicks the link and sees a loading spinner, they just need to wait ~60 seconds.

---

## CI/CD

Every push to `main` triggers the GitHub Actions workflow (`.github/workflows/test.yml`), which:
- Installs dependencies
- Runs the full 16-test pytest suite with coverage reporting

---

## Project structure

```
ada1_project/
├── app/
│   ├── __init__.py       # App factory, CSRF setup
│   ├── models.py         # User, ADAEntry, ChangeLog
│   ├── forms.py          # WTForms with validation
│   ├── routes.py         # All routes (auth, CRUD, admin)
│   ├── static/css/       # Accessible stylesheet
│   └── templates/        # Jinja2 templates (extends base.html)
├── tests/
│   └── test_app.py       # 16 pytest tests (auth, RBAC, injection, CSRF)
├── .github/workflows/
│   └── test.yml          # GitHub Actions CI pipeline
├── seed.py               # Database seeding script
├── start.sh              # Render startup script
├── render.yaml           # Render Blueprint config
├── run.py                # Local development entry point
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## OWASP mitigations

| OWASP Category | Mitigation in ADA-1 |
|---|---|
| A01 Broken Access Control | Server-side role check on all admin routes; per-request clearance check on every asset detail view; POST-only deletes with CSRF tokens |
| A02 Cryptographic Failures | Passwords hashed with Werkzeug's scrypt (never stored as plaintext); SECRET_KEY in environment variable |
| A03 Injection | All DB access via SQLAlchemy ORM with parameterised queries |
| A05 Security Misconfiguration | SECRET_KEY from environment; `.env` excluded from version control via `.gitignore` |
| A07 Identification & Authentication Failures | Custom password strength validator (min 8 chars + digit); generic error messages (no user enumeration) |
