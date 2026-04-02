import json
from datetime import datetime
from sqlalchemy.orm import Session

from backend.models.database import User, Document, FollowUp
from backend.routers.risk_engine import run_extraction

def generate_patient_fhir_bundle(patient: User, db: Session) -> dict:
    """
    Generates an HL7 FHIR R4 JSON Bundle containing all known health data
    for a specific patient.
    """
    resources = []
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    # Prefix helper
    pat_ref = f"Patient/patient-{patient.id}"
    
    # -----------------------------------------------------------------
    # 1. Patient Resource
    # -----------------------------------------------------------------
    gender_map = {"m": "male", "f": "female", "male": "male", "female": "female"}
    # MedBridge users don't have explicit gender right now, default to unknown or guess from name/profile 
    # but we'll leave as unknown if we don't have it.
    
    pat_resource = {
        "resourceType": "Patient",
        "id": f"patient-{patient.id}",
        "meta": {
            "profile": ["http://hl7.org/fhir/StructureDefinition/Patient"]
        },
        "identifier": [{
            "system": "https://medbridge.app/patients",
            "value": str(patient.id)
        }],
        "name": [{
            "use": "official",
            "text": patient.full_name
        }],
        "telecom": [{
            "system": "email",
            "value": patient.email
        }]
    }
    
    if patient.phone_number:
        pat_resource["telecom"].append({
            "system": "phone",
            "value": patient.phone_number
        })
        
    if patient.date_of_birth:
        pat_resource["birthDate"] = patient.date_of_birth.isoformat()
        
    resources.append({"resource": pat_resource})
    
    # -----------------------------------------------------------------
    # Extract Clinical Data On-the-Fly
    # -----------------------------------------------------------------
    extracted = run_extraction(patient.id, db)
    
    # -----------------------------------------------------------------
    # 2. Condition Resources
    # -----------------------------------------------------------------
    conditions_map = {
        "diabetes_dx": "Diabetes",
        "ckd_dx": "Chronic Kidney Disease",
        "proteinuria": "Proteinuria",
        "fhx_heart": "Family history of heart disease"
    }
    
    for key, name in conditions_map.items():
        for item in extracted.get(key, []):
            try:
                date_rec = datetime.strptime(item["date"], "%Y-%m-%d").isoformat() + "Z"
            except:
                date_rec = timestamp
                
            cond_res = {
                "resourceType": "Condition",
                "id": f"cond-{patient.id}-{key}-{abs(hash(item['date'])) % 10000}",
                "subject": {"reference": pat_ref},
                "code": {"text": name},
                "recordedDate": date_rec,
                "clinicalStatus": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active"
                    }]
                }
            }
            resources.append({"resource": cond_res})
    
    # -----------------------------------------------------------------
    # 3. Observation Resources (Labs & Vitals)
    # -----------------------------------------------------------------
    # Mapping extracted keys to LOINCish display names and units
    obs_map = {
        "bp": ("Blood Pressure", "mmHg"),
        "ldl": ("LDL Cholesterol", "mg/dL"),
        "bmi": ("Body Mass Index", "kg/m2"),
        "hba1c": ("Hemoglobin A1c", "%"),
        "glucose": ("Fasting Glucose", "mg/dL"),
        "creatinine": ("Creatinine", "mg/dL"),
        "egfr": ("eGFR", "mL/min/1.73m2")
    }
    
    for key, (display, unit) in obs_map.items():
        for item in extracted.get(key, []):
            try:
                date_eff = datetime.strptime(item["date"], "%Y-%m-%d").isoformat() + "Z"
            except:
                date_eff = timestamp
                
            obs_res = {
                "resourceType": "Observation",
                "id": f"obs-{patient.id}-{key}-{abs(hash(str(item['value'])+item['date'])) % 10000}",
                "status": "final",
                "subject": {"reference": pat_ref},
                "code": {"text": display},
                "effectiveDateTime": date_eff
            }
            
            # Format value
            if key == "bp":
                # Special case for BP
                try:
                    sys, dia = item["value"].split("/")
                    obs_res["component"] = [
                        {
                            "code": {"text": "Systolic Blood Pressure"},
                            "valueQuantity": {"value": float(sys), "unit": unit}
                        },
                        {
                            "code": {"text": "Diastolic Blood Pressure"},
                            "valueQuantity": {"value": float(dia), "unit": unit}
                        }
                    ]
                except:
                    obs_res["valueString"] = str(item["value"])
            else:
                try:
                    obs_res["valueQuantity"] = {
                        "value": float(item["value"]),
                        "unit": unit
                    }
                except:
                    obs_res["valueString"] = str(item["value"])
                    
            resources.append({"resource": obs_res})
            
    # -----------------------------------------------------------------
    # 4. MedicationRequest Resources
    # -----------------------------------------------------------------
    if patient.medications:
        meds = [m.strip() for m in patient.medications.split(",")]
        for i, med in enumerate(meds):
            if not med: continue
            med_res = {
                "resourceType": "MedicationRequest",
                "id": f"med-{patient.id}-{i}",
                "status": "active",
                "intent": "order",
                "subject": {"reference": pat_ref},
                "medicationCodeableConcept": {"text": med},
                "authoredOn": timestamp
            }
            resources.append({"resource": med_res})
            
    # -----------------------------------------------------------------
    # 5. AllergyIntolerance Resources
    # -----------------------------------------------------------------
    if patient.allergies:
        allergies = [a.strip() for a in patient.allergies.split(",")]
        for i, alg in enumerate(allergies):
            if not alg: continue
            alg_res = {
                "resourceType": "AllergyIntolerance",
                "id": f"alg-{patient.id}-{i}",
                "patient": {"reference": pat_ref},
                "code": {"text": alg},
                "recordedDate": timestamp
            }
            resources.append({"resource": alg_res})
            
    # -----------------------------------------------------------------
    # 6. Encounter Resources (Built from FollowUps)
    # -----------------------------------------------------------------
    encounters = db.query(FollowUp).filter(FollowUp.patient_id == patient.id, FollowUp.status == "completed").all()
    for enc in encounters:
        start_date = enc.completed_at.isoformat() + "Z" if enc.completed_at else timestamp
        enc_res = {
            "resourceType": "Encounter",
            "id": f"enc-{enc.id}",
            "status": "finished",
            "subject": {"reference": pat_ref},
            "period": {
                "start": start_date,
                "end": start_date
            },
            "reasonCode": [{
                "text": enc.description
            }]
        }
        resources.append({"resource": enc_res})

    # -----------------------------------------------------------------
    # Wrap in Bundle
    # -----------------------------------------------------------------
    bundle = {
        "resourceType": "Bundle",
        "id": f"bundle-{patient.id}-{int(datetime.utcnow().timestamp())}",
        "type": "collection",
        "timestamp": timestamp,
        "meta": {
            "tag": [{
                "system": "https://medbridge.app",
                "code": "medbridge-export",
                "display": "Exported from MedBridge"
            }]
        },
        "entry": resources
    }
    
    return bundle
