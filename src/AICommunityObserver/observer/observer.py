import time
import uuid
import random

from collections.abc import Callable
from typing import Any, Dict, Optional

from ..metrics import evaluate_metrics, MetricContext, is_evaluation_active, get_id_gen

class Observer:
    """
    Class Observer can be instanced in a module where it is imported such that:
        - The type of model in use can be specified with:
            - "provider" The type of model a.k.a. the provider
            - "model_name" The name of the model (default gemini-3.5-flash). Current options: Gemini, OpenAI, HuggingFace.
        - "testing_freq" A float representing the percentage of calls using this object which will have run tests. Default: 0.1 a.k.a 10%
        - "id_gen" A Callable (function) responsible for id handling. Default: uuid4
    """
    def __init__(self, provider: str = "google", model_name: str = "gemini-3.5-flash",  # Basic essential parameters
                 embed_function: Optional[Callable[..., Any]] = None,
                 testing_freq: float = 0.1, id_gen: Callable[[], object] | None = None  # User customization options
                ):
        self.provider = provider.lower()
        self.model_name = model_name.lower()
        self.testing_freq = testing_freq
        self.id_gen = id_gen or get_id_gen()

        self.embed_function = embed_function

    # Default entrypoint for observer. Always runs evaluate_metrics on prompt-response
    def observe(
        self,
        prompt: str,
        response: str,
        latency: float,
        tokens_used: int,
        model: str = self.model_name,
        id: int | str | str | Callable[[], object] | None = None,
        metadata: dict | None = None,
    ):

        if metadata is None:
            metadata = {"maintain_privacy": True}
        elif metadata.get("maintain_privacy") == None:
            metadata["maintain_privacy"] = True

        if id is None:
            id = self.id_gen
        if callable(id):
            id = id()

        context = MetricContext(
            prompt=prompt,
            response=response,
            latency=latency,
            tokens_used=tokens_used,
            model=model,
            embed_function=self.embed_function,
        )

        evaluate_metrics(
            context=context,
            id=id,
            metadata=metadata,
        )

        return context