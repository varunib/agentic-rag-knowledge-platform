import json
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

from rag import (
    process_document,
    answer_question,
    answer_question_stream,
    list_documents,
    delete_document,
    clear_history,
    get_history,
    set_model,
    get_settings,
    set_web_search,
    AVAILABLE_MODELS,
)

app = FastAPI(title="Advanced RAG Assistant API")

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class QuestionRequest(BaseModel):
    question: str
    session_id: str
    model: Optional[str] = None
    web_search: Optional[bool] = False
    structured: Optional[bool] = True

class ModelRequest(BaseModel):
    session_id: str
    model: str

class WebSearchRequest(BaseModel):
    session_id: str
    enabled: bool

class DeleteDocRequest(BaseModel):
    session_id: str
    filename: str

# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {"status": "running", "message": "Advanced RAG Assistant API"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@app.get("/models")
def get_models():
    return {"models": AVAILABLE_MODELS}

# ---------------------------------------------------------------------------
# Upload Document
# ---------------------------------------------------------------------------

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = Query("default"),
):
    try:
        content = await file.read()
        result = process_document(content, file.filename, session_id)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------------------------
# Document Management
# ---------------------------------------------------------------------------

@app.get("/documents")
def get_documents(session_id: str = Query("default")):
    return {"documents": list_documents(session_id)}

@app.post("/documents/delete")
def delete_document_endpoint(req: DeleteDocRequest):
    return delete_document(req.filename, req.session_id)

# ---------------------------------------------------------------------------
# Ask (non-streaming)
# ---------------------------------------------------------------------------

@app.post("/ask")
async def ask_question(req: QuestionRequest):
    try:
        result = answer_question(
            question=req.question,
            session_id=req.session_id,
            model=req.model,
            enable_web_search=req.web_search or False,
            structured=req.structured,
        )
        return result
    except Exception as e:
        return {"status": "error", "answer": str(e)}

# ---------------------------------------------------------------------------
# Ask (streaming SSE)
# ---------------------------------------------------------------------------

@app.post("/ask/stream")
async def ask_question_stream_endpoint(req: QuestionRequest):
    return StreamingResponse(
        answer_question_stream(
            question=req.question,
            session_id=req.session_id,
            model=req.model,
            enable_web_search=req.web_search or False,
            structured=req.structured,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

# ---------------------------------------------------------------------------
# Session Management
# ---------------------------------------------------------------------------

@app.get("/session")
def get_session_settings(session_id: str = Query("default")):
    return get_settings(session_id)

@app.post("/session/clear")
def clear_session_history(session_id: str = Query("default")):
    return clear_history(session_id)

@app.get("/session/history")
def session_history(session_id: str = Query("default")):
    return {"history": get_history(session_id)}

@app.post("/session/model")
def set_session_model(req: ModelRequest):
    return set_model(req.session_id, req.model)

@app.post("/session/web-search")
def set_session_web_search(req: WebSearchRequest):
    return set_web_search(req.session_id, req.enabled)

# ---------------------------------------------------------------------------
# Run Server
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
