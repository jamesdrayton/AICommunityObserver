from fastapi import APIRouter

from ..observer import Observable
from ..env import get_env_variable

import asyncio
import time
import random
import pandas as pd

router = APIRouter()

# ======================================================================= API and Constant Definitions =======================================================================

GEMINI_API_KEY = get_env_variable("GEMINI_API_KEY")
OPENAI_API_KEY = get_env_variable("OPENAI_API_KEY")

# Define constants to be used in the middleware wrappers (optional)
TESTING_FREQ = 1 # set so 100 percent of all api calls will be tested in depth (optional, 0.1 is the default)

# Define all models to be used in this example project using the Observable class

gemini_middleware = Observable(api_key=GEMINI_API_KEY, model_name='gemini-3.5-flash', testing_freq=TESTING_FREQ) if GEMINI_API_KEY else None 
openai_middleware = Observable(api_key=OPENAI_API_KEY, model_name="gpt-5.4-nano", testing_freq=TESTING_FREQ) if OPENAI_API_KEY else None

# Models dict is composed of each model name as its keys and a list of the model api key/id in position 0 and the wrapper object in position 1
models_dict = {
    "gemini-3.5-flash": gemini_middleware if GEMINI_API_KEY else None, 
    "gpt-5-nano": openai_middleware if OPENAI_API_KEY else None, 
}

default_model = "gemini-3.5-flash"

metadata = {"important_topics": [
    "Write a topic which you want the bot to tell users about",
    "Write an important alert which it's important to include in a bot response",
    "Write something else"
], 
"user_location": "",
"location_weather": ""}

# Generic system prompt for reasoning chatbot
# Optional: Insert metadata fields into the system prompt
systemprompt = """ 
A conversation between User and Assistant. The user asks a question, and the assistant solves it.
The assistant first thinks about the reasoning process in the mind and then provides the user
with the answer. The reasoning process and answer are enclosed within <think></think> and <answer></answer> tags
respectively, i.e., <think> reasoning process here </think> and <answer> answer here </answer>.

Do not generate new code. Do not write python code.

You may also be given examples by the user telling you the expected response format.
Follow the format of the examples, but solve the specific problem asked by the user, not the examples.

Very important - Remember again, your output format should be:
<think> reasoning process here </think>
<answer> answer here </answer>

Your response will be scored by extracting the substring between the <answer>...</answer> tags.
It is critical to follow the above format."""

# Helper function to monitor and check on calls to models for when the call fails or otherwise
def call_with_retries(api_func, *args, retries=3, backoff=2, jitter=0.2, **kwargs):
    """
    Wrapper for robust API calls with retries and exponential backoff.
    api_func: function to call (e.g., model inference function)
    *args/**kwargs: passed to api_func
    """
    for attempt in range(retries):
        try:
            return api_func(*args, **kwargs)
        except Exception as e:
            if attempt == retries - 1:
                raise
            sleep_time = (backoff ** attempt) + random.uniform(0, jitter)
            print(f"API call failed ({e}), retrying in {sleep_time:.2f}s...")
            time.sleep(sleep_time)

# ======================================================================= API endpoints =======================================================================

# ======================================================================= Primary endpoints (Model Calls)  =======================================================================

@router.get("/create_gemini_message", tags=["Model Calls"])
def create_gemini_message(prompt=None):
    """
    Create a new external message calling a Google genai model.
    Default preparation is using one pre-established wrapper defined at the top of testing.py
    ---
    tags:
      - Model Calls
    parameters:
      - name: prompt
        in: query
        type: string
        required: true
        description: "The message being sent"
    responses:
      200:
        description: The model's inference response
        schema:
          type: json
    """
    
    try:
        # Generate response using the Observable
        response = gemini_middleware.generate(prompt=prompt, max_tokens=2560, metadata={"maintain_privacy": False})
                
        return ({
            "prompt": prompt,
            "response": response
        })
    except Exception as e:
        print("Error generating Gemini response:", e)
        return ({"error": str(e)}), 500
    
@router.get("/create_openai_message", tags=["Model Calls"])
def create_openai_message(prompt=None, temperature=1.0, threadId=123, modelName="gpt-5-nano"):
    """
    Create a new external message calling the OpenAI API.
    ---
    tags:
      - Model Calls
    parameters:
      - name: prompt
        in: query
        type: string
        required: true
        description: "The message being sent"
      - name: temperature
        in: query
        type: number
        required: false
        description: "The temperature to use for the response"
      - name: threadId
        in: query
        type: string
        required: false
        description: "The Id of the thread you are creating a message in (if not starting a new one)"
      - name: modelName
        in: query
        type: string
        required: false
        description: "The OpenAI model to use for this message"
    responses:
      200:
        description: The model's inference response
        schema:
          type: json
    """
    
    try:
        # Try to get model from models_dict, or catch KeyError
        # if modelName in models_dict and models_dict[modelName] is not None:
        #     openai_wrapper = models_dict[modelName]
        # else:
        #     # Create a new wrapper instance if not in dict
        #     openai_wrapper = Observable(api_key=OPENAI_API_KEY, model_name=modelName)
        openai_wrapper = models_dict[modelName]
        
        # Generate response using the Observable
        response = openai_wrapper.generate(prompt=prompt, testing_freq = 1.0)
        
        return ({
            "threadId": threadId,
            "model": modelName,
            "prompt": prompt,
            "response": response
        })
    except KeyError as e:
        print("Model not found in models_dict")
        return ({"error": str(e)}), 500
    except Exception as e:
        print("Error generating OpenAI response:", e)
        return ({"error": str(e)}), 500

