"""
SQLite Database Manager

Manages the persistence layer for documents, text chunks, and detected risks
using Python's built-in sqlite3 module with foreign-key cascade support.
"""

import sqlite3
import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

if os.environ.get("VERCEL"):
    DB_PATH = "/tmp/compliance_qa.db"
else:
    DB_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "compliance_qa.db",
    )



class DatabaseManager:
    """Thread-safe SQLite database wrapper with connection-per-call pattern."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        """Creates tables if they don't already exist."""
        logger.info(f"Initializing SQLite database at: {self.db_path}")
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id       TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    upload_time TEXT NOT NULL,
                    status   TEXT NOT NULL,
                    filepath TEXT NOT NULL
                );
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id       TEXT PRIMARY KEY,
                    doc_id   TEXT NOT NULL,
                    page_num INTEGER NOT NULL,
                    text     TEXT NOT NULL,
                    FOREIGN KEY (doc_id) REFERENCES documents (id) ON DELETE CASCADE
                );
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS risks (
                    id                    TEXT PRIMARY KEY,
                    doc_id                TEXT NOT NULL,
                    risk_type             TEXT NOT NULL,
                    severity              TEXT NOT NULL,
                    page_num              INTEGER NOT NULL,
                    text                  TEXT NOT NULL,
                    confidence            REAL NOT NULL,
                    classification_method TEXT NOT NULL,
                    FOREIGN KEY (doc_id) REFERENCES documents (id) ON DELETE CASCADE
                );
            """)
            conn.commit()

    # ------------------------------------------------------------------
    # Document CRUD
    # ------------------------------------------------------------------
    def add_document(self, doc_id: str, filename: str, filepath: str) -> Dict[str, Any]:
        upload_time = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO documents (id, filename, upload_time, status, filepath) "
                "VALUES (?, ?, ?, ?, ?)",
                (doc_id, filename, upload_time, "processing", filepath),
            )
            conn.commit()
        return {
            "id": doc_id,
            "filename": filename,
            "upload_time": upload_time,
            "status": "processing",
            "filepath": filepath,
        }

    def update_document_status(self, doc_id: str, status: str):
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE documents SET status = ? WHERE id = ?",
                (status, doc_id),
            )
            conn.commit()

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Retrieves all documents with aggregated risk statistics."""
        with self._get_connection() as conn:
            query = """
                SELECT d.*,
                       COUNT(r.id) AS total_risks,
                       SUM(CASE WHEN r.severity = 'HIGH'   THEN 1 ELSE 0 END) AS high_risks,
                       SUM(CASE WHEN r.severity = 'MEDIUM' THEN 1 ELSE 0 END) AS medium_risks,
                       SUM(CASE WHEN r.severity = 'LOW'    THEN 1 ELSE 0 END) AS low_risks
                FROM documents d
                LEFT JOIN risks r ON d.id = r.doc_id
                GROUP BY d.id
                ORDER BY d.upload_time DESC
            """
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def delete_document(self, doc_id: str) -> bool:
        """Cascade-deletes a document and its associated chunks/risks."""
        doc = self.get_document(doc_id)
        if not doc:
            return False

        # Remove physical PDF file
        if os.path.exists(doc["filepath"]):
            try:
                os.remove(doc["filepath"])
            except Exception as e:
                logger.error(f"Error removing PDF file {doc['filepath']}: {e}")

        with self._get_connection() as conn:
            conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            conn.commit()
        return True

    # ------------------------------------------------------------------
    # Chunk CRUD
    # ------------------------------------------------------------------
    def add_chunks(self, chunks: List[Dict[str, Any]]):
        if not chunks:
            return
        with self._get_connection() as conn:
            conn.executemany(
                "INSERT INTO chunks (id, doc_id, page_num, text) VALUES (?, ?, ?, ?)",
                [(c["id"], c["doc_id"], c["page_num"], c["text"]) for c in chunks],
            )
            conn.commit()

    def get_document_chunks(self, doc_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM chunks WHERE doc_id = ? ORDER BY page_num ASC",
                (doc_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    # ------------------------------------------------------------------
    # Risk CRUD
    # ------------------------------------------------------------------
    def add_risks(self, risks: List[Dict[str, Any]]):
        if not risks:
            return
        with self._get_connection() as conn:
            conn.executemany(
                "INSERT INTO risks "
                "(id, doc_id, risk_type, severity, page_num, text, confidence, classification_method) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        r["id"], r["doc_id"], r["risk_type"], r["severity"],
                        r["page_num"], r["text"], r["confidence"],
                        r["classification_method"],
                    )
                    for r in risks
                ],
            )
            conn.commit()

    def get_risks(
        self,
        doc_id: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = """
            SELECT r.*, d.filename AS document_name
            FROM risks r
            JOIN documents d ON r.doc_id = d.id
        """
        params: list = []
        conditions: list = []

        if doc_id:
            conditions.append("r.doc_id = ?")
            params.append(doc_id)
        if severity:
            conditions.append("r.severity = ?")
            params.append(severity.upper())

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY r.severity DESC, d.filename ASC"

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------
    def get_risk_summary(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            total_docs = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            total_risks = conn.execute("SELECT COUNT(*) FROM risks").fetchone()[0]
            high = conn.execute("SELECT COUNT(*) FROM risks WHERE severity = 'HIGH'").fetchone()[0]
            medium = conn.execute("SELECT COUNT(*) FROM risks WHERE severity = 'MEDIUM'").fetchone()[0]
            low = conn.execute("SELECT COUNT(*) FROM risks WHERE severity = 'LOW'").fetchone()[0]

            cursor = conn.execute(
                "SELECT risk_type, COUNT(*) AS count FROM risks GROUP BY risk_type"
            )
            type_distribution = {row["risk_type"]: row["count"] for row in cursor.fetchall()}

            return {
                "total_documents": total_docs,
                "total_risks": total_risks,
                "high_risks": high,
                "medium_risks": medium,
                "low_risks": low,
                "type_distribution": type_distribution,
            }
