
import numpy as np

from sklearn.metrics.pairwise import cosine_similarity
from env import get_env_variable
from metrics.metrics import register_metric
from metrics.metric_analysis import initialize_embeddings

@register_metric(name="relevance.embedding.cosine_similarity")
def compute_cosine_similarity(context):
    """
    Compute cosine similarity between prompt and response embeddings.

    Expects the record to contain 'prompt_embedding' and 'response_embedding' fields,
    which should be lists of floats representing the respective embeddings.

    Args:
        record: dict containing 'prompt_embedding' and 'response_embedding'

    Returns:
        Cosine similarity score between -1 and 1
    """
    if not context.prompt or not context.response:
        return None

    try:
        vec_prompt = context.get_prompt_embedding()
        vec_response = context.get_response_embedding()
        similarity = cosine_similarity(vec_prompt.reshape(1, -1), vec_response.reshape(1, -1))[0][0]
        # similarity = cosine_similarity(np.vstack([vec_prompt, vec_response]))[0][1]

        return float(similarity)
    except Exception as e:
        print(f"Error computing cosine similarity: {e}")
        return None