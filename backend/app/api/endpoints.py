"""
FastAPI REST API Endpoints

Routes:
    POST   /api/upload          — Upload single or multiple PDFs
    POST   /api/ask             — RAG-based question answering
    POST   /api/detect-risk     — On-demand risk assessment
    GET    /api/documents       — List all indexed documents
    DELETE /api/documents/{id}  — Delete a document
    GET    /api/risks           — List all flagged risks
    GET    /api/health          — System health diagnostics
"""

from fastapi import APIRouter, UploadFile, File, Request, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
import logging
from app.services.document_processor import DocumentProcessor, split_into_sentences

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------
class AskRequest(BaseModel):
    query: str
    doc_ids: Optional[List[str]] = None


class RiskDetectRequest(BaseModel):
    text: Optional[str] = None
    doc_id: Optional[str] = None


# ---------------------------------------------------------------------------
# POST /upload
# ---------------------------------------------------------------------------
@router.post("/upload")
async def upload_documents(
    request: Request,
    files: List[UploadFile] = File(...),
):
    """
    Upload single or multiple PDF documents.

    Pipeline: save → extract text → chunk → embed in FAISS → detect risks → save to SQLite.
    """
    db = request.app.state.db
    vs = request.app.state.vector_store
    rd = request.app.state.risk_detector

    if os.environ.get("VERCEL"):
        upload_dir = "/tmp/uploads"
    else:
        upload_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "uploads",
        )
    os.makedirs(upload_dir, exist_ok=True)


    results = []

    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            logger.warning(f"Skipping non-PDF file: {file.filename}")
            continue

        doc_id = str(uuid.uuid4())
        filename = file.filename
        filepath = os.path.join(upload_dir, f"{doc_id}_{filename}")

        try:
            # 1. Save file to disk
            contents = await file.read()
            with open(filepath, "wb") as f:
                f.write(contents)

            # 2. Create DB record
            db.add_document(doc_id, filename, filepath)

            # 3. Extract text page by page
            pages = DocumentProcessor.extract_text_from_pdf(contents)
            if not pages:
                db.update_document_status(doc_id, "failed")
                raise ValueError("Could not extract any text from the PDF.")

            # 4. Create overlapping chunks
            chunks = DocumentProcessor.create_chunks(pages, chunk_size=500, overlap=100)

            # 5. Store chunks in SQLite
            db_chunks = []
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_c{i}"
                db_chunks.append({
                    "id": chunk_id,
                    "doc_id": doc_id,
                    "page_num": chunk["metadata"]["page_num"],
                    "text": chunk["text"],
                })
            db.add_chunks(db_chunks)

            # 6. Index in FAISS vector store
            vs.add_documents(doc_id, filename, chunks)

            # 7. Run risk detection on all sentences
            sentences = DocumentProcessor.get_sentences_with_metadata(pages)
            detected_risks = rd.detect_risks_in_document(doc_id, sentences)

            # 8. Save risks to DB
            db.add_risks(detected_risks)

            # 9. Mark as processed
            db.update_document_status(doc_id, "processed")

            results.append({
                "document_id": doc_id,
                "filename": filename,
                "status": "processed",
                "chunks_count": len(chunks),
                "risks_count": len(detected_risks),
            })

        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            db.update_document_status(doc_id, "failed")
            results.append({
                "document_id": doc_id,
                "filename": filename,
                "status": f"failed: {str(e)}",
            })

    return results


# ---------------------------------------------------------------------------
# POST /ask
# ---------------------------------------------------------------------------
@router.post("/ask")
async def ask_question(request: Request, body: AskRequest):
    """RAG-based question answering with document citations."""
    vs = request.app.state.vector_store
    qa = request.app.state.qa_service

    query = body.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        retrieved = vs.search(query, top_k=5, doc_ids=body.doc_ids)
        return qa.answer_question(query, retrieved)
    except Exception as e:
        logger.error(f"QA error for '{query}': {e}")
        raise HTTPException(status_code=500, detail=f"QA processing failed: {e}")


# ---------------------------------------------------------------------------
# POST /detect-risk
# ---------------------------------------------------------------------------
@router.post("/detect-risk")
async def detect_risk_endpoint(request: Request, body: RiskDetectRequest):
    """On-demand risk assessment on raw text or a stored document."""
    rd = request.app.state.risk_detector
    db = request.app.state.db

    if body.text:
        try:
            sentences = [
                {"text": s, "page_num": 1}
                for s in split_into_sentences(body.text)
            ]
            risks = rd.detect_risks_in_document("on_demand", sentences)
            return {"text": body.text, "risks": risks}
        except Exception as e:
            logger.error(f"On-demand risk assessment error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    elif body.doc_id:
        try:
            chunks = db.get_document_chunks(body.doc_id)
            if not chunks:
                raise HTTPException(status_code=404, detail="Document chunks not found.")

            sentences = []
            for chunk in chunks:
                for s in split_into_sentences(chunk["text"]):
                    sentences.append({"text": s, "page_num": chunk["page_num"]})

            risks = rd.detect_risks_in_document(body.doc_id, sentences)
            return {"document_id": body.doc_id, "risks": risks}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Document risk scan error for {body.doc_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(
            status_code=400,
            detail="Must provide either 'text' or 'doc_id'.",
        )


# ---------------------------------------------------------------------------
# GET /documents
# ---------------------------------------------------------------------------
@router.get("/documents")
async def get_documents(request: Request):
    """List all indexed documents with risk statistics."""
    db = request.app.state.db
    try:
        return db.get_all_documents()
    except Exception as e:
        logger.error(f"Error retrieving documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve documents.")


# ---------------------------------------------------------------------------
# DELETE /documents/{doc_id}
# ---------------------------------------------------------------------------
@router.delete("/documents/{doc_id}")
async def delete_document(request: Request, doc_id: str):
    """Delete a document and clean up FAISS index + database records."""
    db = request.app.state.db
    vs = request.app.state.vector_store

    try:
        deleted = db.delete_document(doc_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found.")
        vs.remove_document(doc_id)
        return {"document_id": doc_id, "status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET /risks
# ---------------------------------------------------------------------------
@router.get("/risks")
async def get_risks(
    request: Request,
    doc_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
):
    """Retrieve flagged compliance risks with optional filters."""
    db = request.app.state.db
    try:
        return db.get_risks(doc_id=doc_id, severity=severity)
    except Exception as e:
        logger.error(f"Error retrieving risks: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve risks.")


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------
@router.get("/health")
async def health_check(request: Request):
    """System health and diagnostics endpoint."""
    db = request.app.state.db
    vs = request.app.state.vector_store
    qa = request.app.state.qa_service

    try:
        summary = db.get_risk_summary()
        db_ok = True
    except Exception as e:
        logger.error(f"Health check DB error: {e}")
        summary = {}
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "database": {
            "connected": db_ok,
            "total_documents": summary.get("total_documents", 0),
            "total_risks": summary.get("total_risks", 0),
        },
        "vector_store": {
            "indexed_chunks": len(vs.chunks),
            "faiss_active": vs.faiss_index is not None,
        },
        "qa_service": {
            "qa_model_loaded": qa.qa_pipeline is not None,
            "fallback_active": not qa.use_qa_model_env or qa.qa_pipeline is None,
        },
    }
