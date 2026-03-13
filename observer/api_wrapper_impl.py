
import os
import json
import time
import httpx
import logging
import google.generativeai as genai

from openai import OpenAI

from huggingface_hub import login, InferenceClient
# from unsloth import FastLanguageModel

# TODO 4: Debug metrics
#from ..metrics.metrics import evaluate_metrics

# Import performance logger for metrics
from metrics.performance_logger import get_performance_logger

# Configure logging
# TODO: Create a threshold of changes for relevance before adding to log to prevent file bloat.
# Currently logs even when insignificant changes are happening (1 change detected per second)
logging.basicConfig(
    filename="gemini_calls.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# TODO: Assess if it's possible to generate the models list when detecting the model type on class instantiation
openai_models = ['gpt-4-0613', 'gpt-4', 'gpt-3.5-turbo', 'gpt-5.1-codex-mini', 'gpt-5.1-chat-latest', 'gpt-5.1-2025-11-13', 'gpt-5.1', 'gpt-5.1-codex', 'davinci-002', 'babbage-002', 
          'gpt-3.5-turbo-instruct', 'gpt-3.5-turbo-instruct-0914', 'dall-e-3', 'dall-e-2', 'gpt-4-1106-preview', 'gpt-3.5-turbo-1106', 'tts-1-hd', 'tts-1-1106', 'tts-1-hd-1106', 
          'text-embedding-3-small', 'text-embedding-3-large', 'gpt-4-0125-preview', 'gpt-4-turbo-preview', 'gpt-3.5-turbo-0125', 'gpt-4-turbo', 'gpt-4-turbo-2024-04-09', 'gpt-4o', 
          'gpt-4o-2024-05-13', 'gpt-4o-mini-2024-07-18', 'gpt-4o-mini', 'gpt-4o-2024-08-06', 'chatgpt-4o-latest', 'gpt-4o-audio-preview', 'gpt-4o-realtime-preview', 
          'omni-moderation-latest', 'omni-moderation-2024-09-26', 'gpt-4o-realtime-preview-2024-12-17', 'gpt-4o-audio-preview-2024-12-17', 'gpt-4o-mini-realtime-preview-2024-12-17', 
          'gpt-4o-mini-audio-preview-2024-12-17', 'o1-2024-12-17', 'o1', 'gpt-4o-mini-realtime-preview', 'gpt-4o-mini-audio-preview', 'o3-mini', 'o3-mini-2025-01-31', 
          'gpt-4o-2024-11-20', 'gpt-4o-search-preview-2025-03-11', 'gpt-4o-search-preview', 'gpt-4o-mini-search-preview-2025-03-11', 'gpt-4o-mini-search-preview', 
          'gpt-4o-transcribe', 'gpt-4o-mini-transcribe', 'o1-pro-2025-03-19', 'o1-pro', 'gpt-4o-mini-tts', 'o3-2025-04-16', 'o4-mini-2025-04-16', 'o3', 'o4-mini', 
          'gpt-4.1-2025-04-14', 'gpt-4.1', 'gpt-4.1-mini-2025-04-14', 'gpt-4.1-mini', 'gpt-4.1-nano-2025-04-14', 'gpt-4.1-nano', 'gpt-image-1', 'gpt-4o-realtime-preview-2025-06-03', 
          'gpt-4o-audio-preview-2025-06-03', 'gpt-4o-transcribe-diarize', 'gpt-5-chat-latest', 'gpt-5-2025-08-07', 'gpt-5', 'gpt-5-mini-2025-08-07', 'gpt-5-mini', 
          'gpt-5-nano-2025-08-07', 'gpt-5-nano', 'gpt-audio-2025-08-28', 'gpt-realtime', 'gpt-realtime-2025-08-28', 'gpt-audio', 'gpt-5-codex', 'gpt-image-1-mini', 
          'gpt-5-pro-2025-10-06', 'gpt-5-pro', 'gpt-audio-mini', 'gpt-audio-mini-2025-10-06', 'gpt-5-search-api', 'gpt-realtime-mini', 'gpt-realtime-mini-2025-10-06', 
          'sora-2', 'sora-2-pro', 'gpt-5-search-api-2025-10-14', 'gpt-3.5-turbo-16k', 'tts-1', 'whisper-1', 'text-embedding-ada-002']

# TODO: Reconfigure to work in the api wrapper class instead
# Helper class to track the token usage for each model
class UsageTracker:
    def __init__(self):
        self.usage = {}

    def update(self, model_id, prompt_tokens, completion_tokens):
        """Update token usage stats for a model."""
        if model_id not in self.usage:
            self.usage[model_id] = {"prompt": 0, "completion": 0}
        self.usage[model_id]["prompt"] += prompt_tokens
        self.usage[model_id]["completion"] += completion_tokens

    def report(self):
        """Return current usage stats."""
        return self.usage

class APIWrapper:
    """
    Class APIWrapper can be instanced in a module where it is imported such that:
        - The type of model access can be specified for that instance (default API key) if given a key or access token. Options:
            - "api_key" which requires
                - api_key: str
                - Supports: Gemini, OpenAI, HuggingFace models
            - "api_token" which requires
                - token_url: str
                - client_id: str
                - client_secret: str
                - For: Custom API endpoints
        - The name of the model (default gemini-2.0-flash). Current options: Google Gemini, OpenAI, HuggingFace model IDs.

    and the generate function can be called on that instance such that it will prompt the defined model in that instance with a given str
    """
    
    # Helper function to detect the available hardware (GPU and vRAM) for init
    def _detect_hardware():
        # TODO: Either automate or move to user config.
        return

    # Helper function to detect model type. Consider deleting and moving to user config.
    def _detect_model_type(self, model_name: str, api_key: str) -> str:
        """
        Detect the model type based on model name and API key.
        Returns: 'gemini', 'openai', or 'huggingface'
        """
        model_lower = model_name.lower()
        
        # Check for Gemini models
        if "gemini" in model_lower:
            return "gemini"
        
        # Check for OpenAI models
        if any(openai_model in model_name for openai_model in openai_models):
            return "openai"
        
        # Check for HuggingFace models (format: username/model-name or just model-name)
        if "/" in model_name or model_name in ["gpt2", "distilbert-base-uncased"]:
            return "huggingface"
        
        # Default to HuggingFace if not recognized (assume it's a HF model ID)
        return "huggingface"
    
    # Init will instantiate the instance as usual, and check if all of the necessary parameters are present for the stated access type
    def __init__(self, 
                 api_key: str = None, token_url: str = None, client_id: str = None, client_secret: str = None, 
                 model_name = "gemini-2.0-flash", access_type: str = "api_key", testing_freq: float = 0.1):
        # Immediately checks for errors in given params, continues if all is well.
        if access_type == "api_key" and api_key is None:
            raise ValueError("Cannot use api_key access without an API key. This APIWrapper instance will not function.")
        elif access_type == "api_token" and (token_url is None or client_id is None or client_secret is None):
            raise ValueError("Cannot use api_token access without all parameters. This APIWrapper instance will not function.")
        
        # Define wrapper access constants
        self.access_type = access_type
        self.model_name = model_name
        self.api_key = api_key
        self.SCOPE = "api"
        self.token_cache = {"access_token": None, "expires_at": 0}

        # Define wrapper configuration constants
        self.testing_freq = testing_freq # TODO: Implement testing frequency
        
        if access_type == "api_key":
            # Detect model type and initialize accordingly
            self.model_type = self._detect_model_type(model_name, api_key)
            
            if self.model_type == "gemini":
                # Google Gemini
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel(model_name=model_name,
                                                generation_config={"response_mime_type": "text/plain"}
                                                )
            elif self.model_type == "openai":
                # OpenAI
                self.model = OpenAI(api_key=api_key)
            elif self.model_type == "huggingface":
                # HuggingFace Inference API
                # TODO: Alternate between InferenceClient and Unsloth FastLanguageModel based on _detect_hardware()
                self.model = InferenceClient(model=model_name, token=api_key)
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
    # generate is the main point of access for instances of this class
    # generate must take a prompt, and it passes the prompt to the instance's chosen model
    async def generate(self, prompt: str, max_tokens: int = 256, temperature: float = 0.7,
                       metadata: dict = None, url: str = None, headers=None, body=None):
        # Initialize performance logger
        perf_logger = get_performance_logger()

        # Use empty dict if metadata is None (safer than default mutable argument)
        if metadata is None:
            metadata = {}

        # Create base log entry
        log_entry = perf_logger.create_base_entry(
            prompt=prompt,
            model=self.model_name,
            metadata=metadata
        )

        # Generate unique log ID based on start time
        start_time = time.time()
        log_id = perf_logger.generate_log_id(start_time)

        # Try making the call to the respective model with their given prompt
        # TODO: Insert changes to given prompt here as the interception point for metrics, username, region, etc.
        # TODO: Insert code to log to the database for training data which can be fed back into retraining

        try:
            # Point of difference for api_key vs api_token access type
            if self.access_type == "api_key":
                # Handle different model types
                if self.model_type == "gemini":
                    response = self.model.generate_content(
                        prompt,
                        generation_config={
                            "max_output_tokens": max_tokens,
                            "temperature": temperature,
                        }
                    )
                    response_text = response.text.strip()

                elif self.model_type == "openai":
                    response = self.model.chat.completions.create(
                        model=self.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                    response_text = response.choices[0].message.content.strip()

                elif self.model_type == "huggingface":
                    response = self.model.text_generation(
                        prompt,
                        max_new_tokens=max_tokens,
                        temperature=temperature,
                    )
                    response_text = response.strip()

                else:
                    raise ValueError(f"Unsupported model type: {self.model_type}")

            elif self.access_type == "api_token" and (url is not None and headers is not None and body is not None):
                # TODO: Troubleshoot this elif, currently it's just there in case someone calls generate() on the wrong instance instead of using the helpers
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, headers=headers, json=body)
                    response.raise_for_status()
                    return response.json()
            else:
                raise ValueError("Cannot access the API without url, headers, and body")

            duration = time.time() - start_time

            # Log successful call
            perf_logger.log_success(
                log_entry=log_entry,
                response=response_text,
                latency_sec=duration,
                log_id=log_id
            )

            # TODO: Code to call metrics evaluation with the log_id
            # drift_amount = evaluate_metrics(log_id, self.model_name, prompt, response_text, duration)
            # TODO: Record the drift amount

            return response_text

        except Exception as e:
            duration = time.time() - start_time

            # Log error call
            perf_logger.log_error(
                log_entry=log_entry,
                error=e,
                latency_sec=duration,
                log_id=log_id
            )

            return None