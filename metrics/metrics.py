
import numpy as np
import importlib
import logging
import time
import json
import csv
import os

from .config import is_metric_enabled
from .metric_analysis import (
    initialize_embeddings,
    analyze_latency_with_llm,
    generate_prompt_responses
)

from .context import MetricContext

try:
    from env import get_env_variable
except ImportError:
    import os
    get_env_variable = os.getenv

logger = logging.getLogger(__name__)

# Initialize embedding model
# PROMPT/RESPONSE SIZES SHOULD ALSO BE MEASURED AND PASSED TO METRICS. THIS ALLOWS RELATIVE EFFICACY MEASUREMENTS
# TODO: Make log file and path customizable
DEFAULT_LOG_FILE = "metrics_log.jsonl"
log_history = [] # TODO: Evaluate the purpose of log_history if we save to persistence layer every time
token_usage_history = [] # e.g. 500, 750, 600, 1200

# -----------------------------
# Metric Plugin Registry
# -----------------------------

registered_metrics = set({})

def register_metric(name=None):
    """
    Decorator used to register a metric function.

    Metric functions must accept at minimum:
        (given_prompt, given_response)
        within a MetricContext object

    and return a dictionary of results.

    Example:
        @register_metric(name="example_metric_name")
        def example_metric(MetricContext context):
            return {"example_metric": 0.91}
    """
    def decorator(func):
        registered_metrics.add(func)
        func.metric_name = name or func.__name__
        registered_metrics.add(func)
        return func
    return decorator

# Primary entry for developers using the Observer or Observable middleware.
# Takes in the prompt, response, latency, and other relevant info and evaluates all registered metrics. Adds to log_history and returns results.
def evaluate_metrics(id, model, given_prompt, given_response, latency):

    info = {
        "id": id,
        "model": model,
        "prompt": given_prompt,
        "response": given_response,
        "latency": latency,
        "metrics": {}
    }
    context = MetricContext(
        prompt=given_prompt,
        response=given_response,
        latency=latency,
        model=model
    )

    # Iterate over metrics in alphabetical order
    # TODO: Allow order customization
    for metric_func in registered_metrics:

        metric_name = getattr(metric_func, "metric_name", metric_func.__name__)

        if not is_metric_enabled(metric_name):
            continue

        try:
            result = metric_func(
                context
            )

            if result is not None:
                info["metrics"][metric_func.metric_name] = result

        except Exception as e:
            print(f"Metric plugin failed: {metric_func.__name__} -> {e}")

    # Remove prompt and response from info before saving as metrics. Important for data privacy and storage.
    info.pop("prompt", None)
    info.pop("response", None)

    log_history.append(info)

    save_metrics(info) # save the info dict to a persistent database

    return info

# Configurable fn for the dumping the log_history to a database for storage/reading/display to dashboard
def save_metrics(data, file_path=DEFAULT_LOG_FILE):
    """Appends log_history to a JSONL file. Each line is a separate JSON object."""
    try:
        record = {"timestamp": time.time(),
                  "data": data}
        
        with open(file_path, "a") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        raise Exception(f"Persistence error: {e}")

    return

# TODO: Change to scan subdirectory when tests have been registered.
# Helper to load ALL files containing measurable tests in this directory.
def load_metric_plugins():
    plugins_dir = os.path.dirname(__file__) + "/plugins"
    # Iterates over and imports all decorated metrics files so they're loaded
    try:
        for file in os.listdir(plugins_dir):
            if file.endswith(".py") and file not in ("metrics.py", "context.py"):
                module_name = file[:-3]
                importlib.import_module(f".plugins.{module_name}", package=__package__)
    except FileNotFoundError as e:
        raise Exception(f"Error loading metric plugins: {e} \n Consider checking directory pathing.")
    except Exception as e:
        raise Exception(f"Error loading metric plugins: {e}")

load_metric_plugins()