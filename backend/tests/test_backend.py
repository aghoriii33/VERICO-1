"""
Backend Unit & Integration Tests

Tests cover:
  - Text cleanup and sentence splitting
  - PDF chunking
  - Rule-based risk detection (regex)
  - ML risk classifier inference
  - FastAPI endpoints (/health, /documents, /risks)
  - Upload pipeline integration
"""

import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.document_processor import (
    split_into_sentences,
    clean_text,
    DocumentProcessor,
)
from app.services.risk_detector import RiskDetector
from app.services.predict_risk import predict


# ---------------------------------------------------------------------------
# Unit Tests
# ---------------------------------------------------------------------------
class TestTextProcessing:
    def test_clean_text_normalizes_whitespace(self):
        raw = "Hello   world! \r\n This is a \n\n\n test."
        cleaned = clean_text(raw)
        assert "  " not in cleaned
        assert "\r" not in cleaned
        assert "\n\n\n" not in cleaned

    def test_split_into_sentences_handles_abbreviations(self):
        text = (
            "This is sentence one. "
            "This is sentence two, e.g. with abbreviations. "
            "Is this the third sentence?"
        )
        sents = split_into_sentences(text)
        assert len(sents) == 3
        assert sents[0] == "This is sentence one."
        assert "e.g." in sents[1]

    def test_chunking_produces_output(self):
        pages = [{"page_num": 1, "text": "First paragraph.\n\nSecond paragraph with more text."}]
        chunks = DocumentProcessor.create_chunks(pages, chunk_size=500, overlap=100)
        assert len(chunks) >= 1
        assert "metadata" in chunks[0]
        assert chunks[0]["metadata"]["page_num"] == 1


class TestRiskDetection:
    def test_rule_based_unlimited_liability(self):
        detector = RiskDetector()
        sentences = [
            {"text": "The vendor shall have unlimited liability under this contract.", "page_num": 1},
            {"text": "Standard governing law applies.", "page_num": 2},
        ]
        risks = detector.detect_risks_in_document("test_doc", sentences)
        liability = [r for r in risks if r["risk_type"] == "unlimited_liability"]
        assert len(liability) == 1
        assert liability[0]["severity"] == "HIGH"
        assert liability[0]["classification_method"] == "rule"

    def test_rule_based_auto_renewal(self):
        detector = RiskDetector()
        sentences = [
            {"text": "The contract will automatically renew every year.", "page_num": 3},
        ]
        risks = detector.detect_risks_in_document("test_doc", sentences)
        renewal = [r for r in risks if r["risk_type"] == "auto_renewal"]
        assert len(renewal) == 1
        assert renewal[0]["severity"] == "MEDIUM"

    def test_ml_classification_output_structure(self):
        clause = "We will be liable for all direct and indirect damages without limitation."
        res = predict(clause)
        assert "risk_level" in res
        assert "confidence" in res
        assert res["risk_level"] in ("HIGH", "MEDIUM", "LOW")
        assert 0.0 <= res["confidence"] <= 1.0


# ---------------------------------------------------------------------------
# Integration Tests (FastAPI endpoints)
# ---------------------------------------------------------------------------
class TestAPIEndpoints:
    def test_health_endpoint(self):
        with TestClient(app) as client:
            response = client.get("/api/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "database" in data
            assert "vector_store" in data
            assert "qa_service" in data

    def test_get_documents_returns_list(self):
        with TestClient(app) as client:
            response = client.get("/api/documents")
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    def test_get_risks_returns_list(self):
        with TestClient(app) as client:
            response = client.get("/api/risks")
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    def test_ask_empty_query_returns_400(self):
        with TestClient(app) as client:
            response = client.post(
                "/api/ask",
                json={"query": "   "},
            )
            assert response.status_code == 400

    def test_detect_risk_requires_input(self):
        with TestClient(app) as client:
            response = client.post(
                "/api/detect-risk",
                json={},
            )
            assert response.status_code == 400
