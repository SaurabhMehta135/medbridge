# MedBridge

**AI-powered two-sided health record platform for patients and doctors**

![Status](https://img.shields.io/badge/Status-In%20Development-yellow)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688)
![Streamlit](https://img.shields.io/badge/Streamlit-1.25%2B-FF4B4B)

## 📌 The Problem
Medical history is fragmented. Patients struggle to gather and supply their full medical records when seeing new specialists. Doctors spend too much time reading redundant paperwork and risk missing critical details (like allergies or conflicting medications). 

## 💡 The Solution
MedBridge acts as a singular hub:
1. **Patients** upload their health documents and generate shareable access codes.
2. **Doctors** enter the access code to get an AI-summarized, highly searchable view of the patient’s history.

## ✨ Features

### 🏥 For Patients (Patient App)
- **Document Management**: Securely upload and manage medical PDFs
- **AI Health Assistant**: Ask questions in simple terms about your own health records
- **Consent-based Sharing**: Generate time-scoped access codes for your doctor
- **Revoke Access**: Full control over who sees your data

### 🩺 For Doctors (Doctor App)
- **Patient Dashboard**: Input an access code to list and view authorized patients
- **Population Analytics**: Aggregated dashboard showing condition and risk distributions
- **FHIR R4 Export**: Export complete patient health records to the international HL7 FHIR standard
- **Clinical Assistant**: Clinical-grade AI specifically scoped to ONE patient's records
- **Drug & Allergy Alerts**: Proactive warnings about potential issues
- **Targeted Search**: Quickly search for conditions, recent labs, and history inside the patient's record

## 🛠️ Tech Stack
- **Backend**: FastAPI
- **Frontend**: Two separate Streamlit apps (Patient & Doctor)
- **Database**: SQLite with SQLAlchemy
- **Vector Database**: ChromaDB
- **Embeddings**: BioBERT (`pritamdeka/BioBERT-mnli-snli-scinli-scitail-mednli-sts`)
- **LLM**: Claude (Anthropic API) & OpenAI
- **PDF Processing**: PyPDF2
- **Authentication**: JWT tokens with bcrypt

## 📁 Project Structure

```
medbridge/
├── backend/            # FastAPI backend and auth logic
├── ai_pipeline/        # RAG, ChromaDB, and BioBERT logic
├── patient_app/        # Streamlit app for patients
├── doctor_app/         # Streamlit app for doctors
├── data/               # Local database and vector storage
├── tests/              # Unit and integration tests
└── docs/               # Architecture diagrams and documentation
```

## 🚀 Getting Started

*(Instructions will be added once development is complete)*

## 📄 Acknowledgement
This project utilizes the [MTSamples](https://mtsamples.com/) dataset for realistic (but entirely synthetic/anonymized) medical transcriptions.

## ⚖️ License
MIT License
