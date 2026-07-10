"""
context.py

Defines the MetricContext object used to pass structured data
into metric plugins.

This acts as the canonical schema for all metric inputs.
"""

from typing import Any, Dict
from google import genai
from google.genai import types

class MetricContext:
    """
    Container for all inputs to metric evaluation.

    This object is passed to all registered metric plugins.
    """

    def __init__(
        self,
        prompt: str = "",
        response: str = "",
        prompt_embeddings: dict = {},
        response_embeddings: dict = {}, # TODO: Decide if we want to pass this from init or do it in the background
        latency: float = 999.999,
        model: str = "",
        metadata: Dict[str, Any] = {"Empty": None}
    ):
        self.prompt = prompt
        self.response = response
        self.latency = latency
        self.model = model

        self.client = None
        self.prompt_embeddings = prompt_embeddings or {}
        self.response_embeddings = response_embeddings or {}

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

    def _get_client(self):
        if self.client is None:
            self.client = genai.Client()
        return self.client
    
    # Note: These vary with content configs. Current embedding caching is within a dict referred to by (model, task_type)
    def get_prompt_embedding(self, task_type: str = "SEMANTIC_SIMILARITY", model: str = "gemini-embedding-001"):
        key = (model, task_type)
        if key not in self.prompt_embeddings and self.prompt:
            client = self._get_client()
            result = client.models.embed_content(
                model=model,
                contents=self.prompt,
                config=types.EmbedContentConfig(task_type=task_type)
            )
            self.prompt_embeddings[key] = result.embeddings[0].values
        return self.prompt_embeddings[key]
    
    def get_response_embedding(self, task_type: str = "SEMANTIC_SIMILARITY", model: str = "gemini-embedding-001"):
        key = (model, task_type)
        if key not in self.response_embeddings and self.response:
            client = self._get_client()
            result = client.models.embed_content(
                model=model,
                contents=self.response,
                config=types.EmbedContentConfig(task_type=task_type)
            )
            self.response_embeddings[key] = result.embeddings[0].values
        return self.response_embeddings[key]