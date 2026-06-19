"""
CLI Risk Prediction Script

Usage:
    python -m app.services.predict_risk "The vendor's liability shall be unlimited."
"""

import os
import sys
import argparse
import pickle

try:
    from app.services.train_risk_model import MODEL_PATH, train_and_save_model
except ImportError:
    from train_risk_model import MODEL_PATH, train_and_save_model


def get_classifier():
    """Load the trained classifier, auto-training if the model file is missing."""
    if not os.path.exists(MODEL_PATH):
        print("Model file not found. Training now...")
        train_and_save_model()

    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


def predict(text: str) -> dict:
    """Predict risk label and confidence for a given clause."""
    clf = get_classifier()
    prediction = clf.predict([text])[0]
    probs = clf.predict_proba([text])[0]
    class_probs = dict(zip(clf.classes_, probs))

    return {
        "text": text,
        "risk_level": prediction,
        "confidence": float(class_probs.get(prediction, 0.0)),
        "probabilities": {k: float(v) for k, v in class_probs.items()},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Predict compliance risk category of a contract clause."
    )
    parser.add_argument(
        "text",
        type=str,
        nargs="?",
        help="The contract clause or sentence to analyze.",
    )
    args = parser.parse_args()

    if not args.text:
        print('Usage: python predict_risk.py "clause text here"')
        sys.exit(1)

    res = predict(args.text)
    print(f'\nClause: "{res["text"]}"')
    print(f'Risk Level: {res["risk_level"]}')
    print(f'Confidence: {res["confidence"]:.2%}')
    print("Probabilities:")
    for lvl, prob in res["probabilities"].items():
        print(f"  - {lvl}: {prob:.2%}")
