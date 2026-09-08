
from collections.abc import Iterable, Callable
from pathlib import Path
import uuid

LOG_FILE = Path("metrics_log.jsonl") # Default file path
ID_GEN = uuid.uuid4                  # Default callable
METRIC_SCHEMA = {                    # Default schema
            "id": str,
            "prompt": str,
            "response": str,
            "model": str,
            "metrics": dict,
            "metadata": dict,
        }

ENABLED_METRICS = None               # Set of metric names that are enabled for recording and storage. By default, all registered metrics are enabled.
METRIC_ORDER = None

def _default_metric_order(metrics):
    """Return metrics sorted alphabetically by their configured metric names."""
    return sorted(metrics, key=lambda metric: getattr(metric, "metric_name", metric.__name__).lower())


# ========================================================= LOG CONFIG =========================================================
def set_log_file(path: str = "metrics_log.jsonl") -> None:
    """Set the log file path where metrics will be saved. Default is the same directory as config.py. Path must be a .jsonl file to avoid overwriting."""
    global LOG_FILE
    LOG_FILE = Path(path)
    return None

def get_log_file() -> Path:
    return LOG_FILE

# ========================================================= ID CONFIG ==============================================================

def set_id_gen(id_gen: Callable) -> None:
    """Set the id generation function. Default is uuid.uuid4. This setting in config will still be overwritten if values are set in Observable/Observer init."""
    global ID_GEN
    ID_GEN = id_gen
    return None

def get_id_gen() -> Callable:
    return ID_GEN

# ========================================================= METRIC SCHEMA CONFIG ===================================================

def get_metric_schema() -> dict:
    return METRIC_SCHEMA

def set_metric_schema(schema: dict) -> None:
    """
    Set the schema for outputting metrics on Observable/Observer calls.
    Beware changing this, as the schema can be quite fiddly without the required keys.
    """
    global METRIC_SCHEMA
    METRIC_SCHEMA = schema
    return None

# ========================================================= METRICS CONFIG =========================================================
def set_enabled_metrics(metric_names: Iterable | None = None) -> None:
    """
    Set the list of enabled metrics for recording and storage. This allows users to filter which metrics they want to keep track of, without needing to change their metric plugin code.

    Example:
        set_enabled_metrics(["relevance", "toxicity"])
    """
    global ENABLED_METRICS

    if metric_names is None:
        ENABLED_METRICS = None
        return

    normalized = set()
    for metric_name in metric_names:
        if hasattr(metric_name, "metric_name"):
            normalized.add(getattr(metric_name, "metric_name"))
        elif hasattr(metric_name, "__name__"):
            normalized.add(metric_name.__name__)
        else:
            normalized.add(str(metric_name))

    ENABLED_METRICS = normalized
    return None

def get_enabled_metrics() -> set | None:
    """
    Get the current set of enabled metrics for recording and storage.
    """
    return ENABLED_METRICS

def is_metric_enabled(metric_name: str) -> bool:
    """
    Check if a given metric name is currently enabled for recording and storage.
    """
    return (ENABLED_METRICS is None) or metric_name in ENABLED_METRICS


def set_metric_order(order_fn: Callable = None) -> None:
    """Set the function used to determine the order metrics will be evaluated in. Alphabetical by default."""
    global METRIC_ORDER
    if order_fn is None:
        METRIC_ORDER = _default_metric_order
    else:
        METRIC_ORDER = order_fn
    return None


def get_metric_order() -> Callable:
    """Get the current function used to determine the order metrics will be evaluated in."""
    if METRIC_ORDER is None:
        return _default_metric_order
    return METRIC_ORDER