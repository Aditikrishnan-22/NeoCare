"""
Module 1 — Child Growth Monitoring
WHO Z-score calculations for Weight, Length, Head Circumference
"""
import math
from typing import Optional
from pydantic import BaseModel


# ── WHO LMS PARAMETERS ────────────────────────────────────────
# Format: age_months -> (L, M, S)
# Source: WHO Child Growth Standards

WHO_WEIGHT_FOR_AGE = {
    "boys": {
        0: (-0.3521, 3.3464, 0.14602), 1: (-0.3521, 4.4709, 0.13395),
        2: (-0.3521, 5.5675, 0.12385), 3: (-0.3521, 6.3762, 0.11727),
        4: (-0.3521, 7.0023, 0.11316), 5: (-0.3521, 7.5105, 0.10963),
        6: (-0.3521, 7.9340, 0.10680), 7: (-0.3521, 8.2970, 0.10454),
        8: (-0.3521, 8.6151, 0.10298), 9: (-0.3521, 8.9014, 0.10175),
        10: (-0.3521, 9.1649, 0.10069), 11: (-0.3521, 9.4122, 0.09972),
        12: (-0.3521, 9.6479, 0.09880), 18: (-0.3521, 10.9300, 0.09647),
        24: (-0.3521, 12.1410, 0.09560), 36: (-0.3521, 14.3000, 0.09500),
        48: (-0.3521, 16.3000, 0.09500), 60: (-0.3521, 18.3000, 0.09500),
    },
    "girls": {
        0: (-0.3833, 3.2322, 0.14171), 1: (-0.3833, 4.1873, 0.13724),
        2: (-0.3833, 5.1282, 0.13000), 3: (-0.3833, 5.8458, 0.12619),
        4: (-0.3833, 6.4237, 0.12222), 5: (-0.3833, 6.8985, 0.11898),
        6: (-0.3833, 7.2981, 0.11657), 7: (-0.3833, 7.6422, 0.11423),
        8: (-0.3833, 7.9487, 0.11243), 9: (-0.3833, 8.2254, 0.11080),
        10: (-0.3833, 8.4800, 0.10939), 11: (-0.3833, 8.7192, 0.10828),
        12: (-0.3833, 8.9481, 0.10726), 18: (-0.3833, 10.2000, 0.10500),
        24: (-0.3833, 11.5000, 0.10300), 36: (-0.3833, 13.9000, 0.10000),
        48: (-0.3833, 15.9000, 0.10000), 60: (-0.3833, 17.9000, 0.10000),
    }
}

WHO_LENGTH_FOR_AGE = {
    "boys": {
        0: (1, 49.8842, 0.03795), 3: (1, 61.4292, 0.03598),
        6: (1, 67.6236, 0.03570), 12: (1, 75.7490, 0.03813),
        18: (1, 82.3241, 0.03580), 24: (1, 87.8161, 0.03694),
        36: (1, 96.1000, 0.03800), 48: (1, 103.3000, 0.03800),
        60: (1, 110.0000, 0.03800),
    },
    "girls": {
        0: (1, 49.1477, 0.03790), 3: (1, 59.8029, 0.03608),
        6: (1, 65.7311, 0.03624), 12: (1, 74.0150, 0.03804),
        18: (1, 80.7410, 0.03665), 24: (1, 86.4153, 0.03776),
        36: (1, 95.1000, 0.03800), 48: (1, 102.7000, 0.03800),
        60: (1, 109.4000, 0.03800),
    }
}

WHO_HC_FOR_AGE = {
    "boys": {
        0: (1, 34.4618, 0.03686), 3: (1, 40.5138, 0.03034),
        6: (1, 43.3223, 0.02847), 12: (1, 46.5796, 0.02717),
        18: (1, 48.0000, 0.02600), 24: (1, 49.0000, 0.02500),
        36: (1, 50.3000, 0.02400), 48: (1, 51.0000, 0.02300),
        60: (1, 51.7000, 0.02200),
    },
    "girls": {
        0: (1, 33.8787, 0.03496), 3: (1, 39.5328, 0.02956),
        6: (1, 42.2441, 0.02814), 12: (1, 45.4192, 0.02706),
        18: (1, 46.9000, 0.02600), 24: (1, 47.8000, 0.02500),
        36: (1, 49.1000, 0.02400), 48: (1, 49.8000, 0.02300),
        60: (1, 50.5000, 0.02200),
    }
}


# ── SCHEMAS ───────────────────────────────────────────────────
class GrowthInput(BaseModel):
    age_months: float
    sex: str
    weight_kg: Optional[float] = None
    length_cm: Optional[float] = None
    hc_cm:     Optional[float] = None


# ── HELPERS ───────────────────────────────────────────────────
def _nearest_age(table: dict, age: float) -> tuple:
    ages = sorted(table.keys())
    nearest = min(ages, key=lambda x: abs(x - age))
    return table[nearest]


def _zscore(value: float, L: float, M: float, S: float) -> float:
    if L == 0:
        return math.log(value / M) / S
    return ((value / M) ** L - 1) / (L * S)


def _weight_guidance(z: float, ftt: bool) -> tuple[str, str, str]:
    """Returns (status_label, icon, guidance_text)"""
    if z < -3:
        return ("Severe Underweight", "🔴",
                "Urgent: Please consult a pediatrician immediately. Start therapeutic feeding if advised. "
                "Increase calorie and protein-rich foods such as dal, eggs, banana, and milk.")
    if z < -2:
        return ("Underweight", "🟡",
                "Monitor weight weekly. Increase feeding frequency. Add calorie-dense foods. "
                "Follow up with a doctor if there is no improvement in 4 weeks.")
    if z > 3:
        return ("Obese", "🔴",
                "Please consult a pediatrician for a dietary plan and health evaluation.")
    if z > 2:
        return ("Overweight", "🟡",
                "Reduce high-sugar foods and encourage active play. Consult a doctor for dietary advice.")
    return ("Normal Weight", "🟢",
            "Weight is on track! Continue balanced nutrition and regular checkups.")


def _length_guidance(z: float) -> tuple[str, str, str]:
    if z < -3:
        return ("Severe Stunting", "🔴",
                "Severe stunting indicates significant chronic malnutrition. Seek pediatric evaluation urgently. "
                "Focus on long-term nutrition improvement and infection prevention.")
    if z < -2:
        return ("Stunting", "🟡",
                "Stunting detected. Improve diet quality — include proteins (eggs, lentils), zinc-rich foods. "
                "Ensure good hygiene practices to prevent infections.")
    return ("Normal Height", "🟢",
            "Height is within the normal range for this age. Keep up with good nutrition!")


def _hc_guidance(z: float) -> tuple[str, str, str]:
    if z < -2:
        return ("Microcephaly Risk", "🔴",
                "Head size is smaller than expected for age. This cannot be corrected by diet. "
                "Please consult a pediatrician and neurologist for immediate evaluation.")
    if z > 2:
        return ("Macrocephaly Risk", "🔴",
                "Head size is larger than expected for age. "
                "Please consult a pediatrician for neurological evaluation.")
    return ("Normal Head Growth", "🟢",
            "Head circumference is within the normal range for age.")


# ── MAIN ANALYSIS FUNCTION ────────────────────────────────────
def analyze(data: GrowthInput) -> dict:
    sex = data.sex.lower()
    if sex not in ("boys", "girls"):
        sex = "boys"

    results = {}

    # Weight-for-Age
    if data.weight_kg:
        L, M, S = _nearest_age(WHO_WEIGHT_FOR_AGE[sex], data.age_months)
        z = round(_zscore(data.weight_kg, L, M, S), 2)
        ftt = z < -2 and data.age_months > 3
        label, icon, guidance = _weight_guidance(z, ftt)
        results["weight_for_age"] = {
            "z_score": z,
            "status": label,
            "icon": icon,
            "guidance": guidance,
            "ftt_risk": ftt,
        }

    # Length-for-Age
    if data.length_cm:
        L, M, S = _nearest_age(WHO_LENGTH_FOR_AGE[sex], data.age_months)
        z = round(_zscore(data.length_cm, L, M, S), 2)
        label, icon, guidance = _length_guidance(z)
        results["length_for_age"] = {
            "z_score": z,
            "status": label,
            "icon": icon,
            "guidance": guidance,
        }

    # Head Circumference-for-Age
    if data.hc_cm:
        L, M, S = _nearest_age(WHO_HC_FOR_AGE[sex], data.age_months)
        z = round(_zscore(data.hc_cm, L, M, S), 2)
        label, icon, guidance = _hc_guidance(z)
        results["head_circumference"] = {
            "z_score": z,
            "status": label,
            "icon": icon,
            "guidance": guidance,
        }

    return results