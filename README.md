# ragassistantfordocs
This project is a Django-based web backend application designed to handle intelligent document upload, processing, and querying. It enables users to upload .pdf, .docx, or .txt documents, automatically processes their contents, and allows users to ask questions about the content using AI-powered query capabilities.


RAG Project - Comprehensive Setup Guide
A Full-Stack Document Q&A System with Django Backend & React Frontend
images:
![Screenshot 2025-05-31 234754](https://github.com/user-attachments/assets/3e4431a9-631c-4e2b-ab2b-9db878b99897)
/00ad6517-1feb-48d3-98ee-3c091f9781e5)
![image](https://github.com/user-attachments/assets/fab5191a-b543-4b37-849c-f7e9e24fb8fd)
![image](https://github.com/user-attachments/assets/7694e5fb-c929-4184-aa7e-995c367c3e67)
![image](https://github.com/user-attachments/assets/f44e9623-087b-4b5f-9c91-0aff3c83d016)
![image](https://github.com/user-attachments/assets/31d8f6d4-04a6-4043-b62b-3a035806b59f)
![image](https://github.com/user-attachments/assets/caf7ee4c-18a6-4f85-a648-d67615bcf695)



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
