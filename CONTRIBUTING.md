
**Numbers correspond with module numbers in README->Structure**
## TO-DO:

1. Update MetricContext to include embedding and create embeddings from evaluate_metrics to pass to tests (if case multiple uses for it)

1. Implement basic metrics tests from submodules to log.

1. Refactor test_claim_level_entropy.py

1. Convert GenA11 evaluate_prompts.py into a register-able fn in metrics/

1. Double check and add dockerfile to the git

================== Past point of MVP ===================

2. Implement the id schema passed to evaluate_metrics, then make it configurable through a flask endpoint

2. Add a customization endpoint for the order of metrics iteration in evaluate_metrics (default alphabetical)

2. Add Observer python file and object to observer dir, this modifies the wrapper but instead has prompt-responses passed manually

4. Implement and test dashboard and other logging display systems

1. Implement asynchronous or batch testing options for price efficiency.

1. Metrics langchain llm-based analysis. Planned and partially implemented:
    - Pass aggregated runtime metrics from test runs
    - Generalize metric_template to accept a dict -> str for adaptability instead of every individual metric
    - Use langchain llm to summarize failures in software or anomalies in metrics and suggest causes
    Future implementations should evaluate whether:
    - LLM analysis adds meaningful signal over traditional observability tooling
    - embeddings + vector search are necessary for incident comparison

2. Implement custom api access (secret, api token, http request level access for custom models)

3. Create testing endpoint to accept database of prompt-response pairs for evaluation

## IN-PROGRESS:


## IN-REVIEW:

## DONE:
1. Add metrics_context object in its own file and create a class for it. This will be a configuration point for users.
1. Implement metrics.py
3. Add API blueprint outside of testing.py to use as a customization placeholder. 
    - Lays foundation for selected industry benchmarks, id/model schema, percentage measurements, etc.
    - Start with GET /metrics/schema to access the MetricsContext shape in context.py

## General
**Minimum use inputs/ entry points:**
1. API Wrapper (Observable) object to call generation on
    - Accomplished with: APIWrapper.py in innerAI
2. Performance logger (Observer) object to pass text into (subsitute for api calls) representing prompts and responses

In both cases the inputs (prompt-response pairs) are passed to metrics, which runs configured tests (entry point for research contributors).
The metrics module creates logs of the inputs and test results, which the dashboard then reads.

**Minimum use processing:**
1. Metrics modular testing through metrics.py, connected to API Wrapper or Performance Logger
    - Accomplished with: 
        - relevancy_check.py (innerAI)
        - evaluate_claim_level_entropy.py (innerAI) + test_claim_level_entropy.py (innerAI)
        - evaluate_prompts.py (GenA11)

**Minimum use outputs:**
1. Dashboard
2. Feedback logging

**Output schema per run of evaluate_metrics**
NOTE: This is missing the prompt and response. It just contains the metrics for this instance.
{
  "id": "123",
  "model": "",
  "metrics": {
    "latency.value": 0.42,
    "response.length": 120,
    "drift.semantic_similarity": 0.96
  }
}

**NOTE: Forget about batch testing flask/fastapi endpoint examples for now. Only implement as needed for actual testing**

## Submodules:

**A11**
To-take:
1. OpenAI integration should be merged into the existing one in InnerAi
2. User rating easy and good to have. Effectively copy paste.
3. Prompt versioning doesn't hurt to take
4. DevOps automation (CI/CD).
5. Docker option (Integrate with others)

Question:
1. Feedback logging with weights and biases as opposed to existing logging

For later:
1. AWS integration (good model for other cloud integration and testing of MCP, etc.)

**InsightAI**
To-take:
1. Basic key performance indicators/tests: latency, token throughput, successful requests
2. Grafana dashboard (possible placeholder)
3. Docker (Integrate with others)

Question:
1. Advance alerts through slack. Careful with bot creation so as not to spam like in the demo.

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