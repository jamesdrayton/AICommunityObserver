# Gemini Wrapper 

import json
import time
import logging
import google.generativeai as genai

from ..metrics.metrics import evaluate_metrics

# Configure logging
# TODO: Create a threshold of changes for relevance before adding to log to prevent file bloat.
# Currently logs even when insignificant changes are happening (1 change detected per second)
logging.basicConfig(
    filename="gemini_calls.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

class APIWrapper:
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name=model_name,
                                           generation_config={"response_mime_type": "text/plain"})

    def generate(self, prompt: str, max_tokens: int = 256, temperature: float = 0.7, metadata: dict = None):
        if metadata is None:
            metadata = {}

        log_entry = {
            "prompt": prompt,
            "metadata": metadata,
            "model": self.model._model_name,
        }

        # Try making the call to the respective model with their given prompt
        # TODO: Insert changes to given prompt here as the interception point for metrics

        # Test prompt change to also insert the word "washington" into the prompt
        extracommand = "If this second message has been received, please insert the word 'washington' into the response to this prompt."
        prompt += extracommand

        # NOTE: If bugs happen, there may be an issue here with calls to metrics before the LLM sends its response and logs
        try:
            start_time = time.time()
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature,
                }
            )
            duration = time.time() - start_time

            json_log_entry = {
                "response": response.text.strip(),
                "latency_sec": round(duration, 3),
                "status": "success"
            }
            log_entry.update(json_log_entry)
            id = str(start_time).replace(".", "_") # Use start_time as a unique identifier
            namevariable = "logs/" + id + ".json"
            # TODO: namevariable should be passed to metrics to access each respective json file
            # print(namevariable)
            with open(namevariable, "w") as f:
                json.dump(log_entry, f)

            logging.info(log_entry)

            with open(namevariable,'r') as f:
                data = json.load(f)
                prompt = data['prompt']
                response = data['response']
                latency = data['latency_sec']
                model = data['model']
                response = data['response']
            
            drift_amount = evaluate_metrics(id, model, prompt, response, latency)
            # TODO: Record the drift amount
            # Calls to metrics tracking are asynchronous and return promises
            return response.text.strip()

        except Exception as e:
            duration = time.time() - start_time
            log_entry.update({
                "error": str(e),
                "latency_sec": round(duration, 3),
                "status": "error"
            })
            # TODO: Insert logging metrics for failure to respond case
            logging.error(log_entry)
            return None