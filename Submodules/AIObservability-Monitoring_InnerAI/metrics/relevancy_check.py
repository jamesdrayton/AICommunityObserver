#Relevency
# metrics/relevancy.py
"""
Utility for computing prompt–response relevancy with a cross-encoder.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Union

import torch
import torch.nn.functional as F
from sentence_transformers import CrossEncoder  # pip install sentence-transformers

# ────────────────────────────────
# Internal: singleton model loader
# ────────────────────────────────
_encoder: CrossEncoder | None = None


def _get_encoder(model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> CrossEncoder:
    """Load the cross-encoder once and cache it globally."""
    global _encoder
    if _encoder is None:
        _encoder = CrossEncoder(model_name)
    return _encoder


# ────────────────────────────────
# Public helpers
# ────────────────────────────────
def compute_relevancy(record: Dict[str, str], model_name: str | None = None) -> float:
    """
    Given a log *dict* with 'prompt' and 'response' keys,
    return a relevancy score in the range 0‒1.
    """
    prompt = record.get("prompt", "")
    response = record.get("response", "")
    if not prompt or not response:
        raise ValueError("Record must contain non-empty 'prompt' and 'response' fields.")

    encoder = _get_encoder(model_name or "cross-encoder/ms-marco-MiniLM-L-6-v2")
    raw_logit = encoder.predict([(prompt, response)])[0]          # scalar logit
    return float(F.sigmoid(torch.tensor(raw_logit)))              # map to 0-1


def compute_relevancy_from_file(path: Union[str, Path], model_name: str | None = None) -> float:
    """
    Convenience wrapper that loads the JSON log from *path*
    (e.g., Path('logs/2025-06-02-15-50-31.json')) and delegates
    to `compute_relevancy`.
    """
    path = Path(path)
    with path.open(encoding="utf-8") as f:
        record = json.load(f)
    return compute_relevancy(record, model_name)
