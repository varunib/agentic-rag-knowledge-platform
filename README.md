# Agentic RAG Knowledge Platform

An agentic document question-answering application. Upload documents, ask questions in a chat interface, and get answers grounded in retrieved content with citations. The backend uses a LangGraph workflow to route requests to document retrieval or tools such as web search, CSV analysis, SQL, and calculations.

## Features

- Upload and index PDF, DOCX, CSV, JSON, HTML, and plain-text documents.
- Ask questions about uploaded content and receive cited answers.
- Summarize documents and maintain conversational sessions.
- Choose a Groq-supported language model and optionally enable web search.
- Manage uploaded documents and chat history from the web interface.
- Retrieve document passages using ChromaDB, BM25, and cross-encoder reranking.

## Technology

- Frontend: React, Vite, and Axios
- Backend: FastAPI and LangGraph
- Retrieval and storage: ChromaDB, Sentence Transformers, and BM25
- Language models: Groq API

## Requirements

- Python 3.11 or newer
- Node.js 22 or newer
- A Groq API key

## Run Locally

### Backend

In a terminal, create a virtual environment and install the backend dependencies:

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install langgraph
```

The published `backend/requirements.txt` does not yet include LangGraph, although the backend imports it; install it separately as shown above.

Create `backend/.env` and add your API key:

```dotenv
GROQ_API_KEY=your_groq_api_key
```

Start the API from the `backend` directory:

```powershell
uvicorn main:app --reload --port 8000
```

The API root is `http://localhost:8000`; interactive API documentation is at `http://localhost:8000/docs`.

### Frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL printed in the terminal (usually `http://localhost:5173`). The frontend connects to the backend at `http://localhost:8000`.

## Data and Configuration

- Set `GROQ_API_KEY` in `backend/.env`. Keep this key private and do not commit it.
- ChromaDB stores its persistent data in `backend/chroma_data/` when the backend is run from `backend/`.
- The Docker Compose files are included, but the frontend Dockerfile references `frontend/nginx.conf`, which is not currently present. Use the local development steps above unless that deployment configuration has been added.

## API Overview

- `POST /upload` — upload and index a document
- `POST /ask` — ask a question
- `POST /ask/stream` — ask a question with streamed responses
- `GET /documents` — list indexed documents
- `GET /models` — list available models
- `GET /docs` — interactive FastAPI documentation