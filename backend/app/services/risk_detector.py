"""
Risk Detector Service

Hybrid compliance risk detection combining:
  1. Rule-based regex matching from risk_rules.yaml
  2. ML classification via TF-IDF + Logistic Regression model

Rule-based matches take precedence; ML classification only runs
on sentences that don't match any rule.
"""

import os
import re
import yaml
import pickle
import logging
from typing import List, Dict, Any
import uuid

logger = logging.getLogger(__name__)

RULES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "risk_rules.yaml",
)
MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "models",
    "risk_classifier.pkl",
)


class RiskDetector:
    """Hybrid rule + ML risk classification engine."""

    def __init__(
        self,
        rules_path: str = RULES_PATH,
        model_path: str = MODEL_PATH,
    ):
        self.rules_path = rules_path
        self.model_path = model_path
        self.rules: list = []
        self.model = None

        self._load_rules()
        self._load_model()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------
    def _load_rules(self):
        if not os.path.exists(self.rules_path):
            logger.warning(f"Risk rules file not found at {self.rules_path}")
            return
        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self.rules = data.get("rules", [])
                logger.info(f"Loaded {len(self.rules)} risk rules from {self.rules_path}")
        except Exception as e:
            logger.error(f"Error loading risk rules: {e}")

    def _load_model(self):
        if not os.path.exists(self.model_path):
            logger.warning(f"ML model not found at {self.model_path}. ML classification disabled.")
            return
        try:
            with open(self.model_path, "rb") as f:
                self.model = pickle.load(f)
                logger.info("Loaded ML risk classifier successfully.")
        except Exception as e:
            logger.error(f"Error loading ML classifier: {e}")

    # ------------------------------------------------------------------
    # Detection Pipeline
    # ------------------------------------------------------------------
    def detect_risks_in_document(
        self,
        doc_id: str,
        sentences: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Scan a list of sentences for compliance risks.

        Args:
            doc_id:    Document identifier.
            sentences: List of dicts: [{"text": "...", "page_num": 1}]

        Returns:
            List of detected risk dicts ready for database insertion.
        """
        detected: List[Dict[str, Any]] = []

        for sent in sentences:
            text = sent["text"]
            page_num = sent["page_num"]

            # 1. Rule-based detection (takes precedence)
            rule_matched = False
            for rule in self.rules:
                rule_id = rule["id"]
                severity = rule["severity"]
                patterns = rule.get("regex_patterns", [])

                for pattern in patterns:
                    try:
                        if re.search(pattern, text):
                            detected.append({
                                "id": str(uuid.uuid4()),
                                "doc_id": doc_id,
                                "risk_type": rule_id,
                                "severity": severity.upper(),
                                "page_num": page_num,
                                "text": text,
                                "confidence": 1.0,
                                "classification_method": "rule",
                            })
                            rule_matched = True
                            break  # one match per rule is sufficient
                    except Exception as e:
                        logger.error(f"Regex error on pattern '{pattern}': {e}")

            # 2. ML classification (only if no rule matched and model loaded)
            if not rule_matched and self.model is not None:
                try:
                    pred = self.model.predict([text])[0]
                    if pred in ("HIGH", "MEDIUM"):
                        probs = self.model.predict_proba([text])[0]
                        class_probs = dict(zip(self.model.classes_, probs))
                        confidence = float(class_probs.get(pred, 0.0))

                        if confidence > 0.45:
                            risk_type = (
                                "ml_high_risk" if pred == "HIGH" else "ml_medium_risk"
                            )
                            detected.append({
                                "id": str(uuid.uuid4()),
                                "doc_id": doc_id,
                                "risk_type": risk_type,
                                "severity": pred,
                                "page_num": page_num,
                                "text": text,
                                "confidence": round(confidence, 4),
                                "classification_method": "ml",
                            })
                except Exception as e:
                    logger.error(f"ML classification error: {e}")

        return detected
