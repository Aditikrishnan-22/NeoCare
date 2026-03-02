# 🌿 NeoCare — AI Postpartum & Child Health Monitoring System

> An AI-powered system supporting new mothers and monitoring newborn growth and development.

---

## 📁 Project Structure

```
neocare/
│
├── backend/
│   ├── main.py                  ← FastAPI entry point
│   ├── requirements.txt
│   └── modules/
│       ├── __init__.py
│       ├── growth.py            ← Module 1: WHO Z-score logic
│       ├── milestones.py        ← Module 2: TDSC evaluation
│       └── postpartum.py        ← Module 3: Chatbot + PPD screening
│
└── frontend/
    ├── index.html               ← Home / Landing page
    ├── growth.html              ← Module 1 page
    ├── milestones.html          ← Module 2 page
    ├── postpartum.html          ← Module 3 page
    ├── css/
    │   └── style.css            ← Shared design system
    └── js/
        ├── growth.js            ← Growth charts & analysis
        ├── milestones.js        ← TDSC checklist & timeline
        └── postpartum.js        ← Chat & PPD screening
```

---

## 🚀 Quick Start

### 1. Install Python dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Start the backend server
```bash
cd backend
python main.py
```

### 3. Open the app
```
http://localhost:8000
```

---

## 🔑 Groq API Key (for Chatbot)
1. Visit console.groq.com — free account
2. Generate an API key
3. Paste it in the Postpartum page API key field

---

## ⚠️ Disclaimer
NeoCare is a screening and support tool only — not a diagnostic system.
Always consult a qualified healthcare professional for medical concerns.