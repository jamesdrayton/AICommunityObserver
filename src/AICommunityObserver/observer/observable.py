
import json
import time
import uuid
import httpx
import random
import logging

from collections.abc import Callable

from google import genai
from google.genai import types

from openai import OpenAI

from huggingface_hub import login, InferenceClient
# from unsloth import FastLanguageModel

from ..metrics import evaluate_metrics, MetricContext, is_evaluation_active

# Configure logging
# TODO: Create a threshold of changes for relevance before adding to log to prevent file bloat.
# Currently logs even when insignificant changes are happening (1 change detected per second)
# logging.basicConfig(
#     filename="gemini_calls.log",
#     level=logging.INFO,
#     format="%(asctime)s | %(levelname)s | %(message)s",
# )

class Observable:
    """
    Class Observable can be instanced in a module where it is imported such that:
        - The type of model access can be specified for that instance (default API key) if given a key or access token. Options:
            - "api_key" which requires
                - api_key: str
                - Supports: Gemini, OpenAI, HuggingFace models
            - "api_token" which requires
                - token_url: str
                - client_id: str
                - client_secret: str
                - For: Custom API endpoints
        - "model_type" The type of model a.k.a. the provider
        - "model_name" The name of the model (default gemini-3.5-flash). Current options: Gemini, OpenAI, HuggingFace.
        - "testing_freq" A float representing the percentage of calls using this object which will have run tests. Default: 0.1 a.k.a 10%
        - "id_gen" A Callable (function) responsible for id handling. Default: uuid4
        - "provider_options" A dict representing the fine-tuning kwargs passed to provider. E.g.
           provider_options_example={
               "client": {
                   "enterprise": True,
                   "project": "...",
                   "location": "...",
               },
               "generate": {
                   "temperature": 0.8,
                   "top_p": 0.95,
               }
           }

    and the generate function can be called on that instance such that it will prompt the defined model in that instance with a given str.
    """
    
    # Helper function to detect the available hardware (GPU and vRAM) for init
    def _detect_hardware(self):
        # TODO: Either automate or move to user config.
        return
    
    # Init will instantiate the instance as usual, and check if all of the necessary parameters are present for the stated access type
    def __init__(self, model_type: str = "gemini", model_name: str = "gemini-3.5-flash",                            # Basic essential parameters
                 api_key: str | None = None, access_type: str = "api_key",                                          # API key access parameters
                 token_url: str | None = None, client_id: str | None = None, client_secret: str | None = None,      # API token access parameters
                 testing_freq: float = 0.1, provider_options: dict = {},                                            # User customization options
                 id_gen: Callable[[], object] = uuid.uuid4
                 ):
        # Immediately checks for errors in given params, continues if all is well.
        if access_type == "api_key" and api_key is None:
            raise ValueError("Cannot use api_key access without an API key. This Observable instance will not function.")
        elif access_type == "api_token" and (token_url is None or client_id is None or client_secret is None):
            raise ValueError("Cannot use api_token access without all parameters. This Observable instance will not function.")
        
        # Define wrapper access constants
        self.access_type = access_type.lower()
        self.model_type = model_type.lower()
        self.model_name = model_name.lower()
        self.embedding_model = "gemini-embedding-001" # TODO: Choose embedding model with a function
        self.api_key = api_key
        self.SCOPE = "api"
        self.token_cache = {"access_token": None, "expires_at": 0}

        # Define wrapper configuration constants
        self.testing_freq = testing_freq
        self.id_gen = id_gen

        if not isinstance(provider_options, dict):
            raise TypeError("provider_options must be a dictionary if provided.")
        self.provider_options = provider_options or {"client": {}, "generate": {}}
        
        if access_type == "api_key":
            # Detect model type and initialize accordingly
            client_kwargs = self.provider_options.get("client", {})
            if self.model_type == "gemini":
                try:
                    # Google Gemini
                    self.model = genai.Client(
                        api_key=api_key,
                        **client_kwargs
                        )
                except Exception as e:
                    print(f"Couldn't instantiate chosen model type: {self.model_type}. Exception returned: {e}")
            elif self.model_type == "openai":
                try:
                    # OpenAI
                    self.model = OpenAI(api_key=api_key)
                except Exception as e:
                    print(f"Couldn't instantiate chosen model type: {self.model_type}. Exception returned: {e}")
            elif self.model_type == "huggingface":
                try:
                    # HuggingFace Inference API
                    # TODO: Alternate between InferenceClient and Unsloth FastLanguageModel based on _detect_hardware()
                    self.model = InferenceClient(model=model_name, token=api_key)
                except Exception as e:
                    print(f"Couldn't instantiate chosen model type: {self.model_type}. Exception returned: {e}")
            else:
                raise ValueError(f"Unknown model type for {model_name}. Supported types: gemini, openai, huggingface")
                
        elif access_type == "api_token":
            self.TOKEN_URL = token_url
            self.CLIENT_ID = client_id
            self.CLIENT_SECRET = client_secret

    # =================================================================== General api_token access ==============================================================================

    # Purpose: call to get an access token from the API
    async def get_access_token(self):
        token_cache = self.token_cache
        # reuse if not expired
        if token_cache["access_token"] and token_cache["expires_at"] > time.time():
            return token_cache["access_token"]

        async with httpx.AsyncClient() as client:
            data = {
                "grant_type": "client_credentials",
                "client_id": self.CLIENT_ID,
                "client_secret": self.CLIENT_SECRET,
                "scope": self.SCOPE
            }
            resp = await client.post(self.TOKEN_URL, data=data)
            resp.raise_for_status()
            token_data = resp.json()
            token_cache["access_token"] = token_data["access_token"]
            token_cache["expires_at"] = time.time() + token_data.get("expires_in", 3600) - 10
            return token_cache["access_token"]
        
    # TODO: Make work with access_type: api_token as well as access_type: api_key
    # TODO: Configure for batch generation
    # generate is the main point of access for instances of this class
    # generate must take a prompt, and it passes the prompt to the instance's chosen model
    def generate(self, prompt: str | list, max_tokens: int = 256, temperature: float = 1.0, 
                       testing_freq: float | int | None = None, do_tests: bool | None = None,
                       metadata: dict | None = None, provider_options: dict | None = None, 
                       url: str = "", headers = None, body = None,                                        # Leftover from api_token options
                       return_context: bool = False, id: int | str | Callable[[], object] | None = None):

        # Set default dict if metadata is None and appends default if it is not
        if metadata is None:
            metadata = {"maintain_privacy" : True}
        elif metadata.get("maintain_privacy") == None:
            metadata["maintain_privacy"] = True

        if not isinstance(provider_options, dict):
            raise TypeError("provider_options must be a dictionary if provided.")
        provider_options = provider_options or self.provider_options

        # Generate a unique id using the given function if it is a function
        if id is None:
            id = self.id_gen
        if callable(id):
            id = id()

        # Override default testing_freq for this generate call if provided as a parameter
        if testing_freq is None:
            testing_freq = self.testing_freq
        testing_freq = float(testing_freq)            

        # Generate unique log ID based on start time
        start_time = time.time()

        # ========== Try making the call to the respective model with the given prompt ==========
        try:
            # Point of difference for api_key vs api_token access type
            if self.access_type == "api_key":
                generate_kwargs = provider_options.get("generate", {})
                # Handle different model types
                if self.model_type == "gemini":
                    response = self.model.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            **generate_kwargs,
                            temperature=temperature,
                            max_output_tokens=max_tokens,
                        )
                    )
                    response_text = response.text.strip()

                elif self.model_type == "openai":
                    response = self.model.chat.completions.create( #type: ignore
                        model=self.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        **generate_kwargs,
                        temperature=temperature,
                        max_completion_tokens=max_tokens,
                    )
                    response_text = response.choices[0].message.content.strip()

                elif self.model_type == "huggingface":
                    response = self.model.text_generation(
                        prompt,
                        **generate_kwargs
                    )
                    response_text = response.strip()

                else:
                    raise ValueError(f"Unsupported model type: {self.model_type}")
            else:
                raise ValueError("Cannot access the API without url, headers, and body")

            duration = time.time() - start_time

            metadata["latency"] = duration
            metadata["tokens_used"] = response.usage_metadata.total_token_count if hasattr(response, "usage_metadata") else 999999 # Flag for missing token usage data
            # TODO: Log or raise an error if tokens_used exceeds max_tokens
            metadata["embedding_model"] = self.embedding_model
            metadata["maintain_privacy"] = metadata.get("maintain_privacy", True)

            # ========== Call evaluate_metrics to implement the observability aspect ==========

            # do_tests bool overrides other params
            if do_tests:
                metadata["do_tests"] = True
            else:
                # Only evaluate some percentage of the time with self.testing_freq
                random.seed(1443)
                metadata["do_tests"] = (random.random() < testing_freq)

            context = MetricContext(
                prompt=prompt,
                response=response_text,
                latency=duration,
                tokens_used=metadata["tokens_used"],
                model=self.model_name,
                embed_function=self.embed
            )
            evaluate_metrics(id=id, context=context, metadata=metadata) if not is_evaluation_active() else None
            if return_context:
                return response_text, context
            return response_text

        except Exception as e:
            duration = time.time() - start_time
            metadata["do_tests"] = False
            metadata["tokens_used"] = 0
            context = MetricContext(
                prompt=prompt,
                response=f"Failure to reach model within Community Observer. Exception: {e}",
                latency=duration,
                tokens_used=0,
                model=self.model_name,
                embed_function=self.embed
            )
            evaluate_metrics(id=id, context=context, metadata=metadata) if not is_evaluation_active() else None
            raise Exception(f"Failure to reach model within Community Observer. Exception: {e}")
    
    # TODO: Configure for batch embedding
    # embed is a general purpose embedding function which will adjust to chosen embedding models according to the defined observable model
    # embed must take text (to perform the embedding on) and returns a vector
    def embed(self, text: str | list, task_type: str = "SEMANTIC_SIMILARITY", embedding_model: str = "gemini-embedding-001"):
        # TODO: Configure for different model types (currently all gemini free)
        try:
            if self.model is None:
                self.model = genai.Client()
            result = self.model.models.embed_content(
                model=embedding_model,
                contents=text,
                config=types.EmbedContentConfig(task_type=task_type)
            )
            return result.embeddings[0].values
        except Exception as e:
            raise Exception(f"Failure to embed: {e}")
        
    # Helper functions to get prompt and response embeddings either through caching or generating a new embedding
    def _get_prompt_embedding(self, context: MetricContext, task_type: str = "SEMANTIC_SIMILARITY", embedding_model: str = "gemini-embedding-001"):
        key = (embedding_model, task_type)
        if key not in context.prompt_embeddings and context.prompt:
            context.prompt_embeddings[key] = self.embed(text=context.prompt, task_type=task_type, embedding_model=embedding_model)
            return context.prompt_embeddings[key]
        return None
    
    def _get_response_embedding(self, context: MetricContext, task_type: str = "SEMANTIC_SIMILARITY", embedding_model: str = "gemini-embedding-001"):
        key = (embedding_model, task_type)
        if key not in context.response_embeddings and context.response:
            context.response_embeddings[key] = self.embed(text=context.response, task_type=task_type, embedding_model=embedding_model)
            return context.response_embeddings[key]
        return None