# MedBridge Deployment Guide

This project is easiest to deploy for free with:

- Backend: Render free web service
- Database: Supabase Postgres free tier
- Patient frontend: Streamlit Community Cloud
- Doctor frontend: Streamlit Community Cloud

## Before You Deploy

The backend currently stores uploaded files in `data/uploads` and ChromaDB data in `data/chromadb`.

That means:

- Free Render is good for demos and portfolio use
- Free Render is not reliable for long-term document storage
- Uploaded documents and vector data can be lost after restart, redeploy, or spin-down

For a true production deployment, move uploads and vector storage off the local filesystem.

## Environment Variables

Backend:

- `DATABASE_URL`
- `SECRET_KEY`
- `FRONTEND_URLS`
- `ENV=production`
- `GROQ_API_KEY` if you want AI summaries, follow-up extraction, and chat
- `GROQ_MODEL` optional
- `OPENAI_API_KEY` optional
- `ANTHROPIC_API_KEY` optional

Frontend apps:

- `BACKEND_URL`
- `DOCTOR_PORTAL_URL` optional for the patient app's doctor redirect message

You can start from `.env.example`.

## 1. Create a Supabase Database

1. Create a new Supabase project.
2. Go to `Project Settings` -> `Database`.
3. Copy the SQLAlchemy-style Postgres connection string.
4. Make sure the URL includes SSL, typically `?sslmode=require`.

Example:

```text
postgresql+psycopg2://postgres:password@host:5432/postgres?sslmode=require
```

Use this value for `DATABASE_URL` in Render.

## 2. Deploy the Backend on Render

This repo includes [render.yaml](/d:/Project/medbridge/render.yaml), but you can also configure the service manually.

Recommended Render settings:

- Environment: `Python`
- Build command: `pip install -r backend-requirements.txt`
- Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

Set these environment variables in Render:

- `PYTHON_VERSION=3.10.0`
- `DATABASE_URL=<your supabase postgres url>`
- `SECRET_KEY=<long random secret>`
- `FRONTEND_URLS=<patient streamlit url>,<doctor streamlit url>`
- `ENV=production`
- `GROQ_API_KEY=<optional but recommended>`
- `GROQ_MODEL=<optional>`
- `OPENAI_API_KEY=<optional>`
- `ANTHROPIC_API_KEY=<optional>`

After deploy, test:

- `/health`
- `/docs`

## 3. Deploy the Patient App on Streamlit Community Cloud

Create a new app with:

- Repository: this repo
- Main file path: `patient_app/app.py`

Advanced settings:

- Python version: `3.10`
- App URL name: your choice

Set app secrets or environment variables:

```toml
BACKEND_URL = "https://your-render-backend.onrender.com"
DOCTOR_PORTAL_URL = "https://your-doctor-app.streamlit.app"
```

Streamlit should install dependencies from `patient_app/requirements.txt`.

## 4. Deploy the Doctor App on Streamlit Community Cloud

Create a second Streamlit app with:

- Repository: this repo
- Main file path: `doctor_app/app.py`

Set:

```toml
BACKEND_URL = "https://your-render-backend.onrender.com"
```

Streamlit should install dependencies from `doctor_app/requirements.txt`.

## 5. Wire CORS Correctly

Once both Streamlit URLs exist, set Render `FRONTEND_URLS` to:

```text
https://your-patient-app.streamlit.app,https://your-doctor-app.streamlit.app
```

That allows your backend in [backend/main.py](/d:/Project/medbridge/backend/main.py) to accept requests from both deployed frontends.

## Known Free-Tier Limitations

- Render free web services spin down after inactivity
- Render free web services can restart at any time
- Render free web services do not provide persistent disks
- First request after idle can be slow
- Local uploads and Chroma data are not durable on free hosting

## Best Next Upgrade

If you want this to behave like a real app instead of a demo:

1. Move uploaded files to Supabase Storage or S3-compatible storage
2. Replace local Chroma persistence with pgvector/Supabase or another hosted vector store

That would make the deployment much more stable without changing the frontend architecture.
