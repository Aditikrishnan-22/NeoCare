"""
NeoCare — FastAPI Backend
Run: uvicorn main:app --reload --port 8000
"""
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from modules import growth, milestones, postpartum

app = FastAPI(title="NeoCare API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
app.mount("/static", StaticFiles(directory="../frontend"), name="static")
# Serve images folder
app.mount("/images", StaticFiles(directory="../frontend/images"), name="images")



# ── IN-MEMORY USER STORE  (replace with DB in production) ──────────
_users: dict[str, dict] = {}   # keyed by email


def _hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ── PYDANTIC SCHEMAS ────────────────────────────────────────────────
class RegisterInput(BaseModel):
    full_name: str
    email: str
    password: str
    phone: Optional[str] = None
    baby_name: Optional[str] = None
    baby_dob: Optional[str] = None        # ISO date string e.g. "2025-08-12"
    delivery_type: Optional[str] = "vaginal"
    bf_status: Optional[str] = "exclusive"


class LoginInput(BaseModel):
    email: str
    password: str


class UpdateProfileInput(BaseModel):
    token: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    baby_name: Optional[str] = None
    baby_dob: Optional[str] = None
    delivery_type: Optional[str] = None
    bf_status: Optional[str] = None
    # Partner / husband details
    partner_name: Optional[str] = None
    partner_email: Optional[str] = None
    partner_phone: Optional[str] = None
    partner_relation: Optional[str] = "husband"
    alert_consent: Optional[bool] = True


def _token_to_user(token: str) -> dict:
    """Resolve a session token to a user dict, or raise 401."""
    for user in _users.values():
        if user.get("token") == token:
            return user
    raise HTTPException(status_code=401, detail="Invalid or expired session token.")


# ── MODULE 0: AUTH ────────────────────────────────────────────────

@app.post("/api/auth/register")
async def register(data: RegisterInput):
    email = data.email.lower().strip()
    if email in _users:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    token = str(uuid.uuid4())
    _users[email] = {
        "id": str(uuid.uuid4()),
        "email": email,
        "password_hash": _hash_pw(data.password),
        "full_name": data.full_name,
        "phone": data.phone,
        "baby_name": data.baby_name,
        "baby_dob": data.baby_dob,
        "delivery_type": data.delivery_type,
        "bf_status": data.bf_status,
        "partner_name": None,
        "partner_email": None,
        "partner_phone": None,
        "partner_relation": "husband",
        "alert_consent": True,
        "token": token,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    u = _users[email]
    return {
        "success": True,
        "token": token,
        "user": {k: v for k, v in u.items() if k != "password_hash"},
    }


@app.post("/api/auth/login")
async def login(data: LoginInput):
    email = data.email.lower().strip()
    user = _users.get(email)
    if not user or user["password_hash"] != _hash_pw(data.password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    # Rotate token on each login
    token = str(uuid.uuid4())
    user["token"] = token
    return {
        "success": True,
        "token": token,
        "user": {k: v for k, v in user.items() if k != "password_hash"},
    }


@app.get("/api/auth/me")
async def me(token: str = Query(...)):
    user = _token_to_user(token)
    return {"user": {k: v for k, v in user.items() if k != "password_hash"}}


@app.post("/api/auth/update-profile")
async def update_profile(data: UpdateProfileInput):
    user = _token_to_user(data.token)
    fields = [
        "full_name", "phone", "baby_name", "baby_dob",
        "delivery_type", "bf_status",
        "partner_name", "partner_email", "partner_phone",
        "partner_relation", "alert_consent",
    ]
    for f in fields:
        val = getattr(data, f)
        if val is not None:
            user[f] = val
    return {"success": True, "user": {k: v for k, v in user.items() if k != "password_hash"}}


# ── MODULE 1: GROWTH ──────────────────────────────────────────

@app.post("/api/growth/analyze")
async def growth_analyze(data: growth.GrowthInput):
    results = growth.analyze(data)
    return {"success": True, "results": results}


# ── MODULE 2: MILESTONES ──────────────────────────────────────

@app.get("/api/milestones/checklist")
async def milestones_checklist(age_months: float):
    return {"milestones": milestones.get_checklist(age_months)}

@app.post("/api/milestones/evaluate")
async def milestones_evaluate(data: milestones.MilestoneInput):
    return milestones.evaluate(data)


# ── MODULE 3: POSTPARTUM ──────────────────────────────────────

@app.post("/api/chat")
async def postpartum_chat(data: postpartum.ChatInput):
    return await postpartum.chat(data)

@app.post("/api/ppd-screening")
async def ppd_screening(data: postpartum.PPDInput):
    return postpartum.ppd_screen(data)

@app.get("/api/ppd-screening/questions")
async def ppd_questions():
    return postpartum.get_epds_questions()

@app.post("/api/partner-setup")
async def partner_setup(data: postpartum.PartnerSetupInput):
    return postpartum.partner_setup(data)

@app.get("/api/chat-state")
async def chat_state(session: str = Query("default")):
    return postpartum.get_chat_state(session)

@app.get("/api/alerts")
async def list_alerts(session: str = Query(None)):
    return postpartum.get_alerts(session)

@app.post("/api/alerts/trigger")
async def trigger_alert(data: postpartum.AlertTriggerInput):
    return postpartum.trigger_alert(data)


@app.get("/api/smtp-status")
async def smtp_status():
    """Check whether SMTP email is configured and active."""
    return {
        "smtp_enabled":  postpartum.SMTP_ENABLED,
        "smtp_host":     postpartum.SMTP_HOST,
        "smtp_port":     postpartum.SMTP_PORT,
        "smtp_user":     postpartum.SMTP_USER if postpartum.SMTP_USER else "(not set)",
        "note": "Set SMTP_USER and SMTP_PASSWORD env vars to enable real email alerts."
    }


class TestAlertInput(BaseModel):
    to_email: str
    severity: str = "medium"


@app.post("/api/test-alert")
async def test_alert(data: TestAlertInput):
    """Send a test wellness alert email — useful for verifying SMTP setup."""
    status = postpartum._send_email_alert(
        to_email=data.to_email,
        severity=data.severity,
        reason="test",
        details="This is a test alert from NeoCare to verify your SMTP configuration is working correctly.",
        mother_name="Test User",
    )
    return {
        "success": status == "sent",
        "sent_status": status,
        "to": data.to_email,
        "note": "If sent_status is 'no_config', set SMTP_USER and SMTP_PASSWORD environment variables."
    }


# ── SERVE FRONTEND ────────────────────────────────────────────

@app.get("/")
async def serve_index():
    return FileResponse("../frontend/login.html")

@app.get("/{page}.html")
async def serve_page(page: str):
    return FileResponse(f"../frontend/{page}.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)