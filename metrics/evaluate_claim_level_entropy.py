import math
from collections import Counter
from sklearn.metrics import accuracy_score, f1_score

from test_claim_level_entropy import decompose_paragraph, generate_questions, evaluate_claims


# Ground truth for each atomic factual claim
truth_labels = {
    "The Eiffel Tower is located in Berlin.": False,
    "Paris is the capital of France.": True,
    "The Great Wall of China can be seen from space.": True,
    "The moon is made of cheese.": False,
    "The sun rises in the east.": True,
    "Water freezes at 0 degrees Celsius.": True,
    "The capital of France is Paris.": True,
    "The Earth revolves around the Sun.": True,
    "Humans can breathe underwater.": False
}

# Sample test paragraphs
sample_paragraphs = [
    "The Eiffel Tower is located in Berlin. Paris is the capital of France. The Great Wall of China can be seen from space.",
    "The moon is made of cheese. The sun rises in the east. Water freezes at 0 degrees Celsius.",
    "The capital of France is Paris. The Earth revolves around the Sun. Humans can breathe underwater."
]

# Map verdicts to truth values
verdict_to_bool = {
    "LIKELY TRUE": True,
    "POSSIBLY TRUE": True,
    "LIKELY FALSE": False,
    "POSSIBLY FALSE": False,
    "UNKNOWN": None  # We'll skip "UNKNOWN" in accuracy/F1 computation
}

def run_entropy_evaluation():
    y_true = []
    y_pred = []

    for paragraph in sample_paragraphs:
        print(f"\nEvaluating paragraph:\n{paragraph}\n{'='*60}")
        results = evaluate_claims(paragraph, verbose=True)

        for claim, verdict in results:
            pred_label = verdict_to_bool.get(verdict, None)
            clean_claim = claim.lstrip("*•- ").strip()
            true_label = truth_labels.get(clean_claim, None)


            print(f"Claim: {claim}")
            print(f"  Verdict: {verdict}")
            print(f"  Ground Truth: {true_label}")

            if true_label is not None and pred_label is not None:
                y_true.append(true_label)
                y_pred.append(pred_label)

    print("\n=== Evaluation Metrics ===")
    accuracy = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)
    print(f"Accuracy: {accuracy:.4f}")
    print(f"F1 Score: {f1:.4f}")

if __name__ == "__main__":
    run_entropy_evaluation()
