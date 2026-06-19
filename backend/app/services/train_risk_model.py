"""
Risk Classifier Training Script

Trains a TF-IDF + Logistic Regression pipeline on a synthetic dataset
of contract clauses labeled as HIGH, MEDIUM, or LOW risk.

Run directly:
    python -m app.services.train_risk_model
"""

import os
import pickle
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "risk_classifier.pkl")


def get_training_data():
    """Generate high-quality synthetic training clauses and labels."""
    data = [
        # ── HIGH RISK ──────────────────────────────────────────────────
        ("The Supplier's total liability under this Agreement shall be completely unlimited under any circumstances.", "HIGH"),
        ("Neither party limits its liability for any damages or breaches.", "HIGH"),
        ("The vendor will be liable for all direct and indirect damages without limitation.", "HIGH"),
        ("Liability is not capped or limited under any circumstances.", "HIGH"),
        ("The client waives all rights of indemnity and recovery against the service provider.", "HIGH"),
        ("Under no circumstances shall the vendor be required to submit to audits or reviews.", "HIGH"),
        ("The customer shall have no right to audit the books or security of the vendor.", "HIGH"),
        ("Auditing of the system, data, or financial records by the client is strictly prohibited.", "HIGH"),
        ("The supplier excludes all rights of audit or inspections by the customer.", "HIGH"),
        ("No audit rights are granted to the customer under this agreement.", "HIGH"),
        ("The vendor is not subject to audit or inspection of any kind.", "HIGH"),
        ("In no event shall the supplier's liability be limited to the fees paid.", "HIGH"),
        ("The provider shall be liable for any third-party claims without limit.", "HIGH"),
        ("Company agrees to indemnify vendor against all claims, including those due to vendor negligence.", "HIGH"),
        ("Audit of vendor facilities, servers, or records is completely prohibited.", "HIGH"),
        ("All data generated during the engagement becomes the property of the vendor.", "HIGH"),
        ("The vendor retains all intellectual property rights over data processed under this contract.", "HIGH"),
        ("The client shall have no claim to any data or output produced during the services.", "HIGH"),

        # ── MEDIUM RISK ───────────────────────────────────────────────
        ("This contract shall automatically renew for successive one-year terms unless cancelled.", "MEDIUM"),
        ("At the end of the initial term, the agreement will auto-renew.", "MEDIUM"),
        ("The service agreement extends automatically unless written notice is given 30 days prior.", "MEDIUM"),
        ("The term of this agreement shall be automatically extended for subsequent periods.", "MEDIUM"),
        ("Either party may terminate this agreement immediately and without notice upon any breach.", "MEDIUM"),
        ("This agreement may be terminated by the vendor immediately without prior written notice.", "MEDIUM"),
        ("We reserve the right to terminate the services immediately and without notice.", "MEDIUM"),
        ("At the end of the term, the subscription will auto-renew on a month-to-month basis.", "MEDIUM"),
        ("This agreement can be terminated immediately without cause by the provider.", "MEDIUM"),
        ("Services may be suspended immediately without liability to the service provider.", "MEDIUM"),
        ("Contract automatically renews for successive 12-month periods.", "MEDIUM"),
        ("Immediate termination of service if payment is delayed by more than 5 days.", "MEDIUM"),
        ("Either party can cancel, but auto-renewal applies if not cancelled 90 days before expiration.", "MEDIUM"),
        ("The agreement shall auto-renew at the current standard list price.", "MEDIUM"),
        ("We may modify terms at any time and continued use auto-renews the subscription.", "MEDIUM"),
        ("The SLA guarantees only 95% uptime which is below industry standard.", "MEDIUM"),
        ("Penalties for service level breaches are capped at 5% of monthly fees.", "MEDIUM"),

        # ── LOW RISK ──────────────────────────────────────────────────
        ("This agreement is governed by the laws of the State of Delaware.", "LOW"),
        ("Each party shall keep all confidential information strictly secret and confidential.", "LOW"),
        ("The parties agree to resolve any disputes through binding arbitration.", "LOW"),
        ("This document represents the entire agreement between the parties.", "LOW"),
        ("Any amendments to this contract must be made in writing and signed by both parties.", "LOW"),
        ("The customer shall pay all invoices within thirty (30) days of receipt.", "LOW"),
        ("All notices under this agreement shall be sent via certified mail.", "LOW"),
        ("The service provider will perform the services with reasonable care and skill.", "LOW"),
        ("Neither party may assign this agreement without the prior written consent of the other.", "LOW"),
        ("If any provision of this agreement is found invalid, the remaining terms remain in effect.", "LOW"),
        ("No waiver of any breach shall constitute a waiver of any subsequent breach.", "LOW"),
        ("The relationship of the parties is that of independent contractors.", "LOW"),
        ("This agreement may be executed in counterparts, each of which is an original.", "LOW"),
        ("We will use commercially reasonable efforts to make the services available 24/7.", "LOW"),
        ("This agreement does not create any joint venture or partnership.", "LOW"),
        ("Standard billing terms apply as detailed in Exhibit A.", "LOW"),
        ("The terms of this contract shall remain confidential.", "LOW"),
        ("Both parties agree to a mutual non-disclosure obligation for the duration of this agreement.", "LOW"),
        ("The warranty period for delivered services is ninety (90) calendar days from acceptance.", "LOW"),
    ]
    texts, labels = zip(*data)
    return list(texts), list(labels)


def train_and_save_model() -> str:
    """Train the classifier and serialize to disk."""
    os.makedirs(MODEL_DIR, exist_ok=True)

    texts, labels = get_training_data()

    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            min_df=1,
            sublinear_tf=True,
        )),
        ("clf", LogisticRegression(
            C=1.0,
            class_weight="balanced",
            random_state=42,
            max_iter=1000,
        )),
    ])

    logger.info(f"Training Logistic Regression classifier on {len(texts)} samples...")
    pipe.fit(texts, labels)

    train_acc = pipe.score(texts, labels)
    logger.info(f"Training accuracy: {train_acc:.2%}")

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(pipe, f)

    logger.info(f"Model saved to {MODEL_PATH}")
    return MODEL_PATH


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_and_save_model()
