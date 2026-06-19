"""
CLI wrapper: Train and save the risk classification model.

Usage:
    python -m app.services.save_model
"""

import sys
import logging

try:
    from app.services.train_risk_model import train_and_save_model
except ImportError:
    from train_risk_model import train_and_save_model

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    try:
        model_path = train_and_save_model()
        print(f"Success: Model trained and saved to {model_path}")
        sys.exit(0)
    except Exception as e:
        print(f"Error training model: {e}", file=sys.stderr)
        sys.exit(1)
