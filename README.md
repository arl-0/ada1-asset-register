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
