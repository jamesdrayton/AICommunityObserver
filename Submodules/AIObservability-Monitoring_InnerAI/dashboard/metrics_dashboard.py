from fastapi import APIRouter
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import os
import csv
from pathlib import Path

router = APIRouter()


<<<<<<< HEAD
# --- CSV Logging Setup ---
LOG_FILE = "metrics_log.csv"
CSV_HEADER = [
    "timestamp", "instance_id", "model_name", "latency", "drift",
    "relevancy", "entropy_scores", "entropy_mean", "prompt", "response"
]
=======
def processed_metrics(processed_json):
    print(processed_json)
    latency = processed_json.get("latency")
>>>>>>> 7a190fa1a8d5a9808d9d7a799e616ab71f80ffd0

# Create file and write headers if it doesn't exist
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(CSV_HEADER)

# Helper functin to append new info into the shared CSV
def append_to_csv(row: list):
    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(row)

# --- Metrics Definitions to display charts ---

# Histogram for latency tracking (seconds)
latency_histogram = Histogram(
    "llm_response_latency_seconds",
    "Latency of LLM responses in seconds",
    ["model_name"]
)

# Histogram for drift tracking (0-1)
drift_histogram = Histogram(
    "llm_drift_score",
    "Drift score of LLM responses (0 to 1)",
    ["model_name"]
)

# Gauge for relevancy score (0-1)
relevancy_score_gauge = Gauge(
    "llm_relevancy_score",
    "Relevancy score of LLM response (0 to 1)",
    ["model_name"]
)

# Entropy scores for hallucination events (0 to 1)
hallucination_histogram = Histogram(
    "llm_hallucination_score",
    "Average entropy score of LLM responses (0 to 1)",
    ["model_name"]
)

# Counter for total prompts received
# TODO: Add flag for prompts which never received a response (this can be done from the failure condition in the try catch from APIWrapper)
prompt_counter = Counter(
    "llm_total_prompts",
    "Total number of prompts received by the middleware",
    ["model_name"]
)

# --- Metric Recording Functions ---

# Takes the model name and records the drift score to a histogram and updates a file
def record_drift(model_name: str, drift_score: float):
    drift_histogram.labels(model_name=model_name).observe(drift_score)

# Takes the model name and records it to 
def record_latency(model_name: str, latency: float):
    latency_histogram.labels(model_name=model_name).observe(latency)

def record_relevancy(model_name: str, score: float):
    relevancy_score_gauge.labels(model_name=model_name).set(score)

def record_hallucination(model_name: str, entropy_scores: list):
    entropy_score = sum(entropy_scores) / len(entropy_scores) if entropy_scores else 0.0
    hallucination_histogram.labels(model_name=model_name, entropy_score=entropy_score).inc()
    return entropy_score

def record_prompt(instance_id: int, model_name: str, prompt: str, response: str):
    prompt_counter.labels(model_name=model_name).inc()


# --- Commands and helper function to add to metrics.py so that this module can receive the data ---
# from ..dashboard import metrics_dashboard as md
# md.processed_metrics(processed_json)

# TODO: make the default values available as variables so they can also be used as flags for missing data

def processed_metrics(processed_json):
    instance_id = processed_json.get("id", "0")
    model_name = processed_json.get("model", "unknown")
    latency = processed_json.get("latency", 0.0)
    drift = processed_json.get("drift", 0.0)
    relevancy = processed_json.get("relevancy", 0.0)
    entropy_scores = processed_json.get("entropy", [])
    prompt = processed_json.get("prompt", "Missing prompt")
    response = processed_json.get("response", "Missing response")

    record_prompt(model_name)
    record_latency(model_name, latency)
    record_drift(model_name, drift)
    record_relevancy(model_name, relevancy)
    entropy_mean = record_hallucination(model_name, entropy_scores)

    # Append to CSV
    csv_row = [
        instance_id, model_name,
        round(latency, 4), round(drift, 4),
        round(relevancy, 4), entropy_scores, round(entropy_mean, 4),
        prompt, response
    ]
    append_to_csv(csv_row)

# --- Prometheus Metrics Endpoint ---

@router.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
