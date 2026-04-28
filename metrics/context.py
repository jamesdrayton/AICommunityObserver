"""
context.py

Defines the MetricContext object used to pass structured data
into metric plugins.

This acts as the canonical schema for all metric inputs.
"""

from typing import Any, Dict


class MetricContext:
    """
    Container for all inputs to metric evaluation.

    This object is passed to all registered metric plugins.
    """

    def __init__(
        self,
        prompt: str = "",
        response: str = "",
        prompt_embedding: list = [],
        response_embedding: list = [], # TODO: Decide if we want to pass this from init or do it in the background
        latency: float = 999.999,
        model: str = "",
        metadata: Dict[str, Any] = {"Empty": None}
    ):
        self.prompt = prompt
        self.response = response
        self.latency = latency
        self.model = model

        self._embedding_model = None
        self.prompt_embedding = prompt_embedding or []
        self.response_embedding = response_embedding or []

        # Flexible extension point
        self.metadata = metadata or {}

    @classmethod
    def schema(cls):
        return { 
            "prompt": "string",
            "response": "string",
            "model": "string",
            "metrics": {
                "latency": "float"
            },
            "metadata": "object"
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert context to dictionary (useful for logging or API responses).
        """
        return {
            "prompt": self.prompt,
            "response": self.response,
            "model": self.model,
            "metrics": {
                "latency": self.latency
            },
            "metadata": self.metadata
        }
    
    # =============================================== Embedding Model Helpers ===============================================

    def _get_embedding_model(self):
        if self._embedding_model is None:
            from metrics.embedding import get_embedding_model
            self._embedding_model = get_embedding_model()
        return self._embedding_model
    
    def get_prompt_embedding(self):
        if not self.prompt_embedding and self.prompt:
            model = self._get_embedding_model()
            self.prompt_embedding = model.encode_query(self.prompt)
        return self.prompt_embedding
    
    def get_response_embedding(self):
        if not self.response_embedding and self.response:
            model = self._get_embedding_model()
            self.response_embedding = model.encode_query(self.response)
        return self.response_embedding