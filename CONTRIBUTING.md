
## TO-DO:
1. Reorganize directories for main project
    - Stick to the innerAI original model, the rest can be incorporated into that. Rename API Wrapper to observer.
    - Dir metrics stub contains metrics.py
    - Dir testing strub contains sample flask and/or fastapi app (relevant for 2)
    - Dir API Wrapper/ observer stub contains observable.py and APIWrapper class becomes Observable
2. Fill out directories with AI Farmer version of InnerAI and remove any ACADES-specific code
    - Test with local API (python -m main)
3. Implement metrics.py to evaluate prompts and responses through other tests listed in the module
    - For stub, just have it log the prompts and responses
4. Add Observer python file and object to observer dir, this modifies the wrapper but instead has prompt-responses passed manually
5. Implement basic metrics tests from submodules to log for 6
6. Implement and test dashboard and other logging display systems
7. 

## IN-PROGRESS:


## IN-REVIEW:


## DONE:



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
        - 

**Minimum use outputs:**
1. Dashboard
2. Feedback logging

**NOTE: Forget about batch testing, flask/fastapi endpoint examples for now. Only implement as needed for testing**

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

**For later:**
1. Anthropic introduced "BrowseComp" to benchmark model performance finding information online. This could be tested across models for domain-specific tasks.
    - https://www.anthropic.com/engineering/eval-awareness-browsecomp 
2. The Assistant Axis. Difficult to operationalize but good to keep track of or try to use.
    - https://arxiv.org/pdf/2601.10387 