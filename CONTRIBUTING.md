# CONTRIBUTING.md

# Contributing to AICommunityObserver

Thank you for contributing to AICommunityObserver.

This project is intended to be an extensible framework for observing, evaluating, and comparing LLM interactions. Contributors are encouraged to understand the architectural goals before implementing new functionality.

At present, this (CONTRIBUTING.md) document is probably 50% AI generated, and so has limited use, although all of the essential context within it (structure etc.) is valid and useful.

---

# Project Philosophy

AICommunityObserver has two primary audiences.

### Developers

Developers should be able to add observability to an existing LLM application with minimal changes.

The preferred integration is through an `Observable` object which wraps a **single generation model** while preserving the application's normal behavior.

### Researchers

Researchers should be able to implement new evaluation methods without needing to understand provider APIs, persistence, dashboards, or other framework internals.

A new evaluation technique should typically require nothing more than implementing a metric plugin.

This can be done using the `@register_metric(name)` decorator. 
---

# Core Architectural Principle

The framework is **not** organized around providers or metrics.

It is organized around **MetricContext**.

Every model interaction becomes a single `MetricContext`.

Every metric receives that same context.

Expensive computations should be exposed through `MetricContext` so they can be reused rather than recomputed.

Whenever adding new functionality, first ask:

> "Should this become part of MetricContext rather than being implemented independently inside a metric?"

---
# Quick Start
TODO

# Current Project Structure

```
AICommunityObserver/
├── .gitignore
├── .gitmodules
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── snapshot.md
├── pyproject.toml
├── requirements.txt
│
└── src/
│    └── AICommunityObserver/
│        ├── __init__.py
│        ├── env.py (no internal imports)
│        ├── metrics/
│        │   ├── __init__.py (from .metrics import evaluate_metrics, register_metric, registered_metrics, is_evaluation_active
│        │   │                from .context import MetricContext 
│        │   │                from .config import get_enabled_metrics, set_enabled_metrics, set_log_file, get_log_file, is_metric_enabled, get_metric_order, set_metric_order)
│        │   ├── metrics.py (from .context import MetricContext and from .config import is_metric_enabled) 
│        │   ├── context.py
│        │   ├── config.py
│        │   └── plugins/* (from ..metrics import register_metric)
│        ├── observer/
│        │   ├── __init__.py (from .observable import Observable)
│        │   └── observable.py (contains Observable class and from ..metrics import evaluate_metrics)
│        └── web/
│            ├── __init__.py (from .testing import testing)
│            ├── main.py (from . import testing  and from . import customization)
│            ├── customization.py (from ..metrics import MetricContext, registered_metrics, get_enabled_metrics, set_enabled_metrics)
│            └── testing.py (from ..observer import Observable and from ..env import get_env_variable)
│
├── dashboard/      (planned)
└── benchmarks/     (planned)
```
# Separation of Responsibilities

The project intentionally separates concerns.

## Observable

Responsible for:

* communicating with model providers
* generating responses
* generating embeddings
* collecting request metadata
* constructing MetricContext
* invoking the metrics engine

Observable should **not** contain evaluation logic.

---

## MetricContext

Represents a single evaluated interaction.

It stores request-level information such as:

* prompt
* response
* model
* latency
* token usage
* metadata

It also owns shared cached resources.

Currently this includes:

* prompt embeddings
* response embeddings

Future shared resources may include:

* language detection
* tokenization
* log probabilities
* provider-specific metadata
* additional cached inference products

Metrics should obtain these values from the context whenever possible rather than recomputing them.

---

## Metrics

Metrics should be:

* independent
* deterministic where practical
* focused on a single evaluation task
* unaware of other metrics

Metrics should never communicate directly with one another.

Shared computation belongs in MetricContext.

---

## Persistence

Persistence consumes metric results.

Evaluation should remain independent from storage implementation.

The default backend writes JSONL files, but future storage backends should be interchangeable.

---

# Plugin Philosophy

The metric plugin system is intended to be the primary extension point of the framework.

Each plugin should:

* register itself automatically
* accept a MetricContext
* return a structured metric result
* avoid side effects

Example:

```python
@register_metric(
    name="relevance.embedding.cosine_similarity"
)
def cosine_similarity(context):
    ...
```

Metrics should generally not perform provider initialization or manage caching themselves.

---

# Naming Convention

Metric names should be namespaced.

Example:

```text
latency.value
relevance.embedding.cosine_similarity
hallucination.claim_support
toxicity.response
```

Names should describe *what is being measured*, not how it is implemented.

---

# Current Extension Points

The framework is designed to support independent evolution of:

* model providers
* evaluation metrics
* persistence backends
* dashboards
* benchmark suites

When adding new functionality, prefer introducing a new extension point rather than modifying existing modules.

---

# Planned Direction

The following architectural goals guide future development.

## Observer

A future `Observer` object is planned.

Unlike `Observable`, it will not perform inference.

Instead it will evaluate existing prompt-response pairs supplied by external applications.

This provides observability without requiring applications to replace their existing inference client.

---

## Richer Metric Registry

The current registry stores registered metric callables.

The long-term goal is to support richer metadata such as:

* tags
* categories
* versions
* dependencies
* package origin

This will enable more flexible discovery, configuration, and third-party metric packages.

---

## Third-Party Metric Packages

One long-term objective is supporting independently distributed metric collections.

For example:

```text
aco-bias-metrics
aco-medical-metrics
aco-security-metrics
```

These packages should be installable independently while integrating seamlessly with the existing metric registry.

---

## Benchmarks

Benchmarks should combine:

* prompt datasets
* existing metrics
* standardized evaluation procedures

Benchmarks should generally reuse metric plugins rather than implementing evaluation algorithms directly.

---

# Design Guidelines

When contributing new features, prefer the following:

✔ Move shared logic into MetricContext.

✔ Keep metrics small and composable.

✔ Keep provider-specific logic inside Observable.

✔ Prefer extension over modification.

✔ Preserve compatibility with existing integrations whenever possible.

---

# Things to Avoid

Avoid introducing unnecessary coupling between modules.

Examples include:

* metrics depending on other metrics
* metrics performing persistence
* providers containing evaluation logic
* dashboards depending on provider implementations

The architecture is intentionally layered.

---

# Current Project Status

The framework currently provides:

* Observable-based model integration
* MetricContext
* automatic metric registration
* plugin-based evaluation
* configurable metrics
* JSONL persistence

Planned work includes:

* Observer
* richer registry metadata
* benchmark framework
* visualization dashboard
* additional persistence backends
* third-party plugin ecosystem

These goals should guide contributions, but implementation details are expected to evolve as the project grows.

**Output schema per run of evaluate_metrics**
NOTE: This is missing the prompt and response. It just contains the metrics for this instance.
{
    "timestamp": 1786620909.6240191, 
    "data": 
        {
            "id": "53827493-f177-4a05-aab0-5c29686975b8", 
            "model": "gemini-3.5-flash", 
            "metadata": 
                {
                "maintain_privacy": true, 
                "latency": 2.557722806930542, 
                "tokens_used": 300, 
                "embedding_model": "gemini-embedding-001", 
                "do_tests": true
                }, 
            "metrics": 
                {
                    "relevance.embedding.cosine_similarity": 0.8973972227783809
                }
        }
}
This will also contain the prompt and response in the json data IFF maintain_privacy is set to false. Otherwise:
{
    "timestamp": 1787041075.7764058, 
    "data": 
        {
            "id": "4fcac831-0b5a-446b-bd3e-6c98f57e47e6", 
            "model": "gemini-3.5-flash", 
            "prompt": "Hi, this is an api test to demo how logging works. All good?", 
            "response": "Hi there! Yes, all good! - The API", 
            "metadata": 
                {
                    "maintain_privacy": false, 
                    "latency": 10.778486490249634, 
                    "tokens_used": 269, 
                    "embedding_model": 
                    "gemini-embedding-001", 
                    "do_tests": false
                }, 
            "metrics": {}
        }
}



**NOTE: Forget about batch testing flask/fastapi endpoint examples for now. Only implement as needed for actual testing**

**Test Ideas**
1. Anthropic introduced "BrowseComp" to benchmark model performance finding information online. This could be tested across models for domain-specific tasks.
    - https://www.anthropic.com/engineering/eval-awareness-browsecomp 
2. The Assistant Axis. Difficult to operationalize but good to keep track of or try to use.
    - https://arxiv.org/pdf/2601.10387 
3. **Easy** Sklearn cosine similarity
4. Jones Walker suggests automation bias and behaviour drift as particular vulnerabilities of GenAI implementation, and proposes solutions:
   Randomized manual sampling, adversarial audits, and defined stop protocols. Track behavioural patterns over time.
    - https://www.joneswalker.com/en/insights/blogs/ai-law-blog/governing-ai-that-acts-part-2-control-in-name-only.html
5. Proposal requires contractors to "identify whether [AI systems used] were modified to comply with non-US or commercial frameworks, and provide documentation tied to compliance, reporting, and use restrictions"
    - https://www.nextgov.com/acquisition/2026/04/trade-and-industry-groups-warn-risks-gsas-draft-ai-procurement-guidance/412614/ 

System Description (LLM-Friendly Context)

AICommunityObserver is a modular observability framework for LLM applications. It is designed to evaluate prompt-response interactions using configurable metrics without requiring changes to existing application logic.

The system introduces an Observable wrapper that replaces or wraps standard model API calls. When a prompt is sent through Observable, it forwards the request to the underlying model provider, captures the response, measures latency, and constructs a MetricContext object containing all relevant data for evaluation.

This context is passed to a metrics engine, which dynamically loads and executes registered metric plugins. Each plugin is a simple function that accepts the context and returns a scalar value. Metrics are namespaced (e.g., relevance.cosine_similarity, latency.value) to allow multiple evaluation strategies to coexist and be compared.

The MetricContext also provides shared resources such as embeddings. These are computed lazily and cached per request, so multiple metrics can reuse them without redundant computation.

Metric execution is controlled through a runtime configuration system exposed via API endpoints. Users can query available metrics and enable or disable specific ones without modifying code.

Results from each evaluation are aggregated into a structured dictionary and written to a JSONL log file. This file serves as the default persistence layer and can be replaced with a custom database if needed.

The framework is intended for both developers and researchers. Developers can integrate it into existing applications to collect performance and quality metrics, while researchers can contribute new evaluation methods as plugins and compare them within a unified system.