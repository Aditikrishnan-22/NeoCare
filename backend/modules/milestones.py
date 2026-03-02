"""
Module 2 — Developmental Milestone Monitoring
Based on the Trivandrum Developmental Screening Chart (TDSC) 0–3 years
"""
from typing import Optional
from pydantic import BaseModel


# ── TDSC MILESTONE DATA ───────────────────────────────────────
# id, label, domain, start_age_months, end_age_months (upper limit)

MILESTONES = [
    {"id": 1,  "label": "Social smile",                            "domain": "Social",       "start": 1,  "end": 2},
    {"id": 2,  "label": "Eyes follow moving object (pen/pencil)",  "domain": "Fine Motor",   "start": 1,  "end": 3},
    {"id": 3,  "label": "Hold head steady",                        "domain": "Gross Motor",  "start": 2,  "end": 4},
    {"id": 4,  "label": "Rolls back to stomach",                   "domain": "Gross Motor",  "start": 3,  "end": 5},
    {"id": 5,  "label": "Turns head to sound (bell/rattle)",       "domain": "Language",     "start": 3,  "end": 6},
    {"id": 6,  "label": "Transfers object hand to hand",           "domain": "Fine Motor",   "start": 4,  "end": 7},
    {"id": 7,  "label": "Raises self to sitting position",         "domain": "Gross Motor",  "start": 5,  "end": 9},
    {"id": 8,  "label": "Stands holding on to furniture",          "domain": "Gross Motor",  "start": 7,  "end": 10},
    {"id": 9,  "label": "Fine prehension (picks up small pellet)", "domain": "Fine Motor",   "start": 8,  "end": 12},
    {"id": 10, "label": "Sits without support",                    "domain": "Gross Motor",  "start": 6,  "end": 10},
    {"id": 11, "label": "Walks with help",                         "domain": "Gross Motor",  "start": 9,  "end": 13},
    {"id": 12, "label": "Says 'mama' or 'dada' (specific)",        "domain": "Language",     "start": 9,  "end": 14},
    {"id": 13, "label": "Walks alone",                             "domain": "Gross Motor",  "start": 11, "end": 18},
    {"id": 14, "label": "Says two meaningful words",               "domain": "Language",     "start": 12, "end": 18},
    {"id": 15, "label": "Walks backwards",                         "domain": "Gross Motor",  "start": 14, "end": 20},
    {"id": 16, "label": "Walks upstairs with help",                "domain": "Gross Motor",  "start": 14, "end": 21},
    {"id": 17, "label": "Points to body parts on doll",            "domain": "Social",       "start": 14, "end": 20},
    {"id": 18, "label": "Removes garments (hat, shoes)",           "domain": "Social",       "start": 15, "end": 22},
    {"id": 19, "label": "Uses words for personal needs",           "domain": "Language",     "start": 16, "end": 24},
    {"id": 20, "label": "Jumps in place",                          "domain": "Gross Motor",  "start": 18, "end": 28},
    {"id": 21, "label": "Differentiates big/small objects",        "domain": "Language",     "start": 20, "end": 28},
    {"id": 22, "label": "Points to common objects when named",     "domain": "Language",     "start": 18, "end": 26},
    {"id": 23, "label": "Brushes teeth with help",                 "domain": "Social",       "start": 22, "end": 30},
    {"id": 24, "label": "Tells own gender when asked",             "domain": "Social",       "start": 24, "end": 33},
    {"id": 25, "label": "Speech half understandable to strangers", "domain": "Language",     "start": 24, "end": 33},
    {"id": 26, "label": "Places objects 'on/under' on instruction","domain": "Language",     "start": 27, "end": 36},
    {"id": 27, "label": "Asks simple questions",                   "domain": "Language",     "start": 28, "end": 36},
]

# Absolute upper-limit red flags (independent of checklist answers)
ABSOLUTE_RED_FLAGS = [
    {"age": 2,  "flag": "No visual fixation or following by 2 months"},
    {"age": 6,  "flag": "No vocalization by 6 months"},
    {"age": 10, "flag": "Cannot sit without support by 10 months"},
    {"age": 12, "flag": "Cannot stand even with assistance by 12 months"},
    {"age": 14, "flag": "Not crawling on hands and knees by 14 months"},
    {"age": 17, "flag": "Cannot stand alone by 17 months"},
    {"age": 18, "flag": "Cannot walk alone by 18 months"},
    {"age": 18, "flag": "No single words by 18 months"},
    {"age": 36, "flag": "No imaginative play by 3 years"},
]

# Domain-specific early stimulation tips
STIMULATION_TIPS = {
    "Gross Motor": [
        "Encourage supervised stair climbing practice",
        "Use push/pull toys to build walking confidence",
        "Allow safe open space for crawling and walking",
        "Practice ball rolling and simple catching games",
    ],
    "Fine Motor": [
        "Provide stacking blocks and shape-sorting cups",
        "Encourage self-feeding with safe finger foods",
        "Drawing, scribbling, and tearing paper activities",
        "Simple puzzles and bead-threading games",
    ],
    "Language": [
        "Talk directly to the child throughout the day",
        "Read picture books daily and name everything",
        "Sing nursery rhymes and simple songs together",
        "Reduce passive screen time — it delays language development!",
    ],
    "Social": [
        "Maintain eye contact and respond warmly to the child's cues",
        "Play imitation games: peek-a-boo, clapping, waving",
        "Name emotions during play ('you look so happy!')",
        "Involve the child in simple daily routines (handing things, tidying)",
    ],
}


# ── SCHEMAS ───────────────────────────────────────────────────
class MilestoneInput(BaseModel):
    age_months:             float
    sex:                    str
    premature:              bool = False
    gestational_age_weeks:  Optional[int] = None
    answers:                dict   # { "1": True, "2": False, ... }
    regression:             bool = False


# ── CHECKLIST BUILDER ─────────────────────────────────────────
def get_checklist(age_months: float) -> list:
    """Return milestones relevant for a given age."""
    return [m for m in MILESTONES if m["start"] <= age_months + 4]


# ── EVALUATION ────────────────────────────────────────────────
def evaluate(data: MilestoneInput) -> dict:
    # Corrected age for premature babies
    corrected_age = data.age_months
    if data.premature and data.gestational_age_weeks:
        weeks_early   = 40 - data.gestational_age_weeks
        corrected_age = max(0.0, data.age_months - (weeks_early / 4.33))

    domains = ["Gross Motor", "Fine Motor", "Language", "Social"]
    domain_items  = {d: [] for d in domains}
    red_flags     = []

    for m in MILESTONES:
        mid = str(m["id"])
        if mid not in data.answers:
            continue

        achieved = data.answers[mid]
        domain   = m["domain"]

        if not achieved and corrected_age > m["end"]:
            red_flags.append({
                "milestone": m["label"],
                "domain":    domain,
                "message":   f"Expected by {m['end']} months — needs evaluation",
            })
            domain_items[domain].append("flag")
        elif not achieved and corrected_age >= m["start"]:
            domain_items[domain].append("monitor")
        else:
            domain_items[domain].append("normal")

    # Summarise each domain
    domain_status = {}
    for d in domains:
        items = domain_items[d]
        if not items:
            domain_status[d] = "not_assessed"
        elif "flag" in items:
            domain_status[d] = "flag"
        elif "monitor" in items:
            domain_status[d] = "monitor"
        else:
            domain_status[d] = "normal"

    # Applicable absolute red flags
    abs_flags = [f["flag"] for f in ABSOLUTE_RED_FLAGS if corrected_age >= f["age"]]

    # Special clinical notes
    special_notes = []
    if (domain_status.get("Language") == "flag"
            and domain_status.get("Gross Motor") in ("normal", "not_assessed")
            and domain_status.get("Social") in ("normal", "not_assessed")):
        special_notes.append(
            "Isolated language delay detected — consider hearing screening and ENT/pediatric consultation."
        )

    return {
        "corrected_age":               round(corrected_age, 1),
        "domain_status":               domain_status,
        "red_flags":                   red_flags,
        "absolute_red_flags_applicable": abs_flags[:4],
        "regression_alert":            data.regression,
        "special_notes":               special_notes,
        "stimulation_tips":            STIMULATION_TIPS,
    }