"""
NeoCare — Module 3: Postpartum Care
File: backend/modules/postpartum.py

Requires:  pip install httpx
Env var:   GROQ_API_KEY=gsk_...  (set in shell or .env — NEVER in frontend)
"""

from __future__ import annotations

import os
import re
import smtplib
import uuid
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Literal, Optional

import httpx
from pydantic import BaseModel

# ══════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════
GROQ_API_KEY = os.getenv("GROQ_API_KEY")   # Set this in your .env file
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.3-70b-versatile"

# ── SMTP Email Config ───────────────────────────────────
SMTP_HOST     = os.getenv("SMTP_HOST",  "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER     = os.getenv("SMTP_USER")      # Set this in your .env file
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  # Set this in your .env file (Gmail App Password)
SMTP_FROM     = os.getenv("SMTP_FROM",  SMTP_USER or "")
SMTP_ENABLED  = bool(SMTP_USER and SMTP_PASSWORD)

# ══════════════════════════════════════════════
#  IN-MEMORY STORES  (replace with DB as needed)
# ══════════════════════════════════════════════
_sessions: dict[str, dict] = {}
_alerts:   list[dict]      = []


def _get_session(sid: str) -> dict:
    if sid not in _sessions:
        _sessions[sid] = {"history": [], "risk_scores": [], "profile": {}}
    return _sessions[sid]


# ══════════════════════════════════════════════
#  PYDANTIC SCHEMAS
# ══════════════════════════════════════════════
class MotherProfile(BaseModel):
    mother_name:    Optional[str] = None
    baby_age_weeks: Optional[int] = None
    delivery_type:  Optional[Literal["vaginal", "c-section"]] = "vaginal"
    bf_status:      Optional[str] = "exclusive"


class PartnerInfo(BaseModel):
    name:    Optional[str] = None
    email:   Optional[str] = None
    phone:   Optional[str] = None
    consent: bool = True


class ChatInput(BaseModel):
    session: str = "default"
    message: str
    profile: Optional[MotherProfile] = None


class PPDInput(BaseModel):
    session: str = "default"
    answers: dict[str, int]   # {"0": 1, "1": 0, ...}


class PartnerSetupInput(BaseModel):
    session: str = "default"
    partner: PartnerInfo


class AlertTriggerInput(BaseModel):
    session:  str = "default"
    severity: Literal["medium", "high"] = "medium"
    reason:   str = "manual"
    details:  str = ""


# ══════════════════════════════════════════════
#  SYSTEM PROMPT  (Groq only — never sent to browser)
# ══════════════════════════════════════════════
_SYSTEM = """You are NeoCare, a compassionate postpartum AI support assistant for new mothers in India.

PERSONA: Warm, calm, empathetic — like a knowledgeable elder sister who is also a healthcare worker.
Validate emotions first, then guide practically.

HARD RULES:
1. You are NOT a doctor. NEVER diagnose. Use "may be", "could be", "consider seeing a doctor".
2. EMERGENCY SIGNS — respond with IMMEDIATE urgency if mentioned:
   • Heavy bleeding (soaking >1 pad/hour), large foul-smelling clots
   • Fever >38°C in mother OR in baby under 3 months
   • Severe headache, blurred vision, chest pain, breathing difficulty
   • Thoughts of harming self or baby
   • Baby not feeding 6+ hours, blue lips, seizures, floppiness, unresponsive
   • Wound redness/pus/foul smell, swollen hot red leg (DVT)
   → State clearly: "Please seek emergency help immediately — call 108 or go to the nearest hospital."
3. Emotional distress → empathy FIRST, always. Then practical steps.
4. Format every response:
   **[Topic Title]**
   Brief explanation (2–3 lines)
   • Action point 1
   • Action point 2
   • Action point 3
   🏥 **Seek help if:** [specific warning — only when clinically relevant]
   [Short warm closing question]
5. Be concise unless the user asks for more detail.
6. Be specific with empathy. Say "Being woken every 2 hours for weeks is genuinely exhausting." Not just "I understand."

════════════════════════════════════
BREASTFEEDING
════════════════════════════════════
EXCLUSIVE BREASTFEEDING (0–6 months):
- No other food or fluid — not even water. Breast milk is 88% water.
- Colostrum (days 1–4): thick, yellowish, full of IgA antibodies. NEVER discard.
- Foremilk (start of feed): watery, quenches thirst. Hindmilk (end): fat-rich for energy. Empty one breast fully before switching.
- Feed on demand: 8–12 times per 24 hours. Frequent feeding builds and maintains supply.

LATCH (root cause of most problems):
- Good latch: mouth wide open, lower lip everted, chin touching breast, more upper areola visible.
- Poor latch → pain, cracked nipples, low supply, gassy baby. Fix latch FIRST for any problem.
- Fix: break suction gently with little finger, bring baby TO breast (not breast to baby).
- Positions: cradle, cross-cradle, football hold (good post C-section), side-lying (good for night).

COMMON PROBLEMS:
- Engorgement (days 3–5): warm compress 2 min before feed, feed very frequently, cold compress after. Hand-express to soften areola so baby can latch.
- Cracked/sore nipples: apply expressed breast milk and let air-dry. Lanolin cream helps. Fix latch (80% of cause). Never use soap on nipples.
- Blocked duct: hard tender lump. Warm compress + massage toward nipple + feed frequently from that breast.
- Mastitis: hard red area + flu-like fever. CONTINUE FEEDING (safe for baby). Warm compress, rest, fluids. See doctor within 24h if no improvement — may need antibiotics.
- Low milk supply (true vs perceived): True = baby losing weight + fewer than 6 wet diapers/day. Most "low supply" is perceived. Feed more frequently — supply matches demand. Avoid formula top-ups unless medically indicated (reduces demand).
- Galactagogues (milk boosters): methi/fenugreek seeds, moringa/drumstick leaves, oats, garlic, fennel seeds. Most important booster: frequent breast emptying.
- Nipple confusion: avoid bottles/pacifiers in first 4–6 weeks. Use cup, paladai or spoon if supplementing.

COMPLEMENTARY FEEDING (from 6 months):
- One food at a time, soft mashed texture. 3–4 feeds/day (6–11m), 4–5 feeds/day (12–24m).
- Energy density: add ghee/oil to increase calories without adding bulk. Use thick gruels not thin dal water. Amylase-rich/malted grains reduce viscosity.

════════════════════════════════════
POSTPARTUM RECOVERY
════════════════════════════════════
VAGINAL DELIVERY:
- Lochia (normal): bright red days 1–4, pink/brown days 5–10, yellow/white days 10–21. Clots up to plum size are normal in first 24h.
- ABNORMAL: soaking more than 1 pad/hour, large clots with foul smell, fever → emergency.
- Perineal pain: sitz bath (warm water) 2–3x/day, keep clean and dry, ice pack first 24h, paracetamol as needed.
- Afterpains (cramping during feeding, days 2–5): normal — uterus shrinking back. More intense with second+ babies.

C-SECTION RECOVERY:
- Wound: keep dry 24–48h, then clean gently with water. Watch for: redness spreading, swelling, pus, foul smell, wound edges separating.
- No lifting more than 2–3 kg for 6 weeks. Support incision when coughing/laughing/sneezing.
- Numbness and pulling sensation around incision: normal, usually resolves over months.
- No driving for 4–6 weeks. Pain normal up to 4–6 weeks.

GENERAL RECOVERY:
- Hair loss (months 3–6): telogen effluvium — hormonally triggered shedding. Peaks at 3–4 months, resolves by 12 months. Iron and protein help recovery.
- Night sweats: normal — estrogen/progesterone dropping. Wear light clothing, stay hydrated.
- Joint pain: relaxin hormone remains elevated while breastfeeding. Normal.
- Kegel exercises: start as soon as comfortable after delivery. Helps bladder leakage.
- Constipation: increase fiber, fluids, gentle movement. Avoid straining. Stool softener safe if needed.

DANGER SIGNS — always refer urgently:
- Heavy bleeding (>1 pad/hr), large clots + foul smell
- Fever >38°C
- Wound infection (redness, pus, opening)
- Swollen, hot, painful leg (DVT)
- Severe headache, visual disturbances, chest pain (preeclampsia/PE)
- Thoughts of self-harm or harming baby

════════════════════════════════════
POSTPARTUM NUTRITION
════════════════════════════════════
ENERGY: Breastfeeding adds ~500 kcal/day to baseline needs.
- Carbohydrates (55–60% energy): whole grains — ragi, oats, brown rice, whole wheat.
- Proteins (10–12% energy): egg (highest biological value), dal, paneer, fish, chicken. Mix cereals + pulses (e.g. rice + dal) for complete protein profile.
- Fats (25–30% energy): include omega-3 EFAs (EPA/DHA) — critical for baby's brain development through breast milk. Sources: fatty fish (best), walnuts, flaxseeds, chia. AVOID trans fats (vanaspati, packaged snacks, junk food).

KEY MICRONUTRIENTS:
- Iron: ragi, spinach, meat, egg yolk, fortified cereals. Pair with Vitamin C (citrus, tomatoes, amla) — doubles absorption. Avoid tea/coffee within 1hr of iron-rich meals.
- Calcium: 3 dairy servings/day, OR ragi, sesame seeds (til), leafy greens. Baby draws calcium from mother's bones if diet is insufficient.
- Vitamin D: 30 min morning sunlight. Eggs, fatty fish. Most Indian mothers are deficient — ask doctor.
- Iodine: iodized salt, dairy, eggs, seafood. Critical for baby's thyroid and brain development through milk.
- Hydration: 8–12 glasses water/day while breastfeeding. Coconut water, buttermilk, soups all count.

INDIA-SPECIFIC RECOVERY FOODS:
- Sathu maavu / ragi porridge: calorie-dense, iron-rich, excellent postpartum food
- Gond ke laddoo (edible gum): strengthens joints and back after delivery
- Methi laddoo: galactagogue + joint support
- Drumstick leaf (moringa) soup: iron + calcium + milk-boosting
- Warm moong dal khichdi: easy to digest, balanced nutrition

AVOID:
- Caffeine >200mg/day (max 2 small cups) — passes into milk, can irritate baby
- Alcohol: no safe amount while breastfeeding
- High-mercury fish: swordfish, shark, king mackerel

════════════════════════════════════
NEWBORN CARE
════════════════════════════════════
NORMAL — don't worry about:
- Hiccups: normal, very frequent in newborns. No treatment needed.
- Sneezing: clearing nasal passages, not a cold sign.
- Crossed eyes in first weeks: eye muscles still developing, resolves by 3 months.
- Fontanelle pulsing: normal. ABNORMAL if bulging (pressure) or sunken (dehydration).
- Skin peeling (first 2 weeks): vernix removal. No lotions needed.
- Milia (white dots on nose), baby acne (weeks 2–4): hormonal, resolve on their own.

JAUNDICE:
- Physiological (normal): peaks days 3–5, resolves by day 14 in term babies. Yellow skin/eyes.
- Management: breastfeed 8–12x/day, 30 min indirect morning sunlight.
- SEEK URGENT CARE: jaundice within 24h of birth, spreads to palms/soles, baby very sleepy or poor feeding — may need phototherapy.
- Breast milk jaundice: extends to week 6. Usually benign. Continue breastfeeding unless doctor says otherwise.

FEVER:
- Any temp >38°C rectally in baby under 3 months = MEDICAL EMERGENCY → hospital immediately.
- Older babies: persistent fever >48h or >39°C → see doctor.

CRYING:
- Normal: 1–3 hours total/day. Evening cluster crying common weeks 2–8.
- Check in order: hunger → wet diaper → gas/colic → temperature → needs holding.
- Gas relief: bicycle legs, gentle clockwise belly massage, burp position after every feed.
- Colic: >3h/day, >3 days/week, >3 weeks. Resolves by 3–4 months. Not dangerous.

NOT FEEDING / LETHARGIC:
- Refusing 2+ consecutive feeds → see a doctor.
- <6 wet diapers/day in newborn → possible dehydration/low intake → urgent.
- Floppy, unresponsive, blue-tinged → emergency.

SAFE SLEEP (SIDS prevention):
- Always on BACK on firm, flat surface. No pillows, loose blankets, stuffed toys in sleep space.
- Comfortable room temperature — not too warm. Smoke-free environment.
- Avoid co-sleeping on sofa/armchair.

KANGAROO MOTHER CARE (KMC):
- Prolonged skin-to-skin contact: prevents hypothermia, promotes weight gain, boosts breastfeeding.
- Especially vital for low birth weight (<2500g) and premature babies. As effective as incubator care.
- Also helps with bonding and maternal oxytocin.

UMBILICAL CORD:
- Falls off in 7–21 days. Keep DRY. Fold diaper below it. Clean with cotton + water only.
- See doctor if: redness spreads onto belly skin, pus, foul smell.

════════════════════════════════════
EMOTIONAL WELLBEING & PPD
════════════════════════════════════
BABY BLUES (days 2–5):
- Crying, mood swings, anxiety, irritability, feeling overwhelmed. Affects 80% of mothers.
- Cause: massive hormone drop (estrogen, progesterone) after delivery.
- Resolves on its own by day 10–14. Family support is key. Not PPD.

POSTPARTUM DEPRESSION (PPD):
- Affects 10–20% of mothers. Often peaks weeks 2–6 but can develop up to 1 year after birth.
- Signs: persistent sadness or emotional numbness lasting >2 weeks, difficulty bonding with baby, feeling like a "bad mother", hopelessness, loss of interest in activities, exhaustion beyond normal tiredness, panic attacks, not wanting to be alive.
- Important: PPD is NOT a personal failure. It is a medical condition caused by hormonal, neurological, and social factors. Fully treatable.
- Treatment: therapy (CBT is most evidence-based), support groups, medication (safe-for-breastfeeding options exist).

POSTPARTUM ANXIETY (PPA):
- Racing thoughts, constant "what if" worries, panic attacks, inability to sleep even when baby sleeps.
- Very common — often more common than PPD. Frequently undiagnosed. Fully treatable.

POSTPARTUM PSYCHOSIS (rare — emergency):
- Rapid mood swings, confusion, hallucinations, paranoia, not sleeping at all.
- Needs immediate medical care → call 108.

WHAT HELPS (evidence-based):
- Social support: most powerful protective factor. Ask for help explicitly, not just "I'm fine."
- Rest in any form — even lying down with eyes closed counts.
- Gentle movement when medically cleared — even a 15-minute walk significantly reduces symptoms.
- Skin-to-skin with baby: releases oxytocin, directly counteracts anxiety.
- Talking — to partner, mother, friend, therapist, or support group.
- Being told "you are doing a good job" matters more than most people realize.

INDIA CRISIS RESOURCES:
- iCall (TISS): 9152987821 (Mon–Sat, 8am–10pm, free, confidential)
- Vandrevala Foundation: 1860-2662-345 (24/7, free, confidential)
- Mpower: 1800-120-820050
- If self-harm thoughts: → "Please call iCall right now: 9152987821. You deserve support and care."

CHILD NUTRITION (when mothers ask about baby feeding after 6 months):
- First 1000 days (conception to age 2): critical window. Deficits are very hard to reverse.
- Protein RDA: 17g/day (1–3y), 20g/day (4–6y), 30g/day (7–9y).
- Fat: 25–30% of energy — include EFAs (EPA/DHA) for brain development.
- Undernutrition: Underweight (low weight-for-age), Stunting (low height-for-age = chronic), Wasting (low weight-for-height = acute).
- SAM: MUAC <11.5cm or weight-for-height < -3SD or bipedal edema → refer to hospital.
- Government support: ICDS (Anganwadi centers), POSHAN Abhiyaan."""


# ══════════════════════════════════════════════
#  RISK DETECTION ENGINE  (pure Python regex — no AI)
# ══════════════════════════════════════════════
_EMERGENCY_PAT = [re.compile(p, re.I) for p in [
    r"heavy bleeding", r"soaking.{0,10}pad", r"chest pain",
    r"can.?t breathe", r"difficulty breath", r"seizure", r"convuls",
    r"thoughts? of (harming|hurting|killing)",
    r"(harm|kill|hurt) (myself|my baby|the baby)",
    r"want to (die|end it|not be here)",
    r"suicidal", r"end my life", r"self.?harm",
    r"baby not feeding", r"baby.*fever", r"blue lips",
    r"baby.*not responding",
]]
_HIGH_PAT = [re.compile(p, re.I) for p in [
    r"i feel hopeless", r"feel hopeless", r"no hope",
    r"i can.?t do this", r"can.?t cope",
    r"want to disappear", r"wish i wasn.?t here",
    r"hate myself", r"i.?m worthless", r"i.?m a failure",
    r"regret (having|the baby)", r"not bonded",
    r"don.?t love my baby", r"feel nothing for",
    r"don.?t want to be a mother", r"better off without me",
    r"no reason to live", r"can.?t go on",
    r"falling apart", r"breaking down", r"i give up",
]]
_MED_PAT = [re.compile(p, re.I) for p in [
    r"keep crying", r"always crying", r"crying every day",
    r"feel(ing)? alone", r"so alone",
    r"nobody (cares|helps|understands)",
    r"overwhelmed", r"too much", r"can.?t handle",
    r"so anxious", r"constant anxiety", r"panic",
    r"can.?t sleep", r"not sleeping", r"no sleep",
    r"bad mother", r"failing as a mother", r"not a good mother",
    r"feel(ing)? numb", r"feel(ing)? empty", r"so exhausted",
    r"no support", r"husband doesn.?t help", r"nobody helps",
]]
_PROTECT_PAT = [re.compile(p, re.I) for p in [
    r"feeling better", r"much better", r"good support",
    r"husband helps", r"mother helps", r"family helps",
    r"doing okay", r"getting better", r"improving",
]]
_SELFHARM_PAT = re.compile(
    r"harm|kill|hurt|suicidal|end my life|self.?harm", re.I
)


def _score(text: str) -> tuple[int, bool, bool]:
    """(score 0-100, is_emergency, is_self_harm)"""
    is_emergency = any(r.search(text) for r in _EMERGENCY_PAT)
    is_self_harm = is_emergency and bool(_SELFHARM_PAT.search(text))
    score = 0
    for r in _HIGH_PAT:
        if r.search(text): score += 35
    for r in _MED_PAT:
        if r.search(text): score += 15
    for r in _PROTECT_PAT:
        if r.search(text): score = max(0, score - 10)
    return min(100, score), is_emergency, is_self_harm


def _should_alert(risk_scores: list[dict]) -> tuple[bool, str, str]:
    """(should_trigger, severity, reason)"""
    now   = datetime.now(timezone.utc).timestamp()
    day   = 86_400
    r7    = [r for r in risk_scores if now - r["ts"] < 7 * day]
    r3    = [r for r in risk_scores if now - r["ts"] < 3 * day]
    high7 = sum(1 for r in r7 if r["score"] >= 60)
    med7  = sum(1 for r in r7 if r["score"] >= 30)
    high3 = sum(1 for r in r3 if r["score"] >= 60)
    if high3 >= 2: return True, "high",   "trend"
    if high7 >= 3: return True, "high",   "trend"
    if med7  >= 5: return True, "medium", "trend"
    return False, "", ""


def _build_email_html(severity: str, reason: str, details: str, mother_name: str = "") -> str:
    """Build a clean HTML alert email body."""
    color  = "#b8413a" if severity == "high" else "#c47b2a"
    emoji  = "🔴" if severity == "high" else "🟡"
    label  = "High Concern" if severity == "high" else "Moderate Concern"
    name   = mother_name or "the mother you are supporting"
    return f"""
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8" />
<style>
  body {{ font-family: 'DM Sans', Arial, sans-serif; background:#fdf8f4; color:#2c1f1a; margin:0; padding:0; }}
  .wrap {{ max-width:560px; margin:32px auto; background:#fffbf9; border-radius:16px;
            border:1px solid #f0d8d4; overflow:hidden;
            box-shadow:0 4px 24px rgba(44,31,26,.10); }}
  .header {{ background:linear-gradient(135deg,{color},{color}cc); padding:28px 32px; text-align:center; }}
  .header h1 {{ color:white; font-size:22px; margin:0; font-weight:700; }}
  .header p  {{ color:rgba(255,255,255,.85); font-size:13px; margin:6px 0 0; }}
  .body {{ padding:28px 32px; }}
  .badge {{ display:inline-block; background:{color}18; border:1.5px solid {color}44; color:{color};
             border-radius:100px; padding:5px 16px; font-size:12px; font-weight:700;
             letter-spacing:.5px; text-transform:uppercase; margin-bottom:18px; }}
  .detail-box {{ background:#f9ece9; border-left:4px solid {color}; border-radius:0 10px 10px 0;
                  padding:14px 18px; font-size:14px; line-height:1.7; margin:16px 0; }}
  .resource {{ background:#edf4ee; border-radius:12px; padding:14px 18px;
                font-size:13px; line-height:1.8; color:#2d5a2d; margin-top:18px; }}
  .footer {{ background:#f5efeb; padding:18px 32px; font-size:11px; color:#b09893; line-height:1.7; }}
  .footer a {{ color:#c4736a; text-decoration:none; }}
</style></head>
<body>
<div class="wrap">
  <div class="header">
    <h1>{emoji} NeoCare Wellness Alert</h1>
    <p>This message was generated automatically by the NeoCare system.</p>
  </div>
  <div class="body">
    <div class="badge">{label} · {reason}</div>
    <p style="font-size:15px;line-height:1.75;margin:0 0 14px">
      Hi, you are receiving this because you are listed as a trusted person for <strong>{name}</strong>
      on NeoCare, and our system has detected repeated emotional distress signals in recent conversations.
    </p>
    <div class="detail-box">
      <strong>Alert Detail:</strong><br/>{details}
    </div>
    <p style="font-size:13px;color:#7a5e58;line-height:1.7;margin:14px 0 0">
      <strong>What this means:</strong> NeoCare monitors conversation patterns for signs of postpartum
      distress. This alert does <em>not</em> share any chat messages — only a wellness signal.
      Please gently check in with {name} and encourage her to seek professional support if needed.
    </p>
    <div class="resource">
      <strong>📞 India Crisis Resources:</strong><br/>
      iCall (TISS): <strong>9152987821</strong> (Mon–Sat, 8am–10pm, free, confidential)<br/>
      Vandrevala Foundation: <strong>1860-2662-345</strong> (24/7 free)
    </div>
  </div>
  <div class="footer">
    🌿 NeoCare — AI-powered postpartum support tool &nbsp;·&nbsp;
    This alert was sent because you are a registered guardian contact. &nbsp;
    <a href="mailto:{SMTP_FROM}">Contact support</a><br/>
    <em>NeoCare never shares chat messages. Privacy is paramount.</em>
  </div>
</div>
</body></html>"""


def _send_email_alert(to_email: str, severity: str, reason: str, details: str,
                      mother_name: str = "") -> str:
    """Send SMTP email. Returns 'sent', 'failed', or 'no_config'."""
    if not SMTP_ENABLED:
        return "no_config"
    if not to_email or "@" not in to_email:
        return "no_email"
    try:
        msg = MIMEMultipart("alternative")
        label = "HIGH CONCERN" if severity == "high" else "MODERATE CONCERN"
        msg["Subject"] = f"[NeoCare Wellness Alert] {label} — Please check in"
        msg["From"]    = SMTP_FROM
        msg["To"]      = to_email

        # Plain text fallback
        plain = (
            f"NeoCare Wellness Alert — {label}\n"
            f"Reason: {reason}\n"
            f"Detail: {details}\n\n"
            f"Please gently check in with {mother_name or 'the mother you support'}.\n"
            f"Crisis: iCall 9152987821 · Vandrevala 1860-2662-345"
        )
        html = _build_email_html(severity, reason, details, mother_name)

        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html,  "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, to_email, msg.as_string())

        print(f"\n✅ EMAIL SENT [{severity.upper()}] → {to_email}")
        return "sent"

    except Exception as e:
        print(f"\n⚠️  EMAIL FAILED: {e}")
        return "failed"


def _add_alert(session: str, severity: str, reason: str, details: str = "") -> dict | None:
    """Rate-limited: 1 alert per session per 24 h. Sends real email if SMTP configured."""
    now = datetime.now(timezone.utc).timestamp()
    if any(a["mother_id"] == session and now - a["created_at"] < 86_400 for a in _alerts):
        return None

    # Retrieve partner/guardian email stored during partner-setup
    sess         = _get_session(session)
    partner      = sess["profile"].get("partner", {})
    guardian_email = partner.get("email") if isinstance(partner, dict) else None
    mother_name  = sess["profile"].get("mother_name", "")
    consent      = partner.get("consent", True) if isinstance(partner, dict) else True

    # Attempt real email delivery
    if consent and guardian_email:
        sent_status = _send_email_alert(guardian_email, severity, reason, details, mother_name)
    elif not consent:
        sent_status = "consent_off"
    else:
        sent_status = "no_email"
        print(f"\n🚨 ALERT [{severity.upper()}] session={session} — no guardian email set")

    print(f"   Reason : {reason}")
    print(f"   Details: {details}")
    print(f"   Status : {sent_status}\n")

    entry = {
        "id":          str(uuid.uuid4()),
        "mother_id":   session,
        "severity":    severity,
        "reason":      reason,
        "details":     details,
        "created_at":  now,
        "sent_status": sent_status,
    }
    _alerts.append(entry)
    return entry


def _wellness(risk_scores: list[dict]) -> dict:
    recent = risk_scores[-6:] if risk_scores else []
    avg    = round(sum(r["score"] for r in recent) / len(recent)) if recent else 0
    level  = "high" if avg >= 60 else "medium" if avg >= 30 else "low"
    label  = "High Concern 🔴" if level == "high" else "Monitor 🟡" if level == "medium" else "All Good 🟢"
    return {"score": avg, "level": level, "label": label}


# ══════════════════════════════════════════════
#  GROQ API CALL  (async — key on server only)
# ══════════════════════════════════════════════
async def _call_groq(messages: list[dict]) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY environment variable is not set.")
    payload = {
        "model":       GROQ_MODEL,
        "max_tokens":  900,
        "temperature": 0.65,
        "messages":    [{"role": "system", "content": _SYSTEM}] + messages,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            GROQ_URL,
            json=payload,
            headers={
                "Content-Type":  "application/json",
                "Authorization": f"Bearer {GROQ_API_KEY}",
            },
        )
    if resp.status_code != 200:
        err = resp.json().get("error", {})
        raise RuntimeError(err.get("message", f"Groq HTTP {resp.status_code}"))
    return resp.json()["choices"][0]["message"]["content"]


# ══════════════════════════════════════════════
#  ENDPOINT HANDLERS
# ══════════════════════════════════════════════

async def chat(data: ChatInput) -> dict:
    """POST /api/chat"""
    sess = _get_session(data.session)
    if data.profile:
        sess["profile"].update(data.profile.model_dump(exclude_none=True))
    p = sess["profile"]
    ctx = (
        f"[Context: Baby {p.get('baby_age_weeks','?')} weeks | "
        f"Delivery: {p.get('delivery_type','?')} | "
        f"BF: {p.get('bf_status','?')} | "
        f"Mother: {p.get('mother_name','her')}]"
    )

    score, is_emergency, is_self_harm = _score(data.message)
    if score > 0 or is_emergency:
        sess["risk_scores"].append({
            "score": 100 if is_emergency else score,
            "ts":    datetime.now(timezone.utc).timestamp(),
        })

    alert_triggered = False
    if is_emergency or is_self_harm:
        entry = _add_alert(data.session, "high", "self-harm keyword",
                           "Emergency/self-harm keywords detected in conversation.")
        alert_triggered = entry is not None
    else:
        should, sev, reason = _should_alert(sess["risk_scores"])
        if should:
            entry = _add_alert(data.session, sev, reason,
                               f"Distress signals across {len(sess['risk_scores'])} messages.")
            alert_triggered = entry is not None

    sess["history"].append({"role": "user", "content": ctx + "\n" + data.message})
    reply = await _call_groq(sess["history"][-12:])
    sess["history"].append({"role": "assistant", "content": reply})

    return {
        "reply":           reply,
        "is_emergency":    is_emergency,
        "is_self_harm":    is_self_harm,
        "alert_triggered": alert_triggered,
        "wellness":        _wellness(sess["risk_scores"]),
    }


# ── EPDS ──────────────────────────────────────
_EPDS_Q = [
    {"id":0, "q":"I have been able to laugh and see the funny side of things.",      "reversed":True,  "opts":["As much as I always could","Not quite so much now","Definitely not so much now","Not at all"]},
    {"id":1, "q":"I have looked forward with enjoyment to things.",                  "reversed":True,  "opts":["As much as I ever did","Rather less than I used to","Definitely less than I used to","Hardly at all"]},
    {"id":2, "q":"I have blamed myself unnecessarily when things went wrong.",        "reversed":False, "opts":["No, never","Not very often","Yes, some of the time","Yes, most of the time"]},
    {"id":3, "q":"I have been anxious or worried for no good reason.",               "reversed":False, "opts":["No, not at all","Hardly ever","Yes, sometimes","Yes, very often"]},
    {"id":4, "q":"I have felt scared or panicky for no very good reason.",           "reversed":False, "opts":["No, not at all","No, not much","Yes, sometimes","Yes, quite a lot"]},
    {"id":5, "q":"Things have been getting on top of me.",                           "reversed":False, "opts":["No, I coped as well as ever","No, most of the time I coped","Yes, sometimes I haven't coped as usual","Yes, most of the time I couldn't cope at all"]},
    {"id":6, "q":"I have been so unhappy that I have had difficulty sleeping.",      "reversed":False, "opts":["No, not at all","Not very often","Yes, sometimes","Yes, most of the time"]},
    {"id":7, "q":"I have felt sad or miserable.",                                    "reversed":False, "opts":["No, not at all","Not very often","Yes, quite often","Yes, most of the time"]},
    {"id":8, "q":"I have been so unhappy that I have been crying.",                 "reversed":False, "opts":["No, never","Only occasionally","Yes, quite often","Yes, most of the time"]},
    {"id":9, "q":"The thought of harming myself has occurred to me.",               "reversed":False, "opts":["Never","Hardly ever","Sometimes","Yes, quite often"], "critical":True},
]
_EPDS_GUIDANCE = {
    "low":    "Your score suggests you are coping well emotionally. The postpartum period is still demanding — continue to rest, nourish yourself, and accept all help offered. Check in again in 2 weeks.",
    "medium": "Your score suggests some emotional distress. This is common and does not mean anything is wrong with you. Please talk to someone you trust — your partner, a family member, or your doctor. You are not alone.",
    "high":   "Your score suggests significant emotional distress. Postpartum depression affects 1 in 7 mothers, is fully treatable, and asking for help is an act of courage, not weakness. Please speak with your doctor or a counsellor as soon as possible.",
}
_CRISIS_RESOURCES = [
    {"name":"iCall (TISS)",          "number":"9152987821",    "hours":"Mon–Sat 8am–10pm"},
    {"name":"Vandrevala Foundation", "number":"1860-2662-345", "hours":"24/7 free confidential"},
]


def ppd_screen(data: PPDInput) -> dict:
    """POST /api/ppd-screening"""
    if len(data.answers) < 10:
        return {"success": False, "error": "All 10 answers required."}
    total = 0
    for item in _EPDS_Q:
        raw = data.answers.get(str(item["id"]), 0)
        total += (3 - raw) if item["reversed"] else raw

    q10    = data.answers.get("9", 0)
    crisis = total >= 20 or q10 >= 2
    level  = "low" if total <= 9 else "medium" if total <= 12 else "high"

    sess = _get_session(data.session)
    sess["risk_scores"].append({
        "score": min(100, round(total * 3.33)),
        "ts":    datetime.now(timezone.utc).timestamp(),
    })

    alert_triggered = False
    if total >= 13 or crisis:
        e = _add_alert(data.session, "high", "self-test",
                       f"EPDS score {total}/30 — {'CRISIS (Q10)' if crisis else 'high concern'}.")
        alert_triggered = e is not None
    elif total >= 10:
        e = _add_alert(data.session, "medium", "self-test",
                       f"EPDS score {total}/30 — moderate concern.")
        alert_triggered = e is not None

    return {
        "success":         True,
        "score":           total,
        "q10":             q10,
        "crisis":          crisis,
        "level":           level,
        "guidance":        _EPDS_GUIDANCE[level],
        "resources":       _CRISIS_RESOURCES if crisis else [],
        "alert_triggered": alert_triggered,
        "wellness":        _wellness(sess["risk_scores"]),
    }


def get_epds_questions() -> dict:
    """GET /api/ppd-screening/questions"""
    return {"questions": _EPDS_Q}


def partner_setup(data: PartnerSetupInput) -> dict:
    """POST /api/partner-setup"""
    sess = _get_session(data.session)
    sess["profile"]["partner"] = data.partner.model_dump()
    return {"success": True, "partner": sess["profile"]["partner"]}


def get_chat_state(session: str) -> dict:
    """GET /api/chat-state"""
    sess = _get_session(session)
    return {
        "history":  sess["history"],
        "profile":  sess["profile"],
        "wellness": _wellness(sess["risk_scores"]),
        "alerts":   [a for a in _alerts if a["mother_id"] == session][-5:],
    }


def get_alerts(session: str | None = None) -> dict:
    """GET /api/alerts"""
    result = [a for a in _alerts if a["mother_id"] == session] if session else _alerts
    return {"alerts": list(reversed(result))}


def trigger_alert(data: AlertTriggerInput) -> dict:
    """POST /api/alerts/trigger"""
    entry = _add_alert(data.session, data.severity, data.reason, data.details)
    if not entry:
        return {"success": False, "message": "Alert already sent within 24 h."}
    return {"success": True, "alert": entry}