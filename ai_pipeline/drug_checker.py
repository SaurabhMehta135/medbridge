"""
MedBridge — Drug Interaction & Allergy Checker

Provides more comprehensive drug interaction checking than the basic
rule-based alerts router. Uses a combination of:
  1. A curated database of known interactions
  2. Document scanning for medication mentions
  3. (Future) NER-based extraction from medical records
"""

import logging
import re
from typing import List, Set, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Drug Interaction Database (curated subset of critical interactions)
# ---------------------------------------------------------------------------

DRUG_INTERACTIONS = {
    # (drug_a, drug_b): {severity, description}
    frozenset({"warfarin", "aspirin"}): {
        "severity": "critical",
        "description": "Increases bleeding risk significantly. Monitor INR closely.",
    },
    frozenset({"warfarin", "ibuprofen"}): {
        "severity": "critical",
        "description": "NSAIDs increase bleeding risk with warfarin. Avoid combination.",
    },
    frozenset({"warfarin", "naproxen"}): {
        "severity": "critical",
        "description": "NSAIDs increase bleeding risk with warfarin.",
    },
    frozenset({"metformin", "contrast"}): {
        "severity": "warning",
        "description": "Hold metformin 48h before/after contrast imaging (lactic acidosis risk).",
    },
    frozenset({"lisinopril", "potassium"}): {
        "severity": "warning",
        "description": "ACE inhibitors increase potassium. Avoid supplemental potassium.",
    },
    frozenset({"lisinopril", "spironolactone"}): {
        "severity": "warning",
        "description": "Both increase potassium levels. Risk of hyperkalemia.",
    },
    frozenset({"methotrexate", "trimethoprim"}): {
        "severity": "critical",
        "description": "Trimethoprim increases methotrexate toxicity. May cause pancytopenia.",
    },
    frozenset({"digoxin", "amiodarone"}): {
        "severity": "critical",
        "description": "Amiodarone increases digoxin levels. Reduce digoxin dose by 50%.",
    },
    frozenset({"simvastatin", "amiodarone"}): {
        "severity": "warning",
        "description": "Increased risk of rhabdomyolysis. Limit simvastatin to 20mg.",
    },
    frozenset({"clopidogrel", "omeprazole"}): {
        "severity": "warning",
        "description": "Omeprazole reduces clopidogrel effectiveness. Use pantoprazole instead.",
    },
    frozenset({"fluoxetine", "tramadol"}): {
        "severity": "critical",
        "description": "Serotonin syndrome risk. Avoid combination.",
    },
    frozenset({"fluoxetine", "mao inhibitor"}): {
        "severity": "critical",
        "description": "Serotonin syndrome risk. Contraindicated combination.",
    },
    frozenset({"ciprofloxacin", "theophylline"}): {
        "severity": "warning",
        "description": "Ciprofloxacin increases theophylline levels. Monitor closely.",
    },
    frozenset({"metronidazole", "alcohol"}): {
        "severity": "warning",
        "description": "Disulfiram-like reaction. Avoid alcohol during and 48h after treatment.",
    },
}

# Drug class mappings (for cross-class interaction detection)
DRUG_CLASSES = {
    "nsaid": ["ibuprofen", "naproxen", "diclofenac", "celecoxib", "meloxicam", "aspirin"],
    "ace_inhibitor": ["lisinopril", "enalapril", "ramipril", "captopril", "benazepril"],
    "ssri": ["fluoxetine", "sertraline", "paroxetine", "citalopram", "escitalopram"],
    "statin": ["simvastatin", "atorvastatin", "rosuvastatin", "pravastatin", "lovastatin"],
    "anticoagulant": ["warfarin", "heparin", "enoxaparin", "rivaroxaban", "apixaban"],
    "beta_blocker": ["metoprolol", "atenolol", "propranolol", "carvedilol", "bisoprolol"],
    "opioid": ["morphine", "hydrocodone", "oxycodone", "fentanyl", "tramadol", "codeine"],
}

# Cross-allergy risk pairs
CROSS_ALLERGIES = {
    "penicillin": ["amoxicillin", "ampicillin", "cephalosporin", "cefazolin", "ceftriaxone"],
    "sulfa": ["sulfamethoxazole", "sulfasalazine", "trimethoprim-sulfamethoxazole"],
    "nsaid": ["aspirin", "ibuprofen", "naproxen"],
}


# ---------------------------------------------------------------------------
# Medication Extraction (regex-based, will be upgraded to NER)
# ---------------------------------------------------------------------------

# Common medication names for regex scanning
COMMON_MEDICATIONS = {
    "metformin", "lisinopril", "amlodipine", "metoprolol", "omeprazole",
    "simvastatin", "atorvastatin", "losartan", "hydrochlorothiazide",
    "amoxicillin", "azithromycin", "ciprofloxacin", "prednisone",
    "warfarin", "aspirin", "ibuprofen", "acetaminophen", "gabapentin",
    "sertraline", "fluoxetine", "citalopram", "tramadol", "morphine",
    "insulin", "levothyroxine", "albuterol", "montelukast", "pantoprazole",
    "furosemide", "spironolactone", "digoxin", "amiodarone", "clopidogrel",
    "naproxen", "diclofenac", "celecoxib", "methylprednisolone",
}


def extract_medications_from_text(text: str) -> Set[str]:
    """Extract medication names from text using regex pattern matching."""
    if not text:
        return set()

    text_lower = text.lower()
    found = set()

    for med in COMMON_MEDICATIONS:
        # Word boundary match to avoid partial matches
        pattern = r"\b" + re.escape(med) + r"\b"
        if re.search(pattern, text_lower):
            found.add(med)

    return found


# ---------------------------------------------------------------------------
# Interaction Checking
# ---------------------------------------------------------------------------

def check_drug_interactions(medications: List[str]) -> List[dict]:
    """
    Check a list of medications for known interactions.

    Returns a list of alert dicts with keys:
        alert_type, severity, title, description, related_drugs
    """
    alerts = []
    meds_lower = {m.lower().strip() for m in medications}

    # Direct pair checks
    for pair, info in DRUG_INTERACTIONS.items():
        if pair.issubset(meds_lower):
            drugs = sorted(pair)
            alerts.append({
                "alert_type": "drug_interaction",
                "severity": info["severity"],
                "title": f"Interaction: {drugs[0].title()} + {drugs[1].title()}",
                "description": info["description"],
                "related_drugs": drugs,
            })

    # Class-level checks (e.g., any NSAID + any anticoagulant)
    patient_classes = {}
    for med in meds_lower:
        for class_name, members in DRUG_CLASSES.items():
            if med in members:
                patient_classes.setdefault(class_name, []).append(med)

    # NSAID + Anticoagulant
    if "nsaid" in patient_classes and "anticoagulant" in patient_classes:
        nsaid = patient_classes["nsaid"][0]
        anticoag = patient_classes["anticoagulant"][0]
        pair_key = frozenset({nsaid, anticoag})
        # Only add if not already detected as a direct interaction
        if not any(set(a["related_drugs"]) == pair_key for a in alerts):
            alerts.append({
                "alert_type": "drug_interaction",
                "severity": "critical",
                "title": f"NSAID + Anticoagulant Risk",
                "description": f"{nsaid.title()} (NSAID) with {anticoag.title()} increases bleeding risk.",
                "related_drugs": [nsaid, anticoag],
            })

    # Duplicate class detection (e.g., two SSRIs)
    for class_name, meds in patient_classes.items():
        if len(meds) > 1:
            alerts.append({
                "alert_type": "duplicate_class",
                "severity": "warning",
                "title": f"Duplicate {class_name.replace('_', ' ').title()} Detected",
                "description": f"Patient is on multiple {class_name.replace('_', ' ')}s: {', '.join(m.title() for m in meds)}. Review for appropriateness.",
                "related_drugs": sorted(meds),
            })

    return alerts


def check_allergy_conflicts(
    allergies: List[str],
    medications: List[str],
) -> List[dict]:
    """
    Check if any current medications conflict with known allergies.

    Returns a list of alert dicts.
    """
    alerts = []
    allergy_lower = {a.lower().strip() for a in allergies}
    med_lower = {m.lower().strip() for m in medications}

    # Direct allergy-medication conflicts
    direct_conflicts = allergy_lower & med_lower
    for drug in direct_conflicts:
        alerts.append({
            "alert_type": "allergy_conflict",
            "severity": "critical",
            "title": f"⚠️ Allergy Alert: {drug.title()}",
            "description": f"Patient is allergic to {drug.title()} but it is listed in current medications!",
            "related_drugs": [drug],
        })

    # Cross-allergy checks
    for allergen_class, related_drugs in CROSS_ALLERGIES.items():
        if allergen_class in allergy_lower:
            for med in med_lower:
                if med in related_drugs:
                    alerts.append({
                        "alert_type": "cross_allergy",
                        "severity": "warning",
                        "title": f"Cross-Allergy Risk: {allergen_class.title()} → {med.title()}",
                        "description": f"Patient is allergic to {allergen_class}. {med.title()} may cause cross-reaction.",
                        "related_drugs": [allergen_class, med],
                    })

    return alerts


def full_safety_check(
    allergies: List[str],
    medications: List[str],
    document_texts: Optional[List[str]] = None,
) -> List[dict]:
    """
    Run a comprehensive safety check combining:
      1. Drug-drug interaction check
      2. Allergy-medication conflict check
      3. Medication extraction from documents (if provided)

    Returns a combined, deduplicated list of alerts sorted by severity.
    """
    all_meds = set(m.lower().strip() for m in medications)

    # Extract additional medications from documents
    if document_texts:
        for text in document_texts:
            found = extract_medications_from_text(text)
            all_meds.update(found)

    all_alerts = []
    all_alerts.extend(check_drug_interactions(list(all_meds)))
    all_alerts.extend(check_allergy_conflicts(allergies, list(all_meds)))

    # Sort by severity (critical first)
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    all_alerts.sort(key=lambda a: severity_order.get(a["severity"], 99))

    return all_alerts
