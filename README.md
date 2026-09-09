# AICommunityObserver

AICommunityObserver is a middleware observability layer for all GenAI applications. This is a centralized access point for all LLM service providers and 
an automated metric gathering platform all in one.

It sits between your application and model calls, automatically collecting and evaluating inputs without changing how you generate or store prompt and response history. Just include the AICommunityObserver in your application and access the Observer or Observable objects to make your API calls, and centralize all of your AI operations to allow unified monitoring, alerting, security, and accessibility management for all GenAI assets within your application.

By default, AICO does not persist prompt/response text in metric records. Set maintain_privacy=False only when storing the underlying text is appropriate for your application and data-handling requirements. Otherwise, store the prompt str you pass to generate() and the generated response however you choose.

---
## Installation
```bash
pip install ai-community-observer
OR
pip install ai-community-observer[fastapi]
```
---
## Quick start / Minimal Example
```python
from AICommunityObserver import Observable

GEMINI_API_KEY = get_env_variable("GEMINI_API_KEY")

model = Observable(api_key=GEMINI_API_KEY, provider="gemini", model_name="gemini-3.5-flash") if GEMINI_API_KEY else None 

response = model.generate("This is where your prompt goes")

```
Observable fills the default parameters for anything not given in the generate function, automatically runs all of the enabled metric tests, and logs to the default location.
Some providers (like google) can auto-detect api_keys from env, and gemini-3.5-flash is the default, so if you're just running gemini-3.5-flash and your key is saved, then the code snippet below works just fine, however this is not considered best practice.

```python
model = Observable()
```
## Quick start / Minimal Example (For creating metric tests)

---
If you want to create and run a new metric test, each one is implemented as an independent plugin.
By default all files in the src/AICommunityObserver/metrics/plugins directory will be registered to run using:
```
from AICommunityObserver import register_metric

@register_metric(name="relevance.embedding.cosine_similarity")
def compute_cosine_similarity(context):
    ...
```
The `@register_metric` decorator puts the metric function into the registry and the name allows you to group it with like metrics
as well as customize the frequency that the metric will run in configuration options.

Every metric receives the same `MetricContext`.

Metrics are intentionally isolated from one another and communicate only through the shared context.

Example metric categories include:

* embedding similarity
* latency
* hallucination detection
* semantic relevance
* domain-specific evaluation metrics

Researchers extend the framework simply by adding additional metric plugins.

## Configuration
### Observable
Observable's generate() function only requires a prompt, and will auto-populate with any default options defined when initializing the Observable.

For special cases it can also take provider option kwargs such as 
`temperature`, `max_tokens`, `provider_options` etc. which override defaults.

The same is true for Observable-specific options such as 
`testing_freq` and `do_tests`, as well as the id generation for logging.

`return_context`, which changes the output from just a str `response_text`, to a tuple `(response_text, context)`
where `context` is a MetricContext object containing all the necessary information created to run all of the metric plugins.

`metadata` is a dict which contains an arbitrary amount of additional data. 
In Observable it always contains the `maintain_privacy` bool which determines if prompt-response str pairs are stored alongside metrics (not recommended). 

The schema of MetricContext can be accessed or changed through the config.py access points. Within Observable it is constructed like so:

```python
            context = MetricContext(
                prompt=prompt,
                response=response_text,
                latency=duration,
                tokens_used=metadata["tokens_used"],
                model=self.model_name,
                embed_function=self.embed
            )
```

When metric plugins run it will lazy-load and store data as necessary, so if any plugins require an embedding (e.g. semantic similarity)

```python
response, context = model.generate("This is where your prompt goes", return_context=True)
prompt_embeddings = context.prompt_embeddings
response_embeddings = context.response_embeddings
# both return dicts with key = (embedding_model, task_type)

key = ("gemini-embedding-001", "SEMANTIC_SIMILARITY")
prompt_embedding = prompt_embeddings[key]
response_embedding = response_embeddings[key]
```
this becomes valid python to access those embeddings.

To create or access embeddings directly:

```python
embedding model.embed("This is where the text to embed goes")
# Default configurable values are: task_type: str = "SEMANTIC_SIMILARITY", embedding_model: str = "gemini-embedding-001"
```

---

### Metrics
```python
from AICommunityObserver.metrics import set_enabled_metrics

set_enabled_metrics(None)                      # Translates to ALL metrics being enabled, the default
set_enabled_metrics([])                        # Translates to NO metrics being enabled
set_enabled_metrics(["relevance", "toxicity"]) # Enable only the specified metrics
```
---
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
---
### Persistence/ Logging
Metric outputs are collected into structured evaluation records.

Persistence is implemented independently from metric execution, allowing different storage backends to be substituted without changing evaluation logic.

The default backend stores JSONL records to allow immediate use without external infrastructure.

Future persistence backends may include relational databases, vector databases, cloud storage, or streaming systems.

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
---
## Structure

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
---
## Contributing
[Code of Conduct for the Community Contributors](https://acrobat.adobe.com/link/track?uri=urn:aaid:scds:US:1cb574fd-0e7e-440e-baf9-2f835c3ab602)

Contributors have the choice of adding to the package infrastructure or just add a plugin. 

---
## Roadmap
v0.4.0
Support for Gemini and OpenAI text generation + embedding. 
Automated metrics registry. 
Config options for testing frequency, logging location, metric ordering.

v0.5.0
Batched & cached options for generation + embedding. 
Namespace governance functionality (detect and sort metric namespaces on initialization).
Config options for ID, namespace governance, and output data logging schema.
Collect addition of all baseline metric tests as default in the plugins dir alongside an added place to keep experimental ideas from research papers.
Add support for more LLM providers.
Verify api access token support.

v0.6.0
`dashboard` addition accessible from fastapi branch to add metrics dashboard to quickstart.
`testing` addition to automate environment/application compatibility tests.
`benchmarks` addition for metric test variants for benchmarking. Specific variants allow running benchmarks from datasets using AICO infrastructure.

v0.7.0
Expansion of namespace governance and benchmarks to cover cross-industry testing organized into directories (e.g. benchmarks/corruption/mining).
Add infrastructure for GDPA compliant data sharing on cross-industry metric effectiveness.
Enable automated testing for cross-industry task, model, and procedure comparisons.

v???
Explicitly enable metrics beyond single prompt-responses (e.g. conversation history)
Select embedding models according to chosen model and provieder on Observable initialization
[project.entry-points."aicommunityobserver.metrics"] endpoint utilization (auto-registering external plugins)
MCP-specific integration. Support local or server-side testing.
Agent/Model harness monitoring.
Local model loading with hardware detection. 
Enable use of metrics to auto-generate training data.

---
Current Community Contributors to this Repo : 

1- Garima Bajpai -  Community Founder & Support


2- Nisha Iyer - Repo Maintainer and Code Reviewer


3- Jay Shah - Repo Admin and Project Support


4- James Drayton Beninger - Key Contributor & Code Reviewer