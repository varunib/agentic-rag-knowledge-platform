import os
import io
import csv
import json
import uuid
import re
import html
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

_executor = ThreadPoolExecutor(max_workers=2)

import chromadb
from groq import Groq
from dotenv import load_dotenv
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
from duckduckgo_search import DDGS

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
embedder = SentenceTransformer("all-MiniLM-L6-v2")
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

AVAILABLE_MODELS = {
    "llama-3.3-70b-versatile": "Llama 3.3 70B (Powerful)",
    "llama-3.1-8b-instant": "Llama 3.1 8B (Fast)",
    "llama3-70b-8192": "Llama 3 70B",
    "mixtral-8x7b-32768": "Mixtral 8x7B",
    "gemma2-9b-it": "Gemma 2 9B",
}

DEFAULT_MODEL = "llama-3.1-8b-instant"

chroma_client = chromadb.PersistentClient(path="./chroma_data")
global_collection = chroma_client.get_or_create_collection(name="documents")

sessions = {}

# BM25 index per session — rebuilt when documents are added/removed
_bm25_index: dict[str, BM25Okapi] = {}
_bm25_chunks: dict[str, list[dict]] = {}  # {session_id: [{text, metadata, id}]}

def _tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())

def _rebuild_bm25(session_id: str):
    chunks = _bm25_chunks.get(session_id, [])
    if not chunks:
        _bm25_index.pop(session_id, None)
        return
    _bm25_index[session_id] = BM25Okapi([_tokenize(c["text"]) for c in chunks])

def _get_session(session_id: str):
    if session_id not in sessions:
        sessions[session_id] = {
            "documents": [],
            "history": [],
            "model": DEFAULT_MODEL,
            "web_search": False,
            "active_file": None,
            "search_all_docs": False,
        }
    return sessions[session_id]

# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_text(content: bytes, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".pdf":
        reader = PdfReader(io.BytesIO(content))
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(f"[Page {i + 1}]\n{text}")
        return "\n".join(pages)
    elif ext == ".docx":
        from docx import Document
        doc = Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)
    elif ext == ".csv":
        text = content.decode("utf-8", errors="ignore")
        reader = csv.reader(io.StringIO(text))
        return "\n".join(" | ".join(row) for row in reader)
    elif ext == ".json":
        data = json.loads(content.decode("utf-8", errors="ignore"))
        return json.dumps(data, indent=2)
    elif ext == ".html":
        text = content.decode("utf-8", errors="ignore")
        clean = re.sub(r"<[^>]+>", " ", text)
        return re.sub(r"\s+", " ", html.unescape(clean)).strip()
    else:
        return content.decode("utf-8", errors="ignore")

# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 150) -> list[dict]:
    separators = ["\n\n", "\n", ". ", "! ", "? ", ", ", " "]
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        if end < text_len:
            best_sep = -1
            for sep in separators:
                pos = text.rfind(sep, start + chunk_size // 2, end)
                if pos > best_sep:
                    best_sep = pos
                    best_sep_str = sep
            if best_sep > 0:
                end = best_sep + len(best_sep_str)
        chunk_content = text[start:end].strip()
        if chunk_content:
            chunks.append({"text": chunk_content, "start": start, "end": end})
        start = end - chunk_overlap if end - chunk_overlap > start else end
        if start >= text_len:
            break
    return chunks if chunks else [{"text": text, "start": 0, "end": text_len}]

# ---------------------------------------------------------------------------
# Document processing
# ---------------------------------------------------------------------------

def process_document(content: bytes, filename: str, session_id: Optional[str] = None) -> dict:
    if not session_id:
        session_id = "default"
    try:
        session = _get_session(session_id)
        text = extract_text(content, filename)
        if not text.strip():
            return {"status": "error", "message": "No text could be extracted from the file."}

        session["active_file"] = filename
        session["history"] = []

        existing = global_collection.get(where={"$and": [{"session_id": session_id}, {"filename": filename}]})
        if existing["ids"]:
            if filename not in session["documents"]:
                session["documents"].append(filename)
            return {"status": "success", "message": f"Already indexed {filename}", "chunks": len(existing["ids"]), "characters": 0}

        chunks = chunk_text(text)
        embeddings = embedder.encode(
            [c["text"] for c in chunks], batch_size=64, show_progress_bar=False, convert_to_numpy=True
        ).tolist()
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [
            {"session_id": session_id, "filename": filename, "chunk_index": i, "start_char": c["start"], "end_char": c["end"]}
            for i, c in enumerate(chunks)
        ]
        global_collection.add(documents=[c["text"] for c in chunks], embeddings=embeddings, ids=ids, metadatas=metadatas)

        # Update BM25 index
        if session_id not in _bm25_chunks:
            _bm25_chunks[session_id] = []
        _bm25_chunks[session_id].extend(
            {"text": c["text"], "metadata": metadatas[i], "id": ids[i]} for i, c in enumerate(chunks)
        )
        _rebuild_bm25(session_id)

        if filename not in session["documents"]:
            session["documents"].append(filename)

        return {"status": "success", "message": f"Processed {filename}", "chunks": len(chunks), "characters": len(text)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------------------------
# List / delete documents
# ---------------------------------------------------------------------------

def list_documents(session_id: str) -> list:
    return _get_session(session_id)["documents"]

def delete_document(filename: str, session_id: str) -> dict:
    session = _get_session(session_id)
    results = global_collection.get(where={"$and": [{"session_id": session_id}, {"filename": filename}]})
    if results["ids"]:
        global_collection.delete(ids=results["ids"])
    if filename in session["documents"]:
        session["documents"].remove(filename)
    if session["active_file"] == filename:
        session["active_file"] = session["documents"][-1] if session["documents"] else None
    # Remove from BM25 index
    if session_id in _bm25_chunks:
        _bm25_chunks[session_id] = [c for c in _bm25_chunks[session_id] if c["metadata"].get("filename") != filename]
        _rebuild_bm25(session_id)
    return {"status": "success", "message": f"Deleted {filename}"}

# ---------------------------------------------------------------------------
# Web search
# ---------------------------------------------------------------------------

def web_search(query: str, num_results: int = 3) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results))
        if not results:
            return ""
        return "\n---\n".join(
            f"Title: {r.get('title', '')}\nBody: {r.get('body', '')}\nURL: {r.get('href', '')}"
            for r in results
        )
    except Exception:
        return ""

# ---------------------------------------------------------------------------
# Rerank with scores
# ---------------------------------------------------------------------------

def rerank_chunks(query: str, documents: list[str], metadatas: list[dict], ids: list[str], top_k: int = 3):
    if not documents:
        return [], [], [], []
    pairs = [[query, doc] for doc in documents]
    scores = reranker.predict(pairs, batch_size=8, show_progress_bar=False)
    min_s, max_s = min(scores), max(scores)
    range_s = max_s - min_s if max_s != min_s else 1
    normalized = [round(((s - min_s) / range_s) * 100) for s in scores]
    scored = sorted(zip(documents, metadatas, ids, normalized), key=lambda x: x[3], reverse=True)[:top_k]
    return [x[0] for x in scored], [x[1] for x in scored], [x[2] for x in scored], [x[3] for x in scored]

# ---------------------------------------------------------------------------
# Build context with citations + confidence scores
# ---------------------------------------------------------------------------

def build_context_with_citations(results, scores: list[int] = None) -> tuple[str, list[dict]]:
    documents = results.get("documents", [[]])[0] if results.get("documents") else []
    metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
    ids = results.get("ids", [[]])[0] if results.get("ids") else []
    if not documents:
        return "", []

    citations = []
    parts = []
    for i, doc in enumerate(documents):
        meta = metadatas[i] if i < len(metadatas) else {}
        ref_num = i + 1
        confidence = scores[i] if scores and i < len(scores) else None
        parts.append(f"[{ref_num}] {doc}")
        citations.append({
            "ref": ref_num,
            "text_preview": doc[:200],
            "filename": meta.get("filename", "unknown"),
            "chunk_index": meta.get("chunk_index", 0),
            "id": ids[i] if i < len(ids) else "",
            "confidence": confidence,
        })
    return "\n\n".join(parts), citations

# ---------------------------------------------------------------------------
# Query routing — LLM decides if question needs document search
# ---------------------------------------------------------------------------

def decide_query_route(question: str, has_active_document: bool, model: str = DEFAULT_MODEL) -> str:
    if not has_active_document:
        return "direct"
    # Fast keyword heuristic — no LLM call needed
    direct_kw = ["what is", "who is", "define", "explain", "how does", "tell me about", "what are"]
    q = question.lower()
    if any(k in q for k in direct_kw) and not any(k in q for k in ["document", "file", "pdf", "this", "it", "the report", "summarize"]):
        return "direct"
    return "document"

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

def build_system_prompt(context: str, question: str, web_results: str = "", low_confidence: bool = False) -> str:
    doc_section = f"Relevant excerpts from the uploaded document:\n{context}\n" if context.strip() else ""
    web_section = f"Web Search Results:\n{web_results}\n" if web_results else ""
    low_conf_note = "\nNote: The retrieved document excerpts have low relevance scores. If they don't answer the question well, say so clearly and answer from general knowledge.\n" if low_confidence else ""
    return f"""You are an expert AI assistant with broad knowledge across technology, science, and general topics.

{doc_section}{web_section}{low_conf_note}User Question: {question}

Instructions:
- Give a detailed, well-structured answer.
- If document excerpts are provided and relevant, use them and cite [1],[2] etc.
- If the question is general knowledge (not about the document), answer from your own expertise.
- Never refuse to answer. Always provide a complete helpful response.
- For technical terms use their standard technical definitions.
"""

# ---------------------------------------------------------------------------
# Retrieve chunks helper
# ---------------------------------------------------------------------------

async def retrieve_chunks(question: str, session_id: str, search_all: bool = False, vector_weight: float = 0.6):
    session = _get_session(session_id)
    loop = asyncio.get_event_loop()
    query_embedding = await loop.run_in_executor(_executor, lambda: embedder.encode([question]).tolist()[0])

    where_filter = {"session_id": session_id} if search_all else {
        "$and": [{"session_id": session_id}, {"filename": session["active_file"]}]
    }

    # --- Vector search ---
    try:
        fetch_n = 8
        results = global_collection.query(query_embeddings=[query_embedding], n_results=fetch_n, where=where_filter, include=["documents", "metadatas", "distances"])
    except Exception:
        return [], [], [], []

    vec_docs  = results.get("documents", [[]])[0] or []
    vec_metas = results.get("metadatas", [[]])[0] or []
    vec_ids   = results.get("ids", [[]])[0] or []
    vec_dists = results.get("distances", [[]])[0] or []
    vec_scores_map = {id_: 1 - dist for id_, dist in zip(vec_ids, vec_dists)}

    # --- BM25 search ---
    bm25_scores_map: dict[str, float] = {}
    bm25 = _bm25_index.get(session_id)
    all_chunks = _bm25_chunks.get(session_id, [])
    if bm25 and all_chunks:
        tokens = _tokenize(question)
        raw_scores = bm25.get_scores(tokens)
        max_score = max(raw_scores) if raw_scores.max() > 0 else 1.0
        for chunk, score in zip(all_chunks, raw_scores):
            meta = chunk["metadata"]
            if not search_all and meta.get("filename") != session["active_file"]:
                continue
            if meta.get("session_id") != session_id:
                continue
            bm25_scores_map[chunk["id"]] = float(score) / max_score

    # --- Hybrid fusion ---
    all_ids = set(vec_scores_map) | set(bm25_scores_map)
    id_to_meta = {id_: meta for id_, meta in zip(vec_ids, vec_metas)}
    id_to_doc  = {id_: doc  for id_, doc  in zip(vec_ids, vec_docs)}
    # fill in any BM25-only hits from cache
    for chunk in all_chunks:
        cid = chunk["id"]
        if cid not in id_to_doc:
            id_to_doc[cid]  = chunk["text"]
            id_to_meta[cid] = chunk["metadata"]

    fused = []
    for cid in all_ids:
        v = vec_scores_map.get(cid, 0.0)
        b = bm25_scores_map.get(cid, 0.0)
        fused.append((cid, vector_weight * v + (1 - vector_weight) * b))
    fused.sort(key=lambda x: x[1], reverse=True)
    top_ids = [cid for cid, _ in fused[:fetch_n]]

    docs  = [id_to_doc[cid]  for cid in top_ids if cid in id_to_doc]
    metas = [id_to_meta[cid] for cid in top_ids if cid in id_to_meta]
    ids   = [cid for cid in top_ids if cid in id_to_doc]

    return await loop.run_in_executor(_executor, lambda: rerank_chunks(question, docs, metas, ids))

# ---------------------------------------------------------------------------
# Answer question (non-streaming)
# ---------------------------------------------------------------------------

async def answer_question(question: str, session_id: str, model: Optional[str] = None,
                    enable_web_search: bool = False, structured: bool = True) -> dict:
    try:
        session = _get_session(session_id)
        model_name = model or session.get("model", DEFAULT_MODEL)

        route = decide_query_route(question, bool(session.get("active_file")), model_name)

        context, citations, chunks_found = "", [], 0
        low_confidence = False
        if route == "document" and session.get("active_file"):
            docs, metas, ids, scores = await retrieve_chunks(question, session_id, session.get("search_all_docs", False))
            chunks_found = len(docs)
            low_confidence = bool(scores) and max(scores) < 30
            context, citations = build_context_with_citations(
                {"documents": [docs], "metadatas": [metas], "ids": [ids]}, scores
            ) if docs else ("", [])

        web_results = ""
        if enable_web_search and not context:
            web_results = web_search(question)

        system_prompt = build_system_prompt(context, question, web_results, low_confidence)
        history = session["history"]
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history[-2:])
        messages.append({"role": "user", "content": question})

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(_executor, lambda: client.chat.completions.create(model=model_name, messages=messages, temperature=0.7, max_tokens=1024))
        answer = response.choices[0].message.content

        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer})

        return {
            "status": "success", "answer": answer, "citations": citations,
            "chunks_found": chunks_found, "route": route,
            "web_search_used": bool(web_results), "model_used": model_name,
        }
    except Exception as e:
        return {"status": "error", "answer": str(e)}

# ---------------------------------------------------------------------------
# Answer question (streaming)
# ---------------------------------------------------------------------------

async def answer_question_stream(question: str, session_id: str, model: Optional[str] = None,
                                  enable_web_search: bool = False, structured: bool = True):
    try:
        session = _get_session(session_id)
        model_name = model or session.get("model", DEFAULT_MODEL)

        # Emit retrieval status
        yield f"data: {json.dumps({'type': 'status', 'message': 'Analyzing question...'})}

"

        route = decide_query_route(question, bool(session.get("active_file")), model_name)

        context, citations, chunks_found = "", [], 0
        low_confidence = False

        if route == "document" and session.get("active_file"):
            yield f"data: {json.dumps({'type': 'status', 'message': 'Searching documents...'})}

"
            docs, metas, ids, scores = await retrieve_chunks(question, session_id, session.get("search_all_docs", False))
            chunks_found = len(docs)
            low_confidence = bool(scores) and max(scores) < 30
            context, citations = build_context_with_citations(
                {"documents": [docs], "metadatas": [metas], "ids": [ids]}, scores
            ) if docs else ("", [])
            yield f"data: {json.dumps({'type': 'status', 'message': f'Found {chunks_found} relevant chunks — generating answer...'})}

"
        else:
            yield f"data: {json.dumps({'type': 'status', 'message': 'Answering from knowledge base...'})}

"

        web_results = ""
        if enable_web_search and not context:
            web_results = web_search(question)

        system_prompt = build_system_prompt(context, question, web_results, low_confidence)
        history = session["history"]
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history[-2:])
        messages.append({"role": "user", "content": question})

        yield f"data: {json.dumps({'type': 'metadata', 'citations': citations, 'chunks_found': chunks_found, 'route': route, 'web_search_used': bool(web_results), 'model_used': model_name, 'low_confidence': low_confidence})}

"

        stream = client.chat.completions.create(
            model=model_name, messages=messages, temperature=0.7, max_tokens=1024, stream=True
        )

        full_answer = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                full_answer += delta
                yield f"data: {json.dumps({'type': 'chunk', 'content': delta})}

"

        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": full_answer})

        yield f"data: {json.dumps({'type': 'done'})}

"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}

"

# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

def clear_history(session_id: str) -> dict:
    session = _get_session(session_id)
    session["history"] = []
    return {"status": "success", "message": "Conversation history cleared."}

def get_history(session_id: str) -> list:
    return _get_session(session_id)["history"]

def set_model(session_id: str, model: str) -> dict:
    if model not in AVAILABLE_MODELS:
        return {"status": "error", "message": f"Unsupported model."}
    _get_session(session_id)["model"] = model
    return {"status": "success", "message": f"Model set to {model}"}

def get_settings(session_id: str) -> dict:
    session = _get_session(session_id)
    return {
        "model": session["model"],
        "web_search": session.get("web_search", False),
        "documents": session["documents"],
        "history_count": len(session["history"]) // 2,
    }

def set_web_search(session_id: str, enabled: bool) -> dict:
    _get_session(session_id)["web_search"] = enabled
    return {"status": "success", "message": f"Web search {'enabled' if enabled else 'disabled'}"}
