"""
context.py

Defines the MetricContext object used to pass structured data
into metric plugins.

This acts as the canonical schema for all metric inputs.
"""

from collections.abc import Callable

from typing import Any, Dict, Optional
from google import genai
from google.genai import types

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
        embed_function: Optional[Callable[..., Any]] = None,
        metadata: Dict[str, Any] | None = None
    ):
        # Essential low-level fields
        self.prompt = prompt
        self.response = response
        self.latency = latency
        self.tokens_used = tokens_used
        self.model = model

        # Non-essential low-level fields
        self.language = None #TODO: Implement

        # Higher level fields for embedding-based metrics
        self.client = None
        self.embed_function = embed_function
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
                "latency": "float",
                "tokens_used": "int",
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
                "latency": self.latency,
                "tokens_used": self.tokens_used
            },
            "metadata": self.metadata
        }
    
    # =============================================== Embedding Model Helpers ===============================================
    
    # Note: These vary with content configs. Current embedding caching is within a dict referred to by (model, task_type)
    def get_prompt_embedding(self, task_type: str = "SEMANTIC_SIMILARITY", model: str = "gemini-embedding-001"):
        key = (model, task_type)
        if key not in self.prompt_embeddings and self.prompt:
            self.prompt_embeddings[key] = self.embed_function(
                self.prompt,
                task_type=task_type,
                model=model
            )
        return self.prompt_embeddings[key]
    
    def get_response_embedding(self, task_type: str = "SEMANTIC_SIMILARITY", model: str = "gemini-embedding-001"):
        key = (model, task_type)
        if key not in self.response_embeddings and self.response:
            self.response_embeddings[key] = self.embed_function(
                self.response,
                task_type=task_type,
                model=model
            )
        return self.response_embeddings[key]