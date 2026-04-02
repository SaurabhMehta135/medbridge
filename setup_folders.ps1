$files = @(
    "backend/__init__.py",
    "backend/main.py",
    "backend/routers/__init__.py",
    "backend/routers/auth.py",
    "backend/routers/patient.py",
    "backend/routers/doctor.py",
    "backend/routers/chat.py",
    "backend/routers/alerts.py",
    "backend/models/__init__.py",
    "backend/models/database.py",
    "backend/models/schemas.py",
    "backend/utils/__init__.py",
    "backend/utils/auth_utils.py",
    "backend/utils/pdf_utils.py",
    "ai_pipeline/__init__.py",
    "ai_pipeline/embeddings.py",
    "ai_pipeline/rag.py",
    "ai_pipeline/document_processor.py",
    "ai_pipeline/drug_checker.py",
    "patient_app/app.py",
    "patient_app/pages/dashboard.py",
    "patient_app/pages/upload.py",
    "patient_app/pages/chat.py",
    "patient_app/pages/share.py",
    "patient_app/pages/emergency_card.py",
    "doctor_app/app.py",
    "doctor_app/pages/patient_list.py",
    "doctor_app/pages/patient_view.py",
    "doctor_app/pages/clinical_chat.py",
    "doctor_app/pages/upload.py",
    "tests/__init__.py",
    "tests/test_auth.py",
    "tests/test_patient.py",
    "tests/test_doctor.py",
    "tests/test_chat.py",
    "data/mtsamples/.gitkeep",
    "data/demo/.gitkeep",
    "docs/.gitkeep"
)

foreach ($f in $files) {
    if ($f -match "/") {
        $dir = Split-Path $f
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Force -Path $dir | Out-Null
        }
    }
    if (-not (Test-Path $f)) {
        New-Item -ItemType File -Force -Path $f | Out-Null
    }
}
Write-Output "Folder structure and files created successfully."
