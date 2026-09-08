from fastapi import APIRouter, HTTPException

from AICommunityObserver.metrics import (MetricContext, registered_metrics, get_enabled_metrics, 
                                         set_enabled_metrics, set_id_gen, get_id_gen, set_log_file, 
                                         set_metric_schema, get_metric_schema)

customization_router = APIRouter()

# ============================ Customization SET Endpoints ============================
@customization_router.post('/metrics/enabled', tags=["Customization"])
def set_enabled_metrics_endpoint(data=None):
    """
    Set the enabled metrics by name.
    """
    requested = set(data.get("enabled_metrics", []))

    available = {
        getattr(m, "metric_name", m.__name__) for m in registered_metrics
    }
    invalid = requested - available

    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metric names: {invalid}. Available metrics: {available}"
        )

    set_enabled_metrics(requested)

    return {
        "enabled_metrics": list(requested)
    }


@customization_router.post('/metrics/schema', tags=["Customization"])
def set_metrics_schema_endpoint(data: dict):
    """
    Set the current schema for metrics recording and storage.

    The supplied schema replaces the current METRIC_SCHEMA.
    """
    schema = data.get("fields")

    if not isinstance(schema, dict):
        raise HTTPException(
            status_code=400,
            detail="'schema' must be a dictionary."
        )

    try:
        python_schema = schema_types_to_python(schema)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    set_metric_schema(python_schema)

    return {
        "schema": schema_types_to_json(schema)
    }


@customization_router.post('/log/file', tags=["Customization"])
def set_log_file_endpoint(data: dict):
    """
    Set the log file path where metrics will be saved.

    The path must have a .jsonl extension.
    """
    path = data.get("path")

    if not isinstance(path, str) or not path:
        raise HTTPException(
            status_code=400,
            detail="'path' must be a non-empty string."
        )

    if not path.lower().endswith(".jsonl"):
        raise HTTPException(
            status_code=400,
            detail="Log file path must have a .jsonl extension."
        )

    LOG_FILE = set_log_file(path)

    return {
        "log_file": str(LOG_FILE)
    }


@customization_router.post('/id', tags=["Customization"])
def set_id_generator_endpoint(data: dict):
    """
    Set the ID generation function.

    Since Python callables cannot be supplied directly through JSON,
    the endpoint accepts the name of a supported ID generator.

    NOTE: Placeholder
    """
    id_gen_name = data.get("id_gen")

    if id_gen_name == "uuid4":
        return { "id_gen": id_gen_name }
    else:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid id_gen '{id_gen_name}'. "
                "Available ID generators: ['uuid4']"
            )
        )

    return {
        "id_gen": id_gen_name
    }

# ============================ Customization GET Endpoints ============================
@customization_router.get('/id', tags=["Customization"])
def get_id_gen_endpoint():
    return {"id_gen": get_id_gen().__name__}

@customization_router.get('/metrics/enabled', tags=["Customization"])
def get_enabled_metrics_endpoint():
    return {"enabled_metrics": list(get_enabled_metrics())}

@customization_router.get('/metrics/schema', tags=["Customization"])
def get_metrics_schema_endpoint():
    """
    Get the current schema for metrics recording and storage. 
    By default, this is also the schema for MetricsContext in context.py
    ---
    tags:
      - Customization
    responses:
      200:
        description: Schema
        schema:
          type: dict
        examples:
          application/json: {"fields": { 
              "prompt": "string",
              "response": "string",
              "model": "string",
              "metrics": {
                  "latency": "float"
              },
              "metadata": "object"
          }}
    """
    schema = get_metric_schema()
    return {
        "fields": schema_types_to_json(schema)
    }

@customization_router.get('/metrics/available', tags=["Customization"])
def get_metrics_available_endpoint():
    """
    Get all registered metric names. Use to avoid namespacing conflicts when setting.
    ---
    tags:
      - Customization
    responses:
      200:
        description: Namespace
        schema:
          type: dict
        examples:
          application/json: {"available_metrics": ["relevance", "coherence", "toxicity"]}
    """
    metric_names = [
        getattr(m, "metric_name", m.__name__) for m in registered_metrics
    ]
    return {
        "available_metrics": metric_names
    }

@customization_router.get('/metrics/plugins', tags=["Customization"])
def get_metrics_plugins_endpoint():
    """
    Get all registered metric plugin functions.
    ---
    tags:
      - Customization
    responses:
      200:
        description: Plugins
        schema:
          type: dict
        examples:
          application/json: {
            "plugins": [
              {
                "name": "latency.value",
                "function": "latency_metric",
                "module": "metrics.plugins.latency_metric"
              }
            ]
          }
    """
    plugins = []
    for m in registered_metrics:
        plugins.append({
            "name": getattr(m, "metric_name", m.__name__),
            "function": m.__name__,
            "module": m.__module__
        })
    return {"plugins": plugins}

# ========================================================= Helpers =========================================================

TYPE_MAP = {
    "string": str,
    "str": str,
    "float": float,
    "integer": int,
    "int": int,
    "boolean": bool,
    "bool": bool,
    "object": object,
    "dict": dict,
    "list": list,
}

def schema_types_to_python(schema: dict) -> dict:
    """
    Convert JSON-friendly type names into Python types.

    Example:
        {"prompt": "string", "metrics": "object"}

    becomes:
        {"prompt": str, "metrics": object}
    """
    converted = {}

    for key, value in schema.items():
        if isinstance(value, dict):
            converted[key] = schema_types_to_python(value)

        elif isinstance(value, str):
            try:
                converted[key] = TYPE_MAP[value.lower()]
            except KeyError:
                raise ValueError(
                    f"Unknown schema type '{value}' for field '{key}'. "
                    f"Supported types: {list(TYPE_MAP)}"
                )

        else:
            raise ValueError(
                f"Invalid schema type for '{key}': {value!r}"
            )

    return converted


def schema_types_to_json(schema: dict) -> dict:
    """
    Convert Python types into JSON-friendly type names.

    Example:
        {"prompt": str, "metrics": object}

    becomes:
        {"prompt": "string", "metrics": "object"}
    """
    reverse_type_map = {
        str: "string",
        float: "float",
        int: "integer",
        bool: "boolean",
        dict: "object",
        object: "object",
        list: "list",
    }

    converted = {}

    for key, value in schema.items():
        if isinstance(value, dict):
            converted[key] = schema_types_to_json(value)

        elif isinstance(value, type):
            if value not in reverse_type_map:
                raise ValueError(
                    f"Unsupported Python type '{value.__name__}' "
                    f"for schema field '{key}'."
                )

            converted[key] = reverse_type_map[value]

        else:
            raise ValueError(
                f"Invalid schema value for '{key}': {value!r}"
            )

    return converted
