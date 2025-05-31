# ragassistantfordocs
This project is a Django-based web backend application designed to handle intelligent document upload, processing, and querying. It enables users to upload .pdf, .docx, or .txt documents, automatically processes their contents, and allows users to ask questions about the content using AI-powered query capabilities.


RAG Project - Comprehensive Setup Guide
A Full-Stack Document Q&A System with Django Backend & React Frontend
images:
![1000053679](https://github.com/user-attachments/assets/9906c1e0-a41b-4a22-94c3-11a65a5d6594)
![1000053678](https://github.com/user-attachments/assets/53e3a51f-119b-4dcc-89bf-e0d13843c2c2)
![1000053677](https://github.com/user-attachments/assets/b2a0b050-d7cc-4767-8026-057abf460955)
![1000053694](https://github.com/user-attachments/assets/aca80fac-105c-4895-8aa3-9ed639f7f276)
![1000053681](https://github.com/user-attachments/assets/ef429138-1c74-4052-9d59-9aae4ac91395)
![1000053680](https://github.com/user-attachments/assets/80bed8aa-6669-4201-9c15-e7552e1c42d9)








📌 Table of Contents
Project Overview

Prerequisites

Backend Setup

Frontend Setup

Running the Project

Data Storage & Workflow

Fallback Logic (LM Studio → Groq)

Troubleshooting

Deployment Notes

🚀 Project Overview
This project is a Retrieval-Augmented Generation (RAG) system that:

Uploads documents (PDF, DOCX, TXT)

Processes them into searchable chunks (stored in ChromaDB)

Answers questions using AI (LM Studio or Groq as fallback)

Tech Stack
Component	Technology
Backend	Django + Django REST Framework
Vector DB	ChromaDB (local storage)
Embeddings	all-MiniLM-L6-v2 (Sentence Transformers)
Frontend	React + TypeScript + TailwindCSS
LLM	LM Studio (local) / Groq (cloud fallback)
📋 Prerequisites
System Requirements:

OS: Windows/macOS/Linux

RAM: 8GB+ (16GB recommended for LM Studio)

Python: 3.9+

Node.js: 18.x

Accounts & API Keys:

Groq API Key (free tier available)

(Optional) LM Studio installed locally

🔧 Backend Setup (Django)
1. Clone the Repository
bash
git clone https://github.com/your-repo/ragproj.git
cd ragproj/backend
2. Set Up a Virtual Environment
bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate    # Windows
3. Install Dependencies
bash
pip install -r requirements.txt
4. Configure Django
Edit backend/settings.py:

python
# Allow frontend connections
CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]
# ChromaDB path (default: "E:/ragproj/chromadb_data")
CHROMA_DB_PATH = os.path.join(BASE_DIR, "chromadb_data")
5. Run Migrations & Start Server
bash
python manage.py migrate
python manage.py runserver
Backend runs at: http://localhost:8000

🎨 Frontend Setup (React)
1. Navigate to the Frontend
bash
cd ../frontend
2. Install Dependencies
bash
npm install
3. Configure API Endpoints
Edit src/services/api.ts:

typescript
const BASE_URL = "http://localhost:8000/api";  // Django backend
4. Start the Frontend
bash
npm start
Frontend runs at: http://localhost:3000

⚙️ Running the Project
1. Upload a Document
Go to http://localhost:3000/upload

Drag & drop a file (PDF/DOCX/TXT)

Backend processes it → stores in ChromaDB + SQLite

2. Ask Questions
Navigate to http://localhost:3000/document/:id

Type a question (e.g., "Summarize this document")

🗃️ Data Storage & Workflow
1. ChromaDB (Vector Storage)
Location: backend/chromadb_data/

Contains:

Document chunks (text)

Embeddings (vector representations)

Metadata (doc ID, chunk index)

2. SQLite (Metadata)
Location: backend/db.sqlite3

Tables:

api_document: File info (title, status, page count)

3. Processing Flow
File uploaded → Django saves to media/

processor.py extracts text → splits into chunks

Chunks are embedded → stored in ChromaDB

Frontend queries ChromaDB + LLM for answers

🔄 Fallback Logic
If LM Studio fails, the system switches to Groq:

1. LM Studio (Local)
Default: Runs at http://localhost:1234

Model: mistral (configured in rag.py)

2. Groq (Cloud Fallback)
Triggered when:

LM Studio is offline

API request times out

Models used:

llama3-70b-8192 (complex queries)

llama3-8b-8192 (simple queries)

3. Final Fallback
If both fail, returns raw document chunks (no LLM).

🐛 Troubleshooting
Issue	Solution
ChromaDB not saving	Check folder permissions (chromadb_data)
LM Studio not responding	Ensure it’s running on port 1234
Groq API errors	Verify API key in rag.py
Frontend CORS errors	Update CORS_ALLOWED_ORIGINS in Django
🚀 Deployment Notes
Backend: Use gunicorn + nginx for production.

Frontend: Build with npm run build → deploy to Vercel/Netlify.

ChromaDB: For production, consider Dockerizing or using a cloud-hosted version.
