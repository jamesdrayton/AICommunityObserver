
import os
import json
import time
import httpx
import logging
import google.generativeai as genai

from openai import OpenAI

from huggingface_hub import login, InferenceClient
# from unsloth import FastLanguageModel

from metrics.metrics import evaluate_metrics

# Configure logging
# TODO: Create a threshold of changes for relevance before adding to log to prevent file bloat.
# Currently logs even when insignificant changes are happening (1 change detected per second)
logging.basicConfig(
    filename="gemini_calls.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# TODO: Assess if it's possible to generate the models list when detecting the model type on class instantiation

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
        - The name of the model (default gemini-2.0-flash). Current options: Google Gemini, OpenAI, HuggingFace model IDs.

    and the generate function can be called on that instance such that it will prompt the defined model in that instance with a given str
    """
    
    # Helper function to detect the available hardware (GPU and vRAM) for init
    def _detect_hardware(self):
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
        if "gpt" in model_lower:
            return "openai"
        
        # Check for HuggingFace models (format: username/model-name or just model-name)
        if "/" in model_name or model_name in ["gpt2", "distilbert-base-uncased"]:
            return "huggingface"
        
        # Default to HuggingFace if not recognized (assume it's a HF model ID)
        return "huggingface"
    
    # Init will instantiate the instance as usual, and check if all of the necessary parameters are present for the stated access type
    def __init__(self, 
                 api_key: str = "", token_url: str = "", client_id: str = "", client_secret: str = "", 
                 model_name = "gemini-2.0-flash", access_type: str = "api_key", testing_freq: float = 0.1):
        # Immediately checks for errors in given params, continues if all is well.
        if access_type == "api_key" and api_key is None:
            raise ValueError("Cannot use api_key access without an API key. This Observable instance will not function.")
        elif access_type == "api_token" and (token_url is None or client_id is None or client_secret is None):
            raise ValueError("Cannot use api_token access without all parameters. This Observable instance will not function.")
        
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
    def generate(self, prompt: str, max_tokens: int = 256, temperature: float = 1.0,
                       metadata: dict = {}, url: str = "", headers=None, body=None):

        # Use empty dict if metadata is None (safer than default mutable argument)
        if metadata is None:
            metadata = {}

        # Generate unique log ID based on start time
        start_time = time.time()

        # ========== Try making the call to the respective model with the given prompt ==========
        # TODO: Consider abstracting to a helper function for the model call

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
                    response = self.model.chat.completions.create( #type: ignore
                        model=self.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        max_completion_tokens=max_tokens,
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
            else:
                raise ValueError("Cannot access the API without url, headers, and body")

            duration = time.time() - start_time

            # ========== Call evaluate_metrics to implement the observability aspect ==========
            # TODO: Configure to:
            # - Use one single schema for ids
            # - Only evaluate some percentage of the time with self.testing_freq
            evaluate_metrics(id=123, model=self.model_name, 
                             given_prompt=prompt, given_response=response_text, 
                             latency=duration)
            
            return response_text

        except Exception as e:
            duration = time.time() - start_time

            evaluate_metrics(id=123, model=self.model_name,
                             given_prompt=prompt, given_response=f"Failure to reach model within Community Observer. Exception: {e}",
                             latency=duration)
            raise Exception(f"Failure to reach model within Community Observer. Exception: {e}")

            return None