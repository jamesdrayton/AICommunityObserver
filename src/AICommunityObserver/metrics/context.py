"""
context.py

Defines the MetricContext object used to pass structured data
into metric plugins.

This acts as the canonical schema for all metric inputs.
"""

from collections.abc import Callable
from .config import get_metric_schema

from typing import Any, Dict, Optional

class MetricContext:
    """
    Container for all inputs to metric evaluation.

    This object is passed to all registered metric plugins.

    It is also optionally accessible to the user.
    """

    def __init__(
        self,
        prompt: str = "",
        response: str = "",
        prompt_embeddings: dict | None = None,
        response_embeddings: dict | None = None,
        latency: float = 999.999,
        tokens_used: int = 999999,
        model: str = "",
        metadata: Dict[str, Any] | None = None
    ):
        # Essential low-level fields
        self.prompt = prompt
        self.response = response
        self.latency = latency
        self.tokens_used = tokens_used
        self.model = model

        if metadata is None:
            metadata = {}

        # TODO: Join with namespacing for accessibility
        # Non-essential low-level fields (Optionally present in metadata dict)
        self.language = metadata.get("language", None) # Implemented for multilingual GenAI applications that may run in 2 or more languages
        self.domain = metadata.get("domain", None)     # Should be a Str if passed
        self.has_rag = metadata.get("has_rag", None)   # Should be a bool if passed

        # Higher level fields for embedding-based metrics
        self.client = None
        self.prompt_embeddings = prompt_embeddings or {}
        self.response_embeddings = response_embeddings or {}        

        # Flexible extension point
        self.metadata = metadata or {}
    
    @classmethod
    def schema(cls, data=None):
        schema = get_metric_schema()

        if data is None:
            return schema

        return cls._fit(data, schema)

    @classmethod
    def _fit(cls, data, schema):
        result = {}

        for key, expected_type in schema.items():
            if key not in data:
                continue

            value = data[key]

            if isinstance(expected_type, dict):
                if isinstance(value, dict):
                    result[key] = cls._fit(value, expected_type)
            else:
                result[key] = value

        return result

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert context to dictionary (useful for logging or API responses).
        """
        return {
            "prompt": self.prompt,
            "response": self.response,
            "model": self.model,
            "metrics": {
                "latency": self.latency,
                "tokens_used": self.tokens_used
            },
            "metadata": self.metadata
        }