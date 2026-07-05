# NeoCare - AI Postpartum & Child Health Monitoring System

> **NeoCare** is an AI-powered, full-stack web application built to support new mothers through postpartum recovery and monitor newborn growth and development. It combines clinical standards (WHO Growth Charts, TDSC Milestones, EPDS Screening) with a compassionate Groq-powered AI chatbot — all in one accessible platform designed for Indian families.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation and Setup](#installation-and-setup)
- [Environment Variables](#environment-variables)
- [Running the App](#running-the-app)
- [Pages and Navigation](#pages-and-navigation)
- [API Reference](#api-reference)
- [Module Details](#module-details)
- [Email Alerts Setup](#email-alerts-setup)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)
- [Dependencies](#dependencies)
- [Disclaimer](#disclaimer)

---

## Overview

NeoCare is a **full-stack health support tool** for new mothers and their families. It is not a diagnostic platform — it is a screening, education, and early-warning system that brings clinical guidelines to everyday caregivers.

The application runs via a **Python FastAPI backend** that serves both the REST API and the HTML frontend. No separate frontend server is needed.

---

## Features

### Module 1 — Child Growth Monitoring
- WHO-standard **Z-score calculations** for weight, height, and head circumference
- Covers ages **0 to 60 months** with separate charts for boys and girls
- Classifies results as Normal, Underweight, Stunted, Overweight, or Obese
- Provides **actionable dietary guidance** for each classification
- Detects **Failure to Thrive (FTT)** risk automatically

### Module 2 — Developmental Milestone Tracking
- Based on the **Trivandrum Developmental Screening Chart (TDSC)** — 0 to 3 years
- Covers 27 milestones across 4 domains: Gross Motor, Fine Motor, Language, Social
- Adjusts age for **premature babies** using corrected gestational age
- Flags missed milestones with **domain-specific stimulation tips**
- Detects isolated language delay and recommends hearing screening
- Lists age-appropriate absolute **red flags**

### Module 3 — Postpartum Support and PPD Screening
- **AI Chatbot** powered by Groq (Llama 3.3 70B) covering:
  - Breastfeeding guidance (exclusive, complementary, latch issues, engorgement)
  - Postpartum recovery (vaginal and C-section)
  - Indian postpartum nutrition (ragi, moringa, gond ke laddoo, methi laddoo)
  - Emergency warning signs with 108/hospital escalation
  - Mental health support and emotional validation
- **Edinburgh Postnatal Depression Scale (EPDS)** — validated 10-question self-screening
- Real-time **PPD risk scoring** (Low / Medium / High / Crisis)
- **Automatic wellness alerts** triggered by distress keywords or high EPDS scores
- Partner/guardian email alert system via SMTP
- In-session **risk tracking** across multiple chat messages

### Authentication System
- Email and password registration and login
- Secure session tokens (UUID-based), rotated on each login
- Profile management — baby details, delivery type, breastfeeding status, partner info

---

## Tech Stack

| Layer             | Technology                                        |
|-------------------|---------------------------------------------------|
| Backend           | Python 3.11+, FastAPI, Uvicorn                    |
| AI / LLM          | Groq API — llama-3.3-70b-versatile                |
| Frontend          | Vanilla HTML5, CSS3, JavaScript (ES6+)            |
| Fonts             | Google Fonts — Cormorant Garamond, DM Sans        |
| HTTP Client       | httpx (async)                                     |
| Data Validation   | Pydantic v2                                       |
| Email Alerts      | Python smtplib (SMTP/TLS)                         |
| Clinical Standards| WHO Child Growth Standards, TDSC, EPDS            |

---

## Project Structure

```
Neocare-real/
|
|-- .env                        <-- Your local secrets (never commit this)
|-- .env.example                <-- Template for .env
|-- .gitignore
|-- requirements.txt            <-- Python dependencies
|-- README.md
|
|-- backend/
|   |-- main.py                 <-- FastAPI app entry point and all route definitions
|   |-- modules/
|       |-- __init__.py
|       |-- growth.py           <-- Module 1: WHO Z-score growth analysis
|       |-- milestones.py       <-- Module 2: TDSC milestone evaluation
|       |-- postpartum.py       <-- Module 3: AI chat, EPDS screening, alerts
|
|-- frontend/
    |-- index.html              <-- Landing / Home page
    |-- login.html              <-- Login and Registration page
    |-- dashboard.html          <-- User dashboard
    |-- growth.html             <-- Growth monitoring page
    |-- milestones.html         <-- Developmental milestones page
    |-- postpartum.html         <-- Postpartum support and AI chat page
    |-- css/
    |   |-- style.css           <-- Shared design system and theme tokens
    |-- js/
        |-- growth.js           <-- Growth chart rendering and WHO analysis
        |-- milestones.js       <-- TDSC checklist and timeline UI
        |-- postpartum.js       <-- Chat UI, EPDS form, partner setup
```

---

## Prerequisites

Make sure the following are installed on your system:

- **Python 3.11 or higher** — https://www.python.org/downloads/
- **pip** (bundled with Python)
- A free **Groq API key** — https://console.groq.com/keys
- (Optional) A Gmail account with an **App Password** for email alerts

Verify your Python version:
```bash
python --version
# Should output: Python 3.11.x or higher
```

---

## Installation and Setup

### Step 1 — Clone the Repository
```bash
git clone https://github.com/your-username/neocare.git
cd neocare
```

### Step 2 — Install Python Dependencies
Run this from the project root:
```bash
pip install -r requirements.txt
```

This installs: `fastapi`, `uvicorn[standard]`, `httpx`, `pydantic`, `python-multipart`, `python-dotenv`

### Step 3 — Configure Environment Variables
Copy the example env file:
```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` in any text editor and fill in your Groq API key and optional SMTP settings.

### Step 4 — Start the Server
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Step 5 — Open the App in Your Browser
```
http://127.0.0.1:8000
```

> **Important:** Do NOT open the HTML files by double-clicking them.
> They must be served through the FastAPI backend.
> Always use `http://127.0.0.1:8000`

---

## Environment Variables

Create a `.env` file in the **project root** (`Neocare-real/`) based on `.env.example`:

```env
# Required for the AI chatbot to work
# Get your free key at: https://console.groq.com/keys
GROQ_API_KEY=gsk_your_groq_key_here

# Optional — enables partner/guardian email alerts for PPD risk
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_16char_app_password
SMTP_FROM=your_email@gmail.com
```

| Variable      | Required | Description                                         |
|---------------|----------|-----------------------------------------------------|
| GROQ_API_KEY  | Yes      | Groq API key for the AI chatbot                     |
| SMTP_HOST     | No       | SMTP server hostname                                |
| SMTP_PORT     | No       | SMTP port (usually 587 for TLS)                     |
| SMTP_USER     | No       | Your email address                                  |
| SMTP_PASSWORD | No       | Gmail App Password (16 characters, no spaces)       |
| SMTP_FROM     | No       | Sender address (defaults to SMTP_USER if not set)   |

> **Warning:** Never commit your `.env` file. It is already listed in `.gitignore`.

---

## Running the App

### Development mode (auto-reload on file changes)
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Without auto-reload
```bash
cd backend
python main.py
```

### Custom port
```bash
cd backend
uvicorn main:app --reload --port 8080
```

On successful startup you will see:
```
INFO:     Will watch for changes in these directories: ['.../backend']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

Press `Ctrl+C` to stop the server.

> **Note:** The `.env` file is only read at startup. If you change any environment
> variable, you must restart the server for changes to take effect.

---

## Pages and Navigation

| Page               | URL                                   | Description                             |
|--------------------|---------------------------------------|-----------------------------------------|
| Landing Page       | http://127.0.0.1:8000/                | Home page with feature overview         |
| Login / Register   | http://127.0.0.1:8000/login.html      | Create account or sign in               |
| Dashboard          | http://127.0.0.1:8000/dashboard.html  | User profile and health summary         |
| Growth Monitoring  | http://127.0.0.1:8000/growth.html     | WHO growth chart analysis               |
| Milestones         | http://127.0.0.1:8000/milestones.html | TDSC developmental screening            |
| Postpartum Support | http://127.0.0.1:8000/postpartum.html | AI chat and PPD screening               |
| API Docs           | http://127.0.0.1:8000/docs            | Auto-generated interactive Swagger docs |

---

## API Reference

All API endpoints are served under `/api/`.
Interactive Swagger documentation is available at: `http://127.0.0.1:8000/docs`

### Authentication

| Method | Endpoint                   | Description                        |
|--------|----------------------------|------------------------------------|
| POST   | /api/auth/register         | Register a new user account        |
| POST   | /api/auth/login            | Login and receive a session token  |
| GET    | /api/auth/me?token=TOKEN   | Get current user profile           |
| POST   | /api/auth/update-profile   | Update user, baby, or partner info |

**Register — example request body:**
```json
{
  "full_name": "Priya Sharma",
  "email": "priya@example.com",
  "password": "securepassword",
  "baby_name": "Ananya",
  "baby_dob": "2025-06-01",
  "delivery_type": "vaginal",
  "bf_status": "exclusive"
}
```

---

### Growth Monitoring

| Method | Endpoint             | Description                           |
|--------|----------------------|---------------------------------------|
| POST   | /api/growth/analyze  | Analyze child growth via WHO Z-scores |

**Request body:**
```json
{
  "age_months": 6,
  "sex": "girls",
  "weight_kg": 7.3,
  "length_cm": 66.0,
  "hc_cm": 42.5
}
```

Response includes: Z-score, status label (Normal / Underweight / Stunted etc.),
icon indicator, guidance text, and FTT risk flag for each measurement provided.

---

### Milestone Tracking

| Method | Endpoint                                | Description                           |
|--------|-----------------------------------------|---------------------------------------|
| GET    | /api/milestones/checklist?age_months=12 | Get milestone checklist for given age |
| POST   | /api/milestones/evaluate                | Evaluate answered milestone checklist |

**Evaluate — request body:**
```json
{
  "age_months": 12,
  "sex": "girls",
  "premature": false,
  "gestational_age_weeks": null,
  "answers": { "1": true, "2": true, "13": false },
  "regression": false
}
```

---

### Postpartum Support

| Method | Endpoint                     | Description                                |
|--------|------------------------------|--------------------------------------------|
| POST   | /api/chat                    | Send message to the AI chatbot (Groq)      |
| GET    | /api/chat-state?session=ID   | Get session history and wellness score     |
| GET    | /api/ppd-screening/questions | Get the 10 EPDS questions                  |
| POST   | /api/ppd-screening           | Submit EPDS answers and receive risk score |
| POST   | /api/partner-setup           | Register partner/guardian for alerts       |
| GET    | /api/alerts?session=ID       | List wellness alerts for a session         |
| POST   | /api/alerts/trigger          | Manually trigger a wellness alert          |
| GET    | /api/smtp-status             | Check email alert configuration status     |
| POST   | /api/test-alert              | Send a test wellness alert email           |

**Chat — request body:**
```json
{
  "session": "unique-session-id",
  "message": "I am having trouble breastfeeding.",
  "profile": {
    "mother_name": "Priya",
    "baby_age_weeks": 6,
    "delivery_type": "vaginal",
    "bf_status": "exclusive"
  }
}
```

**PPD Screening — request body (answers are 0 to 3 per question):**
```json
{
  "session": "unique-session-id",
  "answers": {
    "0": 0, "1": 1, "2": 0, "3": 1,
    "4": 0, "5": 0, "6": 1, "7": 0,
    "8": 0, "9": 0
  }
}
```

---

## Module Details

### backend/modules/growth.py
Implements the **WHO LMS method** (Box-Cox power transformation) for Z-score calculation.

- Contains WHO reference tables for weight-for-age, length-for-age, and head circumference-for-age
- Covers 0 to 60 months with separate data for boys and girls
- `_zscore(value, L, M, S)` — computes the Z-score using the LMS formula
- `_nearest_age(table, age)` — finds the closest reference age in the WHO table
- `analyze(data)` — main function that calculates and classifies all provided measurements
- Returns: Z-score, status label, icon (green/yellow/red), contextual guidance, and FTT flag

### backend/modules/milestones.py
Implements the **TDSC (Trivandrum Developmental Screening Chart)** evaluation logic.

- 27 milestone items, each with a start age, upper-limit age, and developmental domain
- `get_checklist(age_months)` — returns all milestones relevant to the given age
- `evaluate(data)` — processes answers, applies corrected age for premature babies, and returns:
  - Domain status per area (normal / monitor / flag / not_assessed)
  - Red flag list for milestones missed past their upper-limit age
  - Applicable absolute red flags (hardcoded clinical thresholds, e.g. "no walking by 18 months")
  - Domain-specific stimulation tips (Gross Motor, Fine Motor, Language, Social)
  - Special clinical notes (e.g. isolated language delay triggers ENT referral suggestion)

### backend/modules/postpartum.py
The core module — handles AI chat, PPD screening, risk scoring, and email alerting.

- `_call_groq(messages)` — async function making requests to the Groq Chat Completions API
- `_score(message)` — keyword-based distress detection with emergency and self-harm flags
- `_should_alert(risk_scores)` — determines if cumulative risk warrants a wellness alert
- `_add_alert(session, severity, reason, details)` — creates alerts with 24-hour deduplication
- `_send_email_alert(...)` — sends SMTP email to partner/guardian with alert details
- `_wellness(risk_scores)` — computes a rolling wellness score from recent risk history
- `chat(data)` — orchestrates the full chat flow: score message, update history, call Groq, return reply
- `ppd_screen(data)` — scores EPDS answers (with reversed items), triggers alerts if threshold met
- The system prompt embedded in this module is a comprehensive clinical knowledge base covering
  breastfeeding, postpartum recovery, Indian nutrition traditions, and mental health support

---

## Email Alerts Setup

NeoCare sends wellness alert emails to a registered partner or guardian when:
- EPDS score exceeds the threshold (score >= 10 triggers medium, >= 13 triggers high alert)
- Distress or emergency keywords are detected in the chat

### For Gmail (Recommended)

1. Enable **2-Factor Authentication** on your Google account
2. Go to: https://myaccount.google.com/apppasswords
3. Click **"Create App Password"** — choose app: Mail, device: your OS
4. Copy the 16-character password (example: `abcd efgh ijkl mnop`)
5. Set in your `.env` file:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=abcdefghijklmnop
SMTP_FROM=your_email@gmail.com
```

### For Outlook / Hotmail

```env
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your_email@outlook.com
SMTP_PASSWORD=your_account_password
```

### Verifying Email Setup

After starting the server, check status at:
```
http://127.0.0.1:8000/api/smtp-status
```

Send a test alert email:
```bash
curl -X POST http://127.0.0.1:8000/api/test-alert ^
  -H "Content-Type: application/json" ^
  -d "{"to_email": "partner@example.com", "severity": "medium"}"
```

---

## Troubleshooting

### "Could not import module main"
**Cause:** uvicorn is being run from the wrong directory (project root instead of backend/).

**Fix:** Always `cd` into the `backend` folder before running uvicorn:
```bash
cd E:\Neocare-real\backend
uvicorn main:app --reload --port 8000
```

---

### "Server error 500" on the chatbot
**Cause:** Invalid or missing Groq API key.

**Fix:**
1. Get a new key at https://console.groq.com/keys
2. Update `GROQ_API_KEY` in your `.env` file
3. **Restart the server** — the `.env` is only loaded at startup

---

### Pages not loading or broken layout
**Cause:** Opening HTML files directly from the filesystem (file:// protocol).

**Fix:** Always access the app through the running server: `http://127.0.0.1:8000`

---

### ModuleNotFoundError
**Cause:** Python dependencies are not installed.

**Fix:**
```bash
pip install -r requirements.txt
```

---

### Port 8000 already in use
**Fix:** Run on a different port:
```bash
uvicorn main:app --reload --port 8080
```

---

### Email alerts not sending
**Cause:** `SMTP_USER` or `SMTP_PASSWORD` not configured, or Gmail App Password not set up.

**Fix:** Follow the Email Alerts Setup section above.
Check current status at: `http://127.0.0.1:8000/api/smtp-status`

---

### User data lost after server restart
**Cause:** User accounts are stored in memory — not persisted to disk.

**Note:** This is expected behavior for the current development version.
For production use, integrate a database (PostgreSQL or SQLite).

---

## Security Notes

- `.env` is excluded from git via `.gitignore` — never commit it
- The Groq API key lives only on the server — it is never sent to the browser
- Session tokens are UUID-based and rotated on every login
- CORS is currently set to allow all origins (`*`) — restrict this before any public deployment
- User data is in-memory only — no user data is persisted to disk in the current version
- For cloud deployment (Render, Railway, Heroku), set environment variables through the
  platform's dashboard instead of uploading a `.env` file

---

## Dependencies

| Package           | Purpose                                           |
|-------------------|---------------------------------------------------|
| fastapi           | Web framework for building the REST API           |
| uvicorn[standard] | High-performance ASGI server                      |
| httpx             | Async HTTP client for Groq API requests           |
| pydantic          | Data validation and serialization (v2)            |
| python-multipart  | Form data parsing support for FastAPI             |
| python-dotenv     | Loads .env file into environment variables        |

Install all at once:
```bash
pip install -r requirements.txt
```

---

## Disclaimer

NeoCare is a **screening and support tool only**.
It is **not a diagnostic system** and does not replace professional medical advice.

- Growth chart classifications and milestone evaluations are reference tools to guide
  conversations with healthcare providers, not to diagnose medical conditions.
- The AI chatbot provides general postpartum information based on WHO and TDSC guidelines.
  It is not a substitute for a doctor, lactation consultant, or mental health professional.
- Edinburgh Postnatal Depression Scale (EPDS) results are informational only.
  A high score should prompt consultation with a qualified clinician, not self-diagnosis.
- In any emergency, call **108** or go to the nearest hospital immediately.

---

## License

This project is for educational and healthcare awareness purposes.

---

Built with care for new mothers and their families — NeoCare
