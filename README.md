# Academic Question Answering System Using RAG

[![FastAPI](https://img.shields.io/badge/FastAPI-0.142+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-v1.4+-1C3C3C?style=flat&logo=chainlink&logoColor=white)](https://www.langchain.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Persistent-FF6F00?style=flat)](https://www.trychroma.com)
[![React](https://img.shields.io/badge/React-19+-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-v4+-38B2AC?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An academic-grade **Retrieval-Augmented Generation (RAG)** web application designed for students, researchers, and educators. Upload lecture notes, syllabus documents, textbooks, and research papers (PDF or DOCX) to ask deep technical questions. Answers are generated from retrieved material and include source citations (document name, page, chunk ID, and text excerpts).

Runs smoothly on standard 8GB RAM laptops (Windows/Linux/macOS) on CPU with zero local GPU requirements.

---

## Table of Contents
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [RAG Pipeline Workflow](#rag-pipeline-workflow)
- [Tech Stack](#tech-stack)
- [Directory Structure](#directory-structure)
- [Configuration & Environment Variables](#configuration--environment-variables)
- [Provider Switching (Gemini, OpenAI, Ollama)](#provider-switching)
- [Using Gemini (free)](#using-gemini-free)
- [Setup & Installation (Windows Native)](#setup--installation-windows-native)
- [Setup & Installation (Docker & Docker Compose)](#setup--installation-docker--docker-compose)
- [API Reference & cURL Examples](#api-reference--curl-examples)
- [Evaluation Harness](#evaluation-harness)
- [Storage Locations](#storage-locations)
- [Troubleshooting & FAQ](#troubleshooting--faq)
- [Future Improvements](#future-improvements)

---

## Key Features

- **Grounded RAG Pipeline**: Uses retrieved document context and official LangChain split packages (`langchain-chroma`, `langchain-huggingface`, `langchain-google-genai`, `langchain-openai`, `langchain-ollama`).
- **Relevance Threshold Guardrail**: If retrieved chunks do not exceed the relevance threshold, the system returns:
  `"I couldn't find enough information in the uploaded documents to answer this question."` without making an unnecessary LLM call.
- **Source Citations**: Responses show the source document, page, chunk ID, relevance score, and expandable text excerpt when retrieved.
- **Content Hash & Duplicate Prevention**: SHA-256 content hashing detects duplicate uploads instantly, preventing redundant embeddings and storage waste.
- **Conversational Context Condensation**: Multi-turn conversation history is condensed by the LLM into a standalone query before vector retrieval.
- **CPU-Friendly & 8GB RAM Certified**: Default embeddings use `sentence-transformers/all-MiniLM-L6-v2` (only ~80MB), running locally on CPU.
- **Provider Agnostic**: Switch between OpenAI (`gpt-4o-mini`), Google Gemini (`gemini-3.8-flash`), and local Ollama (`llama3.2:3b`), or swap embeddings between HuggingFace and OpenAI with a single `.env` toggle.
- **Embedding Mismatch Protection**: Vector store embeds provider/model metadata signatures; mismatches trigger explicit warnings or safe resets.
- **Modern Responsive UI**: Clean academic dark aesthetic with drag-and-drop PDF/DOCX ingestion, real-time progress indicators, copy actions, and clickable sample questions.

> **Important:** This system may produce inaccurate or hallucinated answers. Always verify against the source excerpts shown. Do not use for legal or medical advice without expert review.

---

## System Architecture

```text
+-------------------------------------------------------------------------+
|                              FRONTEND                                   |
|   React 19 + Vite + Tailwind CSS + Lucide Icons + React-Markdown        |
+------------------------------------+------------------------------------+
                                     |
                         HTTP / REST | JSON
                                     v
+------------------------------------+------------------------------------+
|                         FASTAPI BACKEND                                 |
|  +----------------------+ +--------------------+ +-------------------+  |
|  | /api/documents       | | /api/chat          | | /api/health       |  |
|  +----------------------+ +--------------------+ +-------------------+  |
|                                                                         |
|  [Document Service]                     [Chat Service]                  |
|   - Magic byte validation                - Conversational condenser     |
|   - SHA-256 hash dedup                   - Similarity retriever         |
|   - Text cleaner & sanitizer             - Relevance thresholding       |
|   - PyPDFLoader extraction               - Academic prompt synthesizer  |
+---------------------+----------------------------------+----------------+
                      |                                  |
           Dense Embeddings                   Grounded Synthesis
                      v                                  v
+---------------------+-------------+     +-------------------------------+
|          EMBEDDING LAYER          |     |           LLM LAYER           |
|  - HuggingFace (MiniLM-L6-v2)     |     |  - Gemini (gemini-3.8-flash) |
|  - OpenAI (text-embedding-3-small)|     |  - OpenAI (gpt-4o-mini)       |
|                                   |     |  - Ollama (llama3.2:3b local) |
+---------------------+-------------+     +-------------------------------+
                      |
                      v
+---------------------+-------------+
|        CHROMA VECTOR DB           |
|  - Persistent storage (HNSW)      |
|  - Cosine distance similarity     |
|  - Collection signature metadata  |
+-----------------------------------+
```

---

## RAG Pipeline Workflow

```text
[PDF or DOCX Upload]
     |
     v
[Validation: PDF/DOCX signature + extension + Size <= 25MB]
     |
     v
[SHA-256 Hash Calculation] ---> Duplicate Found? ---> Abort with Conflict (409)
     |
     v
[PyPDFLoader / Docx2txtLoader Extraction]
     |
     v
[Text Cleaning: Hyphenation fixes, control chars removed, whitespace normalized]
     |
     v
[RecursiveCharacterTextSplitter: chunk_size=800, overlap=150]
     |
     v
[Dense Embedding (HuggingFace / OpenAI)] ---> [ChromaDB Persistent Storage]

--------------------------------------------------------------------------

[Student Question + Chat History]
     |
     v
[Query Condensation: Rephrase follow-up into standalone query]
     |
     v
[Cosine Similarity Search (Top-k=4)]
     |
     v
[Relevance Score Threshold Check (Score >= 0.30)]
     |
     +--- (Below threshold / 0 chunks) ---> Return: "I couldn't find enough information..."
     |
     +--- (Passes threshold)
             |
             v
     [Context Synthesis: [Document: X, Page: Y] + Content]
             |
             v
     [Academic LLM Prompt (Gemini / OpenAI / Ollama)]
             |
             v
     [Answer + Deduplicated Source Citations]
```

---

## Tech Stack

### Backend
- **Python**: 3.10+ (tested through 3.13)
- **FastAPI & Uvicorn**: High-performance asynchronous web framework
- **Pydantic v2 & Pydantic-Settings**: Schema validation and environment management
- **LangChain Ecosystem**:
  - `langchain`, `langchain-community`, `langchain-core`
  - `langchain-chroma`: Vector store integration
  - `langchain-huggingface`: Local CPU sentence transformers
  - `langchain-google-genai`: Google Gemini integration
  - `langchain-openai`: OpenAI GPT & embedding integration
  - `langchain-ollama`: Local offline LLM execution
- **PyPDF**: PDF parsing and text stream decoding
- **Docx2txt**: Word document text extraction
- **ChromaDB**: Lightweight, embedded, persistent vector database
- **Sentence-Transformers & PyTorch**: Lightweight local embedding model (`all-MiniLM-L6-v2`)

### Frontend
- **React 19**: Modern component architecture
- **Vite 6/8**: Blazing fast ESM development and production bundler
- **Tailwind CSS v4**: Utility-first responsive design
- **Axios**: Network requests with progress tracking
- **React-Markdown**: Academic formatting for code, lists, and tables
- **Lucide React**: Clean icons

---

## Directory Structure

```text
academic-rag-system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat.py             # POST /api/chat
│   │   │   ├── documents.py        # Upload, list, delete routes
│   │   │   └── health.py           # GET /api/health
│   │   ├── core/
│   │   │   ├── config.py           # Pydantic Settings
│   │   │   ├── exceptions.py       # Custom HTTP exceptions
│   │   │   └── logging.py          # Structured logging
│   │   ├── models/
│   │   │   ├── chat.py             # ChatRequest, ChatResponse, SourceCitation
│   │   │   ├── document.py         # DocumentMetadata, UploadResponse
│   │   │   └── health.py           # HealthResponse
│   │   ├── rag/
│   │   │   ├── cleaner.py          # PDF text normalizer & hyphenation fixer
│   │   │   ├── embeddings.py       # Singleton embedding factory
│   │   │   ├── generator.py        # LLM factory (Gemini / OpenAI / Ollama)
│   │   │   ├── loader.py           # PDF/DOCX loader and text normalization
│   │   │   ├── pipeline.py         # End-to-end RAG orchestrator
│   │   │   ├── prompts.py          # Academic system prompt & condenser
│   │   │   ├── retriever.py        # Vector search with score thresholding
│   │   │   ├── splitter.py         # RecursiveCharacterTextSplitter wrapper
│   │   │   └── vectorstore.py      # ChromaDB client & collection manager
│   │   ├── services/
│   │   │   ├── chat_service.py     # Chat business logic
│   │   │   └── document_service.py # Ingestion & deletion logic
│   │   ├── utils/
│   │   │   ├── file_utils.py       # Magic bytes, hash & size formatting
│   │   │   └── manifest.py         # Persistent document metadata store
│   │   └── main.py                 # FastAPI application & CORS setup
│   ├── chroma_db/                  # Persistent Chroma storage directory
│   ├── sample_documents/           # Sample academic PDFs (DBMS, Networks, Cloud)
│   ├── tests/
│   │   └── test_gemini.py          # Gemini provider unit tests
│   ├── uploads/                    # Physical PDF storage directory
│   ├── create_sample_academic_pdfs.py # Generator for multi-page study PDFs
│   ├── evaluate.py                 # Dataset-based retrieval and answer evaluation
│   ├── ingest_sample_docs.py       # Helper to seed sample PDFs
│   ├── test_backend_pipeline.py    # Automated pipeline unit verification
│   ├── requirements.txt            # Pinned Python dependencies
│   ├── Dockerfile                  # Production container definition
│   └── .env.example                # Backend environment template
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatArea.jsx        # Messages stream & example questions
│   │   │   ├── ChatMessage.jsx     # Markdown bubbles & citation views
│   │   │   ├── DocumentList.jsx    # Ingested documents list & deletion
│   │   │   ├── Header.jsx          # Status badges & model details
│   │   │   ├── SourceCitations.jsx # Collapsible page & snippet badges
│   │   │   ├── Toast.jsx           # Notification alerts
│   │   │   └── UploadCard.jsx      # Drag-and-drop upload zone & progress
│   │   ├── services/
│   │   │   └── api.js              # Axios client
│   │   ├── App.jsx                 # Master application layout
│   │   ├── index.css               # Tailwind CSS v4 & custom styles
│   │   └── main.jsx                # React DOM root
│   ├── index.html                  # HTML entry point
│   ├── package.json                # Frontend dependencies
│   ├── vite.config.js              # Vite server & proxy configuration
│   ├── nginx.conf                  # Production Nginx reverse proxy
│   └── Dockerfile                  # Multi-stage production container
├── docker-compose.yml              # Multi-container orchestration
├── scripts/build_dataset.py        # Build retrieval benchmark dataset from sample documents
├── notebooks/eda.ipynb             # Dataset exploratory analysis and visualizations
├── docs/figures/                    # Exported EDA plot PNGs
├── dataset.csv                     # Cleaned retrieval/answer reference dataset
├── data_dictionary.csv             # Dataset column descriptions
├── .env.example                    # Global environment variables template
├── .gitignore                      # Git exclusion rules (.env, chroma_db, etc.)
└── README.md                       # Comprehensive documentation
```

---

## Configuration & Environment Variables

Copy `.env.example` to `backend/.env`:

```bash
cp .env.example backend/.env
```

### Complete Environment Variable Reference

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `LLM_PROVIDER` | `gemini` | Active LLM provider: `openai`, `gemini`, or `ollama` |
| `OPENAI_API_KEY` | *(empty)* | OpenAI API key (sk-...) |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI chat model name |
| `GOOGLE_API_KEY` | *(empty)* | Google Gemini API key (never commit this value) |
| `GEMINI_MODEL` | `gemini-3.8-flash` | Gemini chat model name; environment settings can override the default |
| `OLLAMA_MODEL` | `llama3.2:3b` | Ollama model name (e.g., `llama3.2:3b`, `mistral`) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server API URL |
| `EMBEDDING_PROVIDER` | `huggingface` | Active embedding provider: `huggingface` or `openai` |
| `HF_EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Local HuggingFace sentence transformer |
| `OPENAI_EMBEDDING_MODEL`| `text-embedding-3-small` | OpenAI embedding model name |
| `CHUNK_SIZE` | `800` | Target chunk size in characters |
| `CHUNK_OVERLAP` | `150` | Overlap between consecutive chunks in characters |
| `TOP_K` | `4` | Number of most similar chunks to retrieve |
| `SCORE_THRESHOLD` | `0.30` | Minimum cosine similarity score for relevance |
| `MAX_FILE_SIZE_MB` | `25` | Maximum allowed PDF or DOCX upload size in megabytes |

---

## Provider Switching

The backend is built with factory patterns (`get_llm()` and `get_embedding_function()`), making provider switching completely seamless without modifying application code.

### 1. Gemini (Free Cloud)
In `backend/.env`:
```env
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-3.8-flash

EMBEDDING_PROVIDER=huggingface
HF_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```
*Benefits*: Google Gemini cloud generation using the configured `GEMINI_MODEL` (default: `gemini-3.8-flash`). Availability and pricing depend on the Google AI account and model access. See the [Using Gemini](#using-gemini-free) section for configuration and rate-limit details.

### 2. OpenAI (Cloud Configuration)
In `backend/.env`:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-your-actual-api-key-here
OPENAI_MODEL=gpt-4o-mini

EMBEDDING_PROVIDER=huggingface
HF_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```
*Benefits*: Fast, high accuracy, highly cost-effective (`gpt-4o-mini`), with free local embeddings that keep costs minimal.

### 3. 100% Offline / Local Private (Ollama)
In `backend/.env`:
```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2:3b
OLLAMA_BASE_URL=http://localhost:11434

EMBEDDING_PROVIDER=huggingface
HF_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```
**Setup Ollama**:
1. Download & install [Ollama](https://ollama.ai).
2. Start the daemon:
   ```bash
   ollama serve
   ```
3. Pull the lightweight 3B model (runs smoothly on 8GB RAM):
   ```bash
   ollama pull llama3.2:3b
   ```
*Benefits*: 100% free, 100% private, no API keys, zero external internet dependencies.

### 4. Switching Embedding Providers & Vector Store Mismatch Protection
ChromaDB collections store an embedding signature (`signature = provider::model`).
- If you change `EMBEDDING_PROVIDER` (e.g. from `huggingface` to `openai`), the vector dimensions change (384 dims vs 1536 dims).
- The system automatically detects this mismatch and raises an `EmbeddingMismatchException` rather than returning corrupt search results.
- To re-index with a new embedding provider:
  ```bash
  # Delete previous Chroma storage to rebuild
  rmdir /s /q backend\chroma_db
  # Re-ingest documents
  python backend/ingest_sample_docs.py
  ```

---

## Using Gemini (free)

Gemini is the default LLM provider. Embeddings stay on HuggingFace so existing ChromaDB vectors remain valid (no re-indexing).

1. Create a free API key at [Google AI Studio](https://aistudio.google.com/apikey) (aistudio.google.com).
2. Put the key only in `backend/.env` (this file is gitignored):

```env
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-3.8-flash

EMBEDDING_PROVIDER=huggingface
HF_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

3. Restart the backend. Startup checks the configured model against the Gemini model list and logs a warning with the closest available suggestion if it is unavailable. `GET /api/health` should report `llm_provider: gemini` and `llm_model: gemini-3.8-flash` (the key is never returned).

The code default is `gemini-3.8-flash`; `GEMINI_MODEL` supplied through the process environment or `backend/.env` takes precedence. The application does not silently retry with another model: model/API errors are returned explicitly, and successful answer calls log the provider and model. Check the [official model list](https://ai.google.dev/gemini-api/docs/models) and ensure the selected model is available to your API project.

**429 troubleshooting**: The Gemini free tier is rate-limited. If you see `"Gemini free-tier rate limit reached. Please wait a minute and try again."`, wait about a minute and retry. Do not paste your API key into chat, logs, or the frontend.

---

## Setup & Installation (Windows Native)

### Prerequisites
- Windows 10/11
- Python 3.10+ (Python 3.13 supported)
- Node.js 18+ and npm
- [Git](https://git-scm.com/)

---

### Step 1: Clone Repository
```powershell
git clone <repository_url> academic-rag-system
cd academic-rag-system
```

---

### Step 2: Backend Setup
Open a PowerShell terminal:

```powershell
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment file
Copy-Item .env.example .env

# (Optional) Open .env in Notepad to insert GOOGLE_API_KEY (Gemini) or OPENAI_API_KEY (OpenAI)
notepad .env

# Generate sample academic PDFs (DBMS, Computer Networks, Cloud Computing)
python create_sample_academic_pdfs.py

# Ingest sample PDFs into ChromaDB
python ingest_sample_docs.py

# Verify the backend RAG pipeline
python test_backend_pipeline.py
```

#### Run the Backend Server
```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The API server is now live at:
- **API Base**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **Health Endpoint**: `http://127.0.0.1:8000/api/health`

---

### Step 3: Frontend Setup
Open a second PowerShell terminal:

```powershell
# Navigate to frontend directory
cd frontend

# Install npm dependencies
npm install

# Start Vite development server
npm run dev
```
Open your browser at:
**`http://localhost:5173`**

---

## Setup & Installation (Docker & Docker Compose)

Docker packages the full frontend, backend, and ChromaDB persistence in isolated containers.

### Prerequisites
- [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) with WSL2 backend.

### Launch with Docker Compose
From the project root:

```bash
# 1. Ensure .env is populated in backend/ (all settings including LLM_PROVIDER, GOOGLE_API_KEY, GEMINI_MODEL, and OPENAI_API_KEY reach the backend container via env_file)
cp .env.example backend/.env

# 2. Build and launch all containers
docker compose up --build
```

- **Frontend Application**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **Interactive API Documentation**: `http://localhost:8000/docs`

To stop containers:
```bash
docker compose down
```

---

## API Reference & cURL Examples

### 1. Health & System Status
```bash
curl -X GET http://127.0.0.1:8000/api/health
```
**Response**:
```json
{
  "status": "ok",
  "llm_provider": "gemini",
  "llm_model": "gemini-3.8-flash",
  "embedding_provider": "huggingface",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "document_count": 3,
  "total_chunks": 14,
  "collection_name": "academic_rag_docs",
  "chroma_status": "connected",
  "message": "Academic RAG System is operational."
}
```

---

### 2. Upload Academic PDFs or DOCX files (Multipart)
```bash
curl -X POST http://127.0.0.1:8000/api/documents/upload \
  -F "files=@sample_documents/DBMS_Study_Notes.pdf"
```
Use the same endpoint with `-F "files=@path/to/notes.docx"` to upload a Word document.
**Response**:
```json
{
  "success": true,
  "uploaded": [
    {
      "document_id": "a9b75822-491b-419b-a010-85f269a842f5",
      "filename": "DBMS_Study_Notes.pdf",
      "page_count": 3,
      "chunk_count": 5,
      "status": "ready",
      "message": "Successfully processed 3 pages and indexed 5 chunks."
    }
  ],
  "errors": []
}
```

---

### 3. List Ingested Documents
```bash
curl -X GET http://127.0.0.1:8000/api/documents
```
**Response**:
```json
{
  "total_documents": 1,
  "total_chunks": 5,
  "documents": [
    {
      "document_id": "a9b75822-491b-419b-a010-85f269a842f5",
      "filename": "DBMS_Study_Notes.pdf",
      "file_path": "uploads/a9b75822-491b-419b-a010-85f269a842f5_DBMS_Study_Notes.pdf",
      "file_hash": "0f810cf16cc1db22b274530fc601...",
      "file_size_bytes": 4485,
      "file_size_formatted": "4.4 KB",
      "page_count": 3,
      "chunk_count": 5,
      "upload_date": "2026-10-04T17:26:01.298506",
      "status": "ready"
    }
  ]
}
```

---

### 4. Delete Document & Purge Vectors
```bash
curl -X DELETE http://127.0.0.1:8000/api/documents/a9b75822-491b-419b-a010-85f269a842f5
```
**Response**:
```json
{
  "success": true,
  "document_id": "a9b75822-491b-419b-a010-85f269a842f5",
  "filename": "DBMS_Study_Notes.pdf",
  "deleted_chunks": 5,
  "message": "Document 'DBMS_Study_Notes.pdf' and 5 vectors successfully deleted."
}
```

---

### 5. Chat & Grounded Question Answering
```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is database normalization and what are the benefits of 3NF?",
    "chat_history": []
  }'
```
**Response**:
```json
{
  "answer": "Database normalization is a systematic approach to decomposing tables to eliminate data redundancy and prevent undesirable anomalies (Insertion, Update, and Deletion anomalies).\n\nKey benefits of Third Normal Form (3NF):\n- Eliminates transitive functional dependencies on the primary key.\n- Minimizes duplicate data storage.\n- Simplifies data consistency and modification integrity.",
  "sources": [
    {
      "document": "DBMS_Study_Notes.pdf",
      "page": 2,
      "content": "Chapter 2: Database Normalization and Normal Forms\nUnderstanding Normalization (1NF, 2NF, 3NF, BCNF)...",
      "score": 0.7835
    }
  ],
  "standalone_question": null
}
```

---

### 6. Irrelevant Question (Relevance Threshold Response)
```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the recipe for baking chocolate chip cookies?",
    "chat_history": []
  }'
```
**Response**:
```json
{
  "answer": "I couldn't find enough information in the uploaded documents to answer this question.",
  "sources": [],
  "standalone_question": null
}
```

---

## Evaluation Harness

`backend/evaluate.py` reads query/reference rows from `dataset.csv`, evaluates retrieval source/score, reference-answer keyword overlap, and end-to-end response latency, and records timestamped results in `evaluation_results/results.csv` and `evaluation_results/summary.md`. The answer-quality score is token recall against the retrieved reference excerpt; it is a lightweight heuristic, not a human or model-based faithfulness assessment.

From the repository root, build the retrieval dataset from sample documents and run the evaluation:
```powershell
python scripts/build_dataset.py
python backend/evaluate.py
```

The dataset builder uses the configured embedding provider to retrieve sample chunks and stores each retrieved source excerpt as a reference answer. The evaluation invokes the configured LLM to produce answers. Configure the selected provider before running evaluation; dataset generation does not invoke an LLM.

The notebook `notebooks/eda.ipynb` contains four executed plots. PNG exports are saved under `docs/figures/`. To reproduce them, open and run the notebook from the repository root after installing `backend/requirements.txt`.

---

## Storage Locations

- **Uploaded PDFs and DOCX files**: Stored on disk under `backend/uploads/` (prefixed with document UUID to prevent file collisions).
- **Persistent ChromaDB Vectors**: Stored on disk under `backend/chroma_db/` (HNSW SQLite index and binary embeddings).
- **Document Metadata Registry**: Stored in `backend/uploads/documents_manifest.json`.

---

## Troubleshooting & FAQ

### 1. `MissingAPIKeyException: 401 Missing OpenAI API key`
- **Cause**: `LLM_PROVIDER=openai` is selected in `backend/.env`, but `OPENAI_API_KEY` is blank or unset.
- **Solution**: Open `backend/.env` and add your OpenAI key:
  ```env
  OPENAI_API_KEY=sk-proj-...
  ```
  Or switch to Gemini:
  ```env
  LLM_PROVIDER=gemini
  GOOGLE_API_KEY=your_google_api_key_here
  ```
  Or switch to Ollama:
  ```env
  LLM_PROVIDER=ollama
  ```

### 2. `MissingAPIKeyException: 401 Missing Google Gemini API key`
- **Cause**: `LLM_PROVIDER=gemini` is selected, but `GOOGLE_API_KEY` is blank or invalid.
- **Solution**: Create a key at [Google AI Studio](https://aistudio.google.com/apikey) and set `GOOGLE_API_KEY` in `backend/.env`:
  ```env
  LLM_PROVIDER=gemini
  GOOGLE_API_KEY=your_google_api_key_here
  ```
  Or switch to Ollama:
  ```env
  LLM_PROVIDER=ollama
  ```

### 3. `GeminiRateLimitException: 429 Gemini free-tier rate limit reached`
- **Cause**: The Gemini free-tier quota was exceeded (too many requests in a short window).
- **Solution**: Wait about a minute and try the question again.

### 4. `OllamaNotRunningException: 503 Ollama is not running`
- **Cause**: `LLM_PROVIDER=ollama` is selected, but the Ollama daemon is not started.
- **Solution**: Start Ollama in your terminal:
  ```bash
  ollama serve
  ollama pull llama3.2:3b
  ```

### 5. `ScannedPDFException: 422 Scanned PDF or non-extractable text`
- **Cause**: The uploaded PDF consists of scanned raster images or photos without an embedded digital text layer.
- **Solution**: Upload PDFs generated with digital text (e.g., exported from Word, LaTeX, Google Docs, or converted with OCR).

### 6. `DuplicateDocumentException: 409 Duplicate document detected`
- **Cause**: The PDF content has the exact same SHA-256 hash as an already indexed file.
- **Solution**: The file is already indexed. You can query it directly in the chat or delete the existing document first.

### 7. `EmbeddingMismatchException: 409 Embedding configuration mismatch`
- **Cause**: You changed `EMBEDDING_PROVIDER` or `HF_EMBEDDING_MODEL` after already creating vectors with another model.
- **Solution**: Delete `backend/chroma_db/` and re-ingest documents so vectors match the new dimensionality.

---

## Future Improvements

- [ ] **OCR Ingestion**: Add `pytesseract` or `easyocr` fallback for scanned handwritten lecture notes.
- [ ] **Hybrid Search**: Combine dense embeddings with BM25 sparse lexical search (Reciprocal Rank Fusion) for exact keyword/formula queries.
- [ ] **PDF In-Browser Highlighting**: Use PDF.js in the frontend to highlight cited bounding boxes directly on the document page.
- [ ] **Cross-Encoder Re-ranking**: Add `cross-encoder/ms-marco-MiniLM-L-6-v2` for second-stage candidate re-ranking.
- [ ] **User Authentication & Multi-Tenancy**: Support separate user workspaces and private study groups with SQLite/PostgreSQL auth.

---

## License
MIT License. Built for students, developers, and researchers.