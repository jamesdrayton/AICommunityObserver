from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from sklearn.metrics.pairwise import cosine_similarity
from ..dashboard.metrics_dashboard import processed_metrics
import numpy as np
import json
import os

# Set your API key
os.environ["GOOGLE_API_KEY"] = "AIzaSyCxAjRIrQnhytFkO2y5YXskO6Ck4zcYU0U"

# Initialize Gemini model
llm_base = ChatGoogleGenerativeAI(model="gemini-2.0-flash-001")
llm_v2 = ChatGoogleGenerativeAI(model="gemini-2.0-flash-001")

embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

latency_history = []
token_usage_history = [500, 750, 600, 1200]

metric_template = """
    You are a specialist in tracking and evaluation the performance of results from prompts

    You will be given variables such as latency, given in seconds (s). Using this information, you must return whether there is an anomaly or not.

    You will also be given a history for previous latenciues. This will be used as your reference and comparison point.

    Additionally, you should use your own common knowledge to determine an answer and validate the response to not include any unnecessary information. This is important as there will be times where there is very little information gain from the latency history.

    Give the response as either "Normal" or "Anomaly" and provide reasoning behind the decision and how to improve sumarrized in 5 bullet points.

    latency: {latency}

    latency_history: {latency_history}
    """

# Create the chat prompt template
prompt = ChatPromptTemplate.from_template(metric_template)

# Create a chain with the model and the prompt
chain = prompt | llm_base

# Run the chain with a specific input

def evaluate_metrics(id, model, given_prompt, given_response, latency, drift_threshold = 0.85):
    llm_base = ChatGoogleGenerativeAI(model=model)
    llm_v2 = ChatGoogleGenerativeAI(model=model)

    chain_base = prompt | llm_base
    # chain_v2 = prompt | llm_v2

    response_base = chain_base.invoke({
        "latency": latency,
        # "token_usage": token_usage,
        "latency_history": latency_history,
        # "token_usage_history": token_usage_history
        }).content

    # chain_base = given_prompt | llm_base
    # chain_v2 = given_prompt | llm_v2

    result_base = llm_base.invoke(given_prompt).content

    result_v2 = llm_v2.invoke(given_prompt).content

    # Embedding comparison for drift detection
    vec_base = embedding_model.embed_query(result_base)
    vec_v2 = embedding_model.embed_query(result_v2)
    drift = cosine_similarity([vec_base], [vec_v2])[0][0]

    # Determine drift
    drift_status = "Drift Detected" if drift < drift_threshold else "No Drift"

    print("\n--- Evaluation ---")
    print(f"Latency: {latency} s")
    print(f"Response:\n{response_base}")
    # print(f"Response (Baseline):\n{response_v2}")
    print(f"Cosine Similarity: {drift:.3f} --> {drift_status}")
    print("-------------------")
    # TODO: Record all of the processed metrics and add to json object to give to metrics dashboard (check comments in metrics_dashboard.py)

    info = {
        "id": id,
        "model": model,
        "prompt": given_prompt,
        "response": given_response,
        "latency": latency,
        "drift": drift,
        "drift_status": drift_status,
        "entropy": [],
        "relevance": 0.0
        }
    
    # print(info)
    
    try:
        processed_json = json.dumps(info)
        # print(processed_json)
    except TypeError as e:
        print("Serialization error:", e)

    # print(processed_json)

    processed_metrics(processed_json)

    latency_history.append(latency)

    return drift

# evaluate_metrics(100, 100)
# evaluate_metrics(10, 1000)
# evaluate_metrics(50, 600)