# AICommunityObserver

AICommunityObserver is a middleware observability layer for all GenAI applications. This is a centralized access point for all LLM service providers, the pytest of generative AI, and an automated M&E tool all rolled into one.

Without AICO:

application → Gemini/OpenAI/etc.

With AICO:

application → Observable → Gemini/OpenAI/etc.
                        ↓
                 metrics + logging

It sits between your application and model calls, automatically collecting and evaluating inputs without changing how you generate or store prompt and response history. Just include the AICommunityObserver in your application and access the Observer or Observable objects to make your API calls, and centralize all of your AI operations to allow unified monitoring, alerting, security, and accessibility management for all GenAI assets within your application.

By default, AICO does not persist prompt/response text in metric records. Set maintain_privacy=False only when storing the underlying text is appropriate for your application and data-handling requirements. Otherwise, store the prompt str you pass to generate() and 

Code of Conduct for the Community Contributors - https://acrobat.adobe.com/link/track?uri=urn:aaid:scds:US:1cb574fd-0e7e-440e-baf9-2f835c3ab602

## Installation
```bash
pip install ai-community-observer
OR
pip install ai-community-observer[fastapi]
```

## Quick start / Minimal Example
```python
from AICommunityObserver import Observable

GEMINI_API_KEY = get_env_variable("GEMINI_API_KEY")
model = Observable(api_key=GEMINI_API_KEY, model_type="gemini", model_name="gemini-3.5-flash") if GEMINI_API_KEY else None 
response = model.generate("This is where your prompt goes")
```
Observable fills the default parameters for anything not given in the generate function, automatically runs all of the enabled metric tests, and logs to the default location.
Some providers (like google) can auto-detect api_keys from env, and gemini-3.5-flash is the default, so if you're just running gemini-3.5-flash and your key is saved, then
```python
model = Observable()
```
Works just fine, however this is not considered best practice.

## Configuration
### Observable
```python
"""
    Class Observable can be instanced in a module where it is imported such that:
        - The type of model access can be specified for that instance (default API key) if given a key or access token. Options:
            - "api_key" which requires
                - api_key: str
                - Supports: Gemini, OpenAI, HuggingFace models
            - "api_token" which requires
                - token_url: str
                - client_id: str
                - client_secret: str
                - For: Custom API endpoints
        - "model_type" The type of model a.k.a. the provider
        - "model_name" The name of the model (default gemini-3.5-flash). Current options: Gemini, OpenAI, HuggingFace.
        - "testing_freq" A float representing the percentage of calls using this object which will have run tests. Default: 0.1 a.k.a 10%
        - "id_gen" A Callable (function) responsible for id handling. Default: uuid4
        - "provider_options" A dict representing the fine-tuning kwargs passed to provider. E.g.
           provider_options_example={
               "client": {
                   "enterprise": True,
                   "project": "...",
                   "location": "...",
               },
               "generate": {
                   "temperature": 0.8,
                   "top_p": 0.95,
               }
           }

    and the generate function can be called on that instance such that it will prompt the defined model in that instance with a given str.
"""
```
Observable's generate() function only requires a prompt, and will auto-populate with any default options defined when initializing the Observable.

For special cases it can also take provider option kwargs such as "temperature", "max_tokens", "provider_options" etc. which override defaults.

The same is true for Observable-specific options such as "testing_freq" and "do_tests", as well as the id generation for logging.

"return_context", which changes the output from just a str "response_text", to a tuple "(response_text, context)" 
where "context" is a MetricContext object containing all the necessary information created to run all of the metric plugins.

"metadata" is a dict which contains an arbitrary amount of additional data. In Observable it always contains the "maintain_privacy" bool which determines 
if prompt-response str pairs are stored alongside metrics (not recommended). 

The schema of MetricContext can be accessed or changed through the config.py access points. Within Observable it is constructed like so:
            context = MetricContext(
                prompt=prompt,
                response=response_text,
                latency=duration,
                tokens_used=metadata["tokens_used"],
                model=self.model_name,
                embed_function=self.embed
            )
When metric plugins run it will lazy-load and store data as necessary that can also be accessed, so if any plugins require an embedding (e.g. semantic similarity)
```python
prompt_embeddings = context.prompt_embeddings         # returns a dict with key key = (embedding_model, task_type)
response_embeddings = context.response_embeddings     # returns a dict with key key = (embedding_model, task_type)
key = ("gemini-embedding-001", "SEMANTIC_SIMILARITY")
prompt_embedding = prompt_embeddings[key]
response_embedding = response_embeddings[key]
```
this becomes valid python to access those embeddings.

To access embeddings in other contexts:
Observable's embed() functions much like generate(), only it returns the embedding values of the string it has been passed instead of a generated response str.
embed() only requires a str, but can also take optional parameters "task_type" and "embedding_model". 
"task_type" configures the task type (e.g. "RETRIEVAL_DOCUMENT" or "RETRIEVAL_QUERY" for RAG with Google's genai)
"embedding_model" is configured according to Observable's init parameters whenever possible.

### Metrics
```python
from AICommunityObserver.metrics import set_enabled_metrics

set_enabled_metrics(None)                      # Translates to ALL metrics being enabled, the default
set_enabled_metrics([])                        # Translates to NO metrics being enabled
set_enabled_metrics(["relevance", "toxicity"]) # Enable only the specified metrics
```

### The order Metrics runs its tests
```python
from AICommunityObserver.metrics import (
    get_metric_order,
    set_metric_order,
)

# Restore the default alphabetical ordering
set_metric_order()

# Define a custom ordering function
def custom_metric_order(metrics):
    return sorted(
        metrics,
        key=lambda metric: getattr(
            metric,
            "metric_name",
            metric.__name__,
        )
    )

set_metric_order(custom_metric_order)

# Inspect the currently configured ordering function
order_function = get_metric_order()
```

### Persistence/ Logging
```python
from AICommunityObserver.metrics import (
    get_log_file,
    set_log_file,
)

# Use the default location
set_log_file("metrics_log.jsonl")

# Store metrics in a relative path
set_log_file("logs/metrics.jsonl")

# Or provide an absolute path
set_log_file("/path/to/my/application/metrics.jsonl")

# Inspect the current log file path
log_file = get_log_file()
print(log_file)

from AICommunityObserver.metrics import registered_metrics

for metric in registered_metrics:
    name = getattr(metric, "metric_name", metric.__name__)
    print(name)
```

## Structure
1. Metrics module. Contains metrics.py with metrics registry and other files running metrics.
metrics/

2. Observer module. Contains code for generalized API wrappers or loggers to pass into metrics.
observer/

3. (optional) Web module. Contains example applications to run for testing or to demonstrate use cases.
web/

4. TODO: Custom dashboard for displaying logged metrics. More relevant for unique tests.
dashboard/

5. TODO: Benchmarks module. Contains benchmarks organized in industry or domain-specific directories
benchmarks/
    reasoning/
    coding/
    corruption/
        mining/
        agriculture/

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

## Contributing

## Roadmap

## Execution Flow
User / Application
        ↓
Observable (API Wrapper)
        ↓
LLM Provider (OpenAI / Gemini / etc.)
        ↓
MetricContext (standardized data object)
        ↓
metrics.evaluate_metrics()
        ↓
Metric Plugins (registry-based execution)
        ↓
Persistence (JSONL → your DB)
        ↓
Dashboard / Analysis

Current Community Contributors to this Repo : 

1- Garima Bajpai -  Community Founder & Support


2- Nisha Iyer - Repo Maintainer and Code Reviewer


3- Jay Shah - Repo Admin and Project Support


4- James Drayton Beninger - Key Contributor & Code Reviewer