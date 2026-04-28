"""
metric_analysis.py

Experimental utilities for using LLMs to interpret metric data.
This module is intentionally separated from core metrics so that
LLM-based evaluation can be iterated on independently.

NOTE:
This module is not currently part of the core metrics pipeline.
Future versions of evaluate_metrics may import these utilities.
"""

import os
from typing import List, Dict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate

from sentence_transformers import SentenceTransformer

# -----------------------------
# LLM Initialization Utilities
# -----------------------------

def initialize_llm(model: str) -> ChatGoogleGenerativeAI:
    """
    Initialize a Gemini LLM instance.

    Args:
        model (str): Model name (e.g., gemini-2.0-flash)

    Returns:
        ChatGoogleGenerativeAI
    """
    return ChatGoogleGenerativeAI(model=model)


def initialize_embeddings():
    """
    Initialize the embedding model used for drift detection.

    Returns:
        GoogleGenerativeAIEmbeddings
    """
    return SentenceTransformer("google/embeddinggemma-300m")


# -----------------------------
# Prompt Templates
# -----------------------------

metric_template = """
    You are a specialist in tracking and evaluation the performance of results from prompts

    You will be given variables such as latency, given in seconds (s). Using this information, you must return whether there is an anomaly or not.

    You will also be given a history for previous latencuies. This will be used as your reference and comparison point.

    Additionally, you should use your own common knowledge to determine an answer and validate the response to not include any unnecessary information. This is important as there will be times where there is very little information gain from the latency history.

    Give the response as either "Normal" or "Anomaly" and provide reasoning behind the decision and how to improve summarized in 5 bullet points.

    latency: {latency}

    log_history: {log_history}
    """


def build_latency_prompt():
    """
    Create the latency evaluation prompt template.
    """
    return ChatPromptTemplate.from_template(metric_template)


# -----------------------------
# LLM Metric Analysis
# -----------------------------

def analyze_latency_with_llm(latency: float, log_history: List[float], model: str = "gemini-2.0-flash"):
    """
    Uses an LLM to analyze latency behavior and determine
    whether the measurement appears anomalous.

    Args:
        latency: Current latency value
        log_history: Previous latency measurements
        model: Gemini model name

    Returns:
        LLM response string
    """

    llm = initialize_llm(model)
    prompt = build_latency_prompt()

    chain = prompt | llm

    response = chain.invoke({
        "latency": latency,
        "log_history": log_history
    })

    return response.content


# -----------------------------
# Prompt Response Generation
# -----------------------------

def generate_prompt_responses(prompt: str, model: str) -> Dict:
    """
    Generates responses for a prompt using two
    LLM instances. Intended for drift testing.

    Args:
        prompt: Input prompt
        model: Model name

    Returns:
        dict containing both responses
    """

    llm_base = initialize_llm(model)
    llm_v2 = initialize_llm(model)

    result_base = llm_base.invoke(prompt).content
    result_v2 = llm_v2.invoke(prompt).content

    return {
        "baseline": result_base,
        "variant": result_v2
    }
