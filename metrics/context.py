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
        latency: float = 999.999,
        model: str = "",
        metadata: Dict[str, Any] = {"Empty": None}
    ):
        self.prompt = prompt
        self.response = response
        self.latency = latency
        self.model = model

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