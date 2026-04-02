"""
MedBridge — Database Seeder using MTSamples Dataset

This script populates the database with realistic medical data from the MTSamples dataset.
It creates a demo patient, a demo doctor, and uploads a sample of medical records,
processing them with the AI pipeline for RAG.
"""

import os
import sys
import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime
import time

# Ensure we can import from backend and ai_pipeline
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.models.database import SessionLocal, engine, Base, User, Document, AccessCode
from backend.utils.auth_utils import hash_password
from ai_pipeline.document_processor import process_document

def seed_database():
    print("🏥 Starting MedBridge Data Seeder...")
    
    csv_path = "data/mtsamples/mtsamples.csv"
    if not os.path.exists(csv_path):
        print(f"❌ Error: Dataset not found at {csv_path}")
        print("Please download the MTSamples dataset and place it there.")
        return

    # Create tables if not exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Check if demo patient exists, else create
        demo_patient = db.query(User).filter(User.email == "demo_patient@medbridge.com").first()
        if not demo_patient:
            print("👤 Creating demo patient...")
            demo_patient = User(
                email="demo_patient@medbridge.com",
                hashed_password=hash_password("password123"),
                full_name="Sarah Jenkins",
                role="patient",
                blood_type="A-",
                date_of_birth=datetime.strptime("1982-05-14", "%Y-%m-%d").date(),
                allergies="Penicillin, Peanuts",
                medications="Lisinopril 10mg, Metformin 500mg",
                emergency_contact_name="Michael Jenkins",
                emergency_contact_phone="555-0198"
            )
            db.add(demo_patient)
            db.commit()
            db.refresh(demo_patient)
        else:
            print("👤 Demo patient already exists.")

        # 2. Check if demo doctor exists, else create
        demo_doctor = db.query(User).filter(User.email == "dr.smith@medbridge.com").first()
        if not demo_doctor:
            print("🩺 Creating demo doctor...")
            demo_doctor = User(
                email="dr.smith@medbridge.com",
                hashed_password=hash_password("password123"),
                full_name="Dr. Robert Smith",
                role="doctor",
                specialty="Internal Medicine",
                license_number="MD-84920"
            )
            db.add(demo_doctor)
            db.commit()
            db.refresh(demo_doctor)
        else:
            print("🩺 Demo doctor already exists.")

        # 3. Create active access code so doctor can view patient
        print("🔗 Establishing doctor-patient connection...")
        existing_code = db.query(AccessCode).filter(
            AccessCode.patient_id == demo_patient.id,
            AccessCode.doctor_id == demo_doctor.id
        ).first()

        if not existing_code:
            code = AccessCode(
                code="DEMO-123",
                patient_id=demo_patient.id,
                doctor_id=demo_doctor.id,
                expires_at=datetime.utcnow().replace(year=2030), # Won't expire soon
                is_revoked=False
            )
            db.add(code)
            db.commit()

        # 4. Load dataset and pick sample documents
        print("\n📚 Loading MTSamples dataset...")
        df = pd.read_csv(csv_path)
        
        # Filter out NaN transcriptions
        df_valid = df.dropna(subset=['transcription']).copy()
        
        # We'll pick a few distinct specialties to demonstrate RAG variety
        target_specialties = [
            ' Cardiovascular / Pulmonary', 
            ' Orthopedic', 
            ' Consult - History and Phy.', 
            ' Gastroenterology',
            ' Neurology'
        ]
        
        samples = []
        for spec in target_specialties:
            spec_df = df_valid[df_valid['medical_specialty'] == spec]
            if not spec_df.empty:
                samples.append(spec_df.iloc[0])

        if not samples:
             # Fallback: just take first 5 valid records if categories don't match exactly
             samples = [df_valid.iloc[i] for i in range(min(5, len(df_valid)))]

        print(f"📄 Processing {len(samples)} clinical documents for {demo_patient.full_name}...")
        
        docs_processed = 0
        for i, row in enumerate(samples):
            # Safe parsing
            specialty = str(row['medical_specialty']).strip()
            desc = str(row['description']).strip()
            transcription = str(row['transcription'])

            # Create a mock filename based on specialty
            filename = f"ClinicalNote_{specialty.replace(' ', '').replace('/', '_')}_{i+1}.txt"

            # Check if this document was already seeded
            existing_doc = db.query(Document).filter(
                Document.patient_id == demo_patient.id,
                Document.original_filename == filename
            ).first()

            if existing_doc:
                print(f"  ⏭️ Skipping {filename} (already exists)")
                continue

            # Create the DB record
            print(f"  🧠 Vectorizing and storing: {filename} ({specialty})")
            
            # Map specialty to doc_type if reasonable, or use 'consultation_note'
            doc_type = "consultation_note"
            if "Cardiovascular" in specialty: doc_type = "lab_report"
            elif "Orthopedic" in specialty: doc_type = "imaging"
            
            # Ensure it's not saved to filesystem, just DB (virtual file)
            new_doc = Document(
                patient_id=demo_patient.id,
                filename=filename,
                original_filename=filename,
                file_path=f"virtual://{filename}", # We won't actually write a file to disk
                file_size=len(transcription.encode('utf-8')),
                content_text=transcription,
                doc_type=doc_type,
                is_processed=False,
                uploaded_by=demo_patient.id
            )
            db.add(new_doc)
            db.commit()
            db.refresh(new_doc)

            # Process AI chunks and embeddings
            try:
                num_chunks = process_document(
                    patient_id=demo_patient.id,
                    document_id=new_doc.id,
                    content_text=transcription,
                    original_filename=filename,
                    doc_type=doc_type
                )
                
                # Mark processed
                new_doc.is_processed = True
                db.commit()
                print(f"    ✅ Embedded {num_chunks} chunks.")
                docs_processed += 1
                
                # Optional small delay to respect API logic if applicable
                time.sleep(1)
            except Exception as e:
                print(f"    ❌ AI Processing failed for {filename}: {e}")

        print(f"\n🎉 Seeding complete!")
        print(f"Demo Patient login: demo_patient@medbridge.com / password123")
        print(f"Demo Doctor login:  dr.smith@medbridge.com / password123")
        print(f"Patient access code: DEMO-123")
        
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
