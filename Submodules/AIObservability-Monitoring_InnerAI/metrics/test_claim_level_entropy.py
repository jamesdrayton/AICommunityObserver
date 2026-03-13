import os
import google.generativeai as genai
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import transformers
transformers.logging.set_verbosity_error()
import torch
import math
from collections import Counter
import time
import json

# Configure Gemini API
api_key = "AIzaSyBqCqiKfAr8y6gesvYRUvemhYhwsjwdsjs"
genai.configure(api_key=api_key)
gemini_model = genai.GenerativeModel('gemini-2.0-flash-lite')

# Load DeBERTa-MNLI model
tokenizer = AutoTokenizer.from_pretrained("microsoft/deberta-large-mnli")
entailment_model = AutoModelForSequenceClassification.from_pretrained("microsoft/deberta-large-mnli")



def decompose_paragraph(paragraph):
    prompt = f"""
Please list the specific factual propositions included in the following paragraph. Be complete and do not leave any factual claims out. Provide each claim as a separate sentence in a separate bullet point.

Paragraph:
{paragraph}
"""
    response = gemini_model.generate_content(prompt)
    text = response.text if hasattr(response, "text") else ""

    # Normalize lines and remove bullet formatting
    raw_lines = text.strip().splitlines()
    claims = [line.lstrip("*•-1234567890. )").strip() for line in raw_lines if line.strip()]
    
    # Filter out non-claim lines like introductory statements
    filtered_claims = [c for c in claims if is_potential_claim(c)]
    return filtered_claims

def generate_questions(claim):
    prompt = f"""
You see the sentence:
"{claim}"
Generate 3 fact-checking questions that directly test the truth of this claim. Each question should include the entities or events from the sentence (e.g., place names, people, dates) and aim to elicit a factual, concise answer. Avoid vague or generic phrasing.

Format:
1. Question
2. Question
3. Question
"""
    response = gemini_model.generate_content(prompt)
    text = response.text if hasattr(response, "text") else ""

    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
    questions = []
    for line in lines:
        # Extract only lines starting with 1., 2., or 3.
        if line[0] in "123" and (len(line) > 1 and line[1] in [".", ")"]):
            # Remove leading number and punctuation
            question = line[2:].strip()
            questions.append(question)
    # If fewer than 3 questions generated, pad with empty strings or fallback
    while len(questions) < 3:
        questions.append("N/A")
    return questions

def generate_answers(question, num_answers=3):
    prompt = f"""
We are writing an answer to the question: "{question}"
Please provide a concise one sentence answer.
"""
    answers = []
    for _ in range(num_answers):
        try:
            response = gemini_model.generate_content(prompt)
            answer = response.text.strip() if hasattr(response, "text") else ""
            if not answer:
                answer = "UNKNOWN"
            answers.append(answer)
        except Exception as e:
            print(f"Error generating answer: {e}")
            answers.append("UNKNOWN")
        time.sleep(4.5)  # Respect rate limits
    return answers

def compute_entropy(claim, answers):
    labels = []
    for answer in answers:
        inputs = tokenizer.encode_plus(claim, answer, return_tensors="pt", max_length=512, truncation=True, padding="max_length")
        with torch.no_grad():
            logits = entailment_model(**inputs).logits
        probabilities = torch.softmax(logits, dim=1).squeeze()
        label = torch.argmax(probabilities).item()  # 0: contradiction, 1: neutral, 2: entailment
        labels.append(label)
    label_counts = Counter(labels)
    total = sum(label_counts.values())
    entropy = -sum((count / total) * math.log2(count / total) for count in label_counts.values() if count > 0)
    return entropy, labels


def get_verdict(entropy, labels):
    majority_label = Counter(labels).most_common(1)[0][0]

    if entropy < 0.5:
        if majority_label == 2:
            return "LIKELY TRUE"
        elif majority_label == 0:
            return "LIKELY FALSE"
        else:
            return "POSSIBLY TRUE"  # Neutral majority but low entropy → mild trust

    elif entropy < 1.0:
        if majority_label == 2:
            return "POSSIBLY TRUE"
        elif majority_label == 0:
            return "POSSIBLY FALSE"
        else:
            return "UNKNOWN"  # Neutral and mid entropy → very unsure

    elif entropy < 1.5:
        return "UNKNOWN"

    else:
        return "UNKNOWN"
def is_potential_claim(sentence: str) -> bool:
    if not sentence or sentence.strip() == "":
        return False
    lowered = sentence.lower()
    # Filter out introductory or meta lines
    invalid_phrases = [
        "Here's a breakdown of the factual propositions",
        "here are the factual propositions",
        "presented as separate bullet points",
        "here are three fact-checking questions",
        "fact-checking questions",
        "generated questions",
        "answers"
    ]
    for phrase in invalid_phrases:
        if phrase in lowered:
            return False
    if len(sentence.split()) < 5:
        return False
    return True

def evaluate_claims(paragraph, verbose=True):
    claims = decompose_paragraph(paragraph)
    results = []

    for claim in claims:
        if verbose:
            print("============================================================")
            print(f"Claim: {claim}")

        questions = generate_questions(claim)
        if verbose:
            print("\nGenerated Questions:")
            for q in questions:
                print(f"  - {q}")

        all_answers = []
        if verbose:
            print("\nAnswers:")
        for q in questions:
            if q == "N/A":
                if verbose:
                    print("  Q: No valid question generated")
                continue
            answer_list = generate_answers(q)
            if verbose:
                print(f"  Q: {q}")
                for ans in answer_list:
                    print(f"    A: {ans}")
            all_answers.extend(answer_list)

        if all_answers:
            entropy_score, labels = compute_entropy(claim, all_answers)
            verdict = get_verdict(entropy_score, labels)
            if verbose:
                print(f"\nEntropy: {entropy_score:.4f}")
                print(f"Labels: {labels}  (0=Contradiction, 1=Neutral, 2=Entailment)")
                print(f"Verdict: {verdict}")
        else:
            verdict = "UNKNOWN"
            if verbose:
                print("\nNo answers generated; skipping entropy and verdict.")

        results.append((claim, verdict, entropy_score))

        if verbose:
            print("============================================================\n")

    return results




# Example usage
if __name__ == "__main__":
    paragraph = """
    The Eiffel Tower is located in Berlin. Paris is the capital of France. The Great Wall of China can be seen from space.
    """
    # read json file and retriteve the response text
    filename = "C:\\Users\\tamog\\OneDrive\\Desktop\\AIObservability-Monitoring_InnerAI\\logs\\1748891749_005353.json"

    if os.path.exists(filename):
        with open(filename, "r") as f:
            data = json.load(f)
            paragraph = data.get("response", "")
    else:
        print(f"File {filename} does not exist. Using default paragraph.")

    results = evaluate_claims(paragraph)

    # Extract entropies and verdicts
    entropies = []
    verdicts = []
    for _, verdict, entropy in results:
        verdicts.append(verdict)
        entropies.append(entropy)

    # Update the JSON structure
    data["entropies"] = entropies
    data["verdicts"] = verdicts

    # Write back to same JSON file
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nUpdated {filename} with entropies and verdicts.")

    #save the results to a json file






