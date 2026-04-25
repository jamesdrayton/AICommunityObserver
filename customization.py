from flask import Blueprint, request, jsonify

from metrics.context import MetricContext
from metrics.metrics import registered_metrics
from metrics.config import get_enabled_metrics, set_enabled_metrics

customization_bp = Blueprint('customization', __name__)

# ============================ Customization SET Endpoints ============================
@customization_bp.route('/metrics/enabled', methods=['POST'])
def set_enabled_metrics_endpoint(data=None):
    """
    Set the enabled metrics by name.
    ---
    tags:
      - Customization
    parameters:
      - name: body
        in: body
        required: true
        description: The metric fields being specified
        schema:
          type: object
          properties:
            enabled_metrics:
              type: array
              items:
                type: string
              examples: ["relevance.cosine_similarity", "toxicity"]
    responses:
      200:
        description: Set the enabled metrics
        schema:
          type: object
        examples:
          application/json: {"enabled_metrics": ["relevance", "toxicity"]}
    """
    data = request.get_json()
    requested = set(data.get("enabled_metrics", []))

    available = {
        getattr(m, "metric_name", m.__name__) for m in registered_metrics
    }
    invalid = requested - available

    if invalid:
        return jsonify({
            "error": f"Invalid metric names: {invalid}",
            "available_metrics": list(available)
        }), 400
    
    set_enabled_metrics(requested)

    return {"enabled_metrics": list(requested)}

# ============================ Customization GET Endpoints ============================
@customization_bp.route('/metrics/enabled', methods=['GET'])
def get_enabled_metrics_endpoint():
    return {"enabled_metrics": list(get_enabled_metrics())}

@customization_bp.route('/metrics/schema', methods=['GET'])
def get_metrics_schema():
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
    return {
        "fields": MetricContext.schema()
    }

@customization_bp.route('/metrics/available', methods=['GET'])
def get_metrics_available():
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

@customization_bp.route('/metrics/plugins', methods=['GET'])
def get_metrics_plugins():
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