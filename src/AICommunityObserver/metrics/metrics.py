
from contextvars import ContextVar
from pathlib import Path
import importlib
import time
import json
import os

from .config import is_metric_enabled, set_enabled_metrics, get_enabled_metrics, get_log_file, get_metric_order

from .context import MetricContext

LOG_FILE = get_log_file()
log_history = [] # Cached version of metrics logs (same ones saved to persistence jsonl)
token_usage_history = [] # e.g. 500, 750, 600, 1200

_evaluation_active = ContextVar(
    "evaluation_active",
    default=False
)

# -----------------------------
# Metric Plugin Registry
# -----------------------------
# Metric plugin namespaces take the form of "category.requirements.name"
# So a plugin which measures prompt-response similarity and requires embeddings will have its name preceded by relevance.embedding
# TODO: Alter registry to govern namespaces (e.g. if a plugin accesses context embeddings, verify .embedding is requirements)

registered_metrics = set()

def register_metric(name: str=None, tags: list[str]=None):
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
    if tags is None:
        tags = []
    tags = [tag.strip() for tag in name.split(".")] if name else []
    def decorator(func):
        registered_metrics.add(func)
        func.metric_name = name or func.__name__
        func.tags = tags
        registered_metrics.add(func)
        return func
    return decorator

# Helper to check for the evaluation token without importing contextvars
def is_evaluation_active() -> bool:
    return _evaluation_active.get()

# Primary entry for developers using the Observer or Observable middleware.
# Takes in the prompt, response, latency, and other relevant info and evaluates all registered metrics. Adds to log_history and returns results.
# Should be called once per prompt-response pair, and each call should have exactly one distinct corresponding context object, which is paired with a unique id.
def evaluate_metrics(id: int | str, context: MetricContext, metadata: dict | None = None):

    if metadata is None:
        metadata = {"maintain_privacy" : True}
    elif metadata.get("maintain_privacy") == None:
        metadata["maintain_privacy"] = True

    info = {
        "id": str(id),
        "model": context.model,
        "prompt": context.prompt,
        "response": context.response,
        "metadata": metadata,
        "metrics": {}
    }

    # Check if the context has flagged to not run a test
    do_tests = metadata.get("do_tests", False)

    token = _evaluation_active.set(True)

    try:
        # Iterate over metrics in alphabetical order by default or use the configured order function.
        metric_order = get_metric_order()
        for metric_func in metric_order(registered_metrics):
            if not do_tests:
                break

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
    finally:
        _evaluation_active.reset(token)

    # Remove prompt and response from info before saving as metrics. Important for data privacy and storage.
    # Optionally disabled in metadata for storage together. Recommended to instead log prompt-response pairs separately from metrics.
    if info["metadata"].get("maintain_privacy", True):
        info.pop("prompt", None)
        info.pop("response", None)
    token_usage_history.append(info["metadata"].get("tokens_used", 999999))
    log_history.append(info)

    save_metrics(info) # save the info dict to a persistent database
    return info

# Configurable fn for the dumping the log_history to a database for storage/reading/display to dashboard
def save_metrics(data, file_path=None):
    """Appends log_history to a JSONL file. Each line is a separate JSON object."""
    if file_path is None:
        file_path = get_log_file()

    file_path = Path(file_path)

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True) # Ensure the directory exists
        
        record = {"timestamp": time.time(),
                  "data": data}

        with open(file_path, "a") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        raise Exception(f"Persistence error: {e}")

    return

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
set_enabled_metrics(registered_metrics)