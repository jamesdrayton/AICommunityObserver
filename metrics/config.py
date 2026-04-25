
ENABLED_METRICS = set()  # Set of metric names that are enabled for recording and storage. By default, all registered metrics are enabled.

def set_enabled_metrics(metric_names):
    """
    Set the list of enabled metrics for recording and storage. This allows users to filter which metrics they want to keep track of, without needing to change their metric plugin code.

    Example:
        set_enabled_metrics(["relevance", "toxicity"])
    """
    global ENABLED_METRICS
    ENABLED_METRICS = set(metric_names)

def get_enabled_metrics():
    """
    Get the current set of enabled metrics for recording and storage.
    """
    return ENABLED_METRICS

def is_metric_enabled(metric_name):
    """
    Check if a given metric name is currently enabled for recording and storage.
    """
    if not ENABLED_METRICS:
        return True
    return metric_name in ENABLED_METRICS