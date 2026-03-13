## How to use as a developer

1. After installing the necessary packages run "python -m main" in the innerAI directory <br>
2. Access the flask apidocs at http://127.0.0.1:8000/docs or http://localhost:8000/docs <br>
3. Most of the relevant flask endpoints are within the "Monitoring and Evaluation" category and contain their own documentation <br>

The innerAI dashboard is a more fine-grained but less intuitive version of the general dashboard. It links to the general dashboard and allows you to run tests which will show up there. <br>
It also allows you to run more specific manual tests on the production models which use data read from csv files in the testing module. These are for investigating flags triggered on the dashboard <br>
which suggest issues like model drift, high numbers of hallucinations, inaccuracy, language issues, etc. <br>
Other endpoints allow you to make direct queries to the model with different system prompts than the default, retrieve histories of queries 

4. In specific cases, the "Training" category is necessary. This can make direct changes to the models and which one(s) are being used in deployment <br> 

When you've confirmed if there are issues with the model using the specific tests, you can then re-train the model with data prepared or gathered from the initial training or since then during deployment. <br>
Finally, you can control which models are being used as the default responses to queries in AIFarmer in production, retrieve a list of all available models, 

# Module structure

| Module         | Role                                                                                                                                                                                           |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **testing**    | Core interface for live-testing inference, fine-tuning, benchmarking. Hosts a Flask Blueprint (Swagger-accessible) for developers to trigger experiments and monitor metrics.                  |
| **APIWrapper** | Middleware intercepting API calls from the Flask Blueprint to route requests/responses through the metrics system. Provides hooks for evaluation and data logging during production inference. |
| **metrics**    | Handles metric computation and persistence. Measures model-level KPIs (e.g., loss trends, BLEU/accuracy, hallucination frequency, drift).                                                      |
| **dashboard**  | Visualization layer for developers linked to dashboard stack. Displays telemetry from the `metrics` module and enables ongoing evaluation. 

Note that metrics.py in the final product is intended to be a midpoint for tests which can be defined in other files from the metrics module (the directory).

**Category: APIWrapper / Inference middleware**

# TODO Summaries
Aggregate progress: ~10%

API-1: Hardware detection & client selection
- File / reference: `APIWrapper/api_wrapper_impl.py` (TODO: Detect hardware; alternate client selection)
- Description: Implement reliable hardware detection (CPU-only vs GPU with available VRAM) and choose between `InferenceClient` and `Unsloth FastLanguageModel` (or similar local client). Provide feature flags/env var override.
- Acceptance criteria:
  - Function `detect_hardware()` returns an enum {cpu, small_gpu, large_gpu}.
  - `APIWrapper.__init__` uses detection + config to choose client implementation.
  - Clear unit tests or simulated detections covering each branch.
- Complexity: Medium
- Est. human time: 1–2 days
- Agent-ease: Moderate (can implement heuristics; hardware testing needs human/dev env)
- Progress notes: Skeleton TODOs exist; model-switching code points present. Progress: ~10%

API-2: Metrics plumbing & debug
- File / reference: `APIWrapper/api_wrapper_impl.py` (TODO 4: Debug metrics; commented evaluate_metrics call)
- Description: Reconnect metrics collection pipeline (calls into `metrics.*`), ensure async/sync boundaries handled, and surface failures safely.
- Acceptance criteria:
  - Metrics calls are made after responses are received, non-blocking (async) or executed in background worker.
  - Failures in metrics do not break inference; they are logged and retried if appropriate.
  - Unit tests that mock metrics module and assert expected calls.
- Complexity: High
- Est. human time: 2–3 days
- Agent-ease: Moderate (requires reading `metrics` module and writing integration tests)
- Progress notes: Metrics hooks partially present but commented. Progress: ~5%

API-3: Logging threshold & retention
- File / reference: `APIWrapper/api_wrapper_impl.py` (Create a threshold of changes... file bloat)
- Description: Add logic to only persist logs that exceed configured relevance thresholds (e.g., drift > X, confidence < Y) and implement log rotation/retention.
- Acceptance criteria:
  - Configurable threshold options in env or config file.
  - Logs below threshold are sampled or skipped; important logs always retained.
  - Rotation (daily/size-based) or TTL is implemented for `logs/`.
- Complexity: Low–Medium
- Est. human time: 4–8 hours
- Agent-ease: Easy (straightforward code changes)
- Progress notes: Only TODO comment. Progress: 0%

API-4: Support `access_type: api_token` for generate path
- File / reference: `APIWrapper/api_wrapper_impl.py` (TODO: Make work with access_type: api_token)
- Description: Ensure `generate()` works for `api_token` access; provide helper wrappers to build url/headers/body and reuse token cache.
- Acceptance criteria:
  - `get_access_token()` returns valid token and caches it.
  - `generate()` handles `access_type == 'api_token'` by making the provided request and returning consistent text result.
  - Tests that mock `httpx` calls validate behavior.
- Complexity: Low
- Est. human time: 4–8 hours
- Agent-ease: Easy (scripting + tests)
- Progress notes: Basic token retrieval exists; branch in generate is skeleton. Progress: ~10%

API-5: Prompt interception & training-data logging
- File / reference: `APIWrapper/api_wrapper_impl.py` (TODO: prompt interception and DB logging)
- Description: Add a hook point to mutate prompts (for region/username tagging), apply privacy filters, and optionally store (masked) prompts+responses to DB for retraining.
- Acceptance criteria:
  - Interception hook (callable) pluggable through `APIWrapper` init.
  - Stored examples are masked/anonymized and meet privacy rules.
  - Config switch to enable/disable training logging.
- Complexity: Medium
- Est. human time: 1–2 days
- Agent-ease: Moderate (DB integration and policy decisions need human oversight)
- Progress notes: TODO placeholders exist. Progress: 0%

API-6: Namevariable->metrics & drift recording
- File / reference: `APIWrapper/api_wrapper_impl.py` (TODO: namevariable, Record the drift amount)
- Description: Ensure each `logs/*.json` entry is passed to `metrics` with an ID and drift is computed and stored.
- Acceptance criteria:
  - `metrics` API receives the filename/ID and returns (or stores) a drift number.
  - Drift value persisted and surfaced in logs/dashboard.
- Complexity: Low
- Est. human time: 4–8 hours
- Agent-ease: Easy
- Progress notes: File creation exists but integration incomplete. Progress: 5%

API-7: Troubleshoot `api_token` branch behavior
- File / reference: `APIWrapper/api_wrapper_impl.py` (TODO: troubleshoot this elif)
- Description: Harden the `api_token` request branch and ensure errors are handled consistently.
- Acceptance criteria:
  - Clear error messages if url/headers/body missing.
  - Return consistent result shape across branches.
- Complexity: Low
- Est. human time: 4 hours
- Agent-ease: Moderate
- Progress notes: Branch exists but minimally tested. Progress: 5%

API-8: Model list generation and `._detect_model_type` refinement
- File / reference: `APIWrapper/api_wrapper_impl.py` (TODO: Assess model list, TODO Evaluate this)
- Description: Replace hard-coded `openai_models` with a maintained source or lightweight heuristic; refine detection logic and coverage.
- Acceptance criteria:
  - Smaller, maintainable lookup or configurable list.
  - Detection unit tests for representative names.
- Complexity: Low
- Est. human time: 4 hours
- Agent-ease: Easy
- Progress notes: `_detect_model_type` exists but can be improved. Progress: 20%

---

**Category: Testing / `training_env.py` (RL / test harness)**

Aggregate progress: ~20%

ENV-1: Action-type support (string vs token)
- File / reference: `testing/training_env.py` (TODOs at top: string or token-level actions)
- Description: Support token-level actions (adjust reward calc and termination) and preserve string-mode compatibility.
- Acceptance criteria:
  - `action_type` configurable to `str` or `tokens`.
  - Token-mode returns partial-step states until end-of-sequence.
  - Tests simulate simple token sequences and assert episode behavior.
- Complexity: Medium
- Est. human time: 1–2 days
- Agent-ease: Moderate (requires test harness + tokenization library)
- Progress notes: Structure for string actions present. Progress: 10%

ENV-2: ID handling & `sent_id` parsing correctness
- File / reference: `testing/training_env.py` (TODO: Confirm how to do the ID)
- Description: Decide canonical ID encoding and implement robust parsing (avoid fragile slicing like `sent_id[2:]`).
- Acceptance criteria:
  - `sent_id` parsing logic documented and unit-tested with sample `sent_id` variants.
  - No exceptions on malformed `sent_id` (graceful fallback).
- Complexity: Low
- Est. human time: 4 hours
- Agent-ease: Easy
- Progress notes: Current code slices `sent_id`. Progress: 20%

ENV-3: Include answers in `obs` & associate reward with response
- File / reference: `testing/training_env.py` (TODO: Should obs contain the answers)
- Description: Optionally include ground-truth answers in observations for supervised RL setups and ensure returned reward maps to the agent's last action.
- Acceptance criteria:
  - Config flag to include answers in `obs` for offline training only.
  - Reward computation uses matched candidate score or fallback logic.
- Complexity: Medium
- Est. human time: 1 day
- Agent-ease: Moderate
- Progress notes: TODOs noted around obs. Progress: 5%

ENV-4: Group extraction by `query_id` & score extraction
- File / reference: `testing/training_env.py` (groupby logic at init; TODOs around candidates)
- Description: Ensure `step()` extracts the correct group for scoring and implements robust matching between action and candidate answers.
- Acceptance criteria:
  - `dataset` grouping is correct and resilient to ordering.
  - Matching uses `_normalize_text` and handles near-misses if configured.
  - Unit tests validate matching and fallback behavior.
- Complexity: Medium
- Est. human time: 1–2 days
- Agent-ease: Moderate
- Progress notes: Grouping logic implemented; matching loop exists. Progress: 30%

ENV-5: Reward calculation correctness & `tau` validation
- File / reference: `testing/training_env.py` (TODOs for reward calc, tau)
- Description: Walk through one example group by hand, validate `normalize_scores`, `group_relative_rewards`, `plackett_luce_from_scores`, and finalize reward choice and formatting penalties.
- Acceptance criteria:
  - Manual worked example documented in tests/notebook.
  - Unit tests confirm expected reward outputs for sample groups.
  - `tau` behavior documented and test coverage added.
- Complexity: High
- Est. human time: 2–4 days
- Agent-ease: Hard (requires domain knowledge and verification by human)
- Progress notes: Utility functions in place but need formal verification. Progress: 10%

ENV-6: Batch-test accessibility via APIWrapper
- File / reference: `testing/training_env.py` & `testing/testing.py` (TODO: prepare to make this accessible through batch_test or another in APIWrapper)
- Description: Expose batch-test runner that calls `APIWrapper` programmatically, collects experiences, and writes experience CSVs used by env.
- Acceptance criteria:
  - `batch_test()` helper that accepts model wrapper and writes experience file matching expected schema.
  - Integration test that runs with a mocked wrapper.
- Complexity: Low–Medium
- Est. human time: 1–2 days
- Agent-ease: Moderate
- Progress notes: Some references in code; needs wiring. Progress: 0%

---

**Category: Testing / `testing.py` & batch tests**

Aggregate progress: ~15%

TEST-1: Add user feedback
- File / reference: `testing/testing.py` (TODO: Add user feedback)
- Description: Add routes or logging to collect user feedback on responses (usefulness/accuracy), store into a review dataset.
- Acceptance criteria:
  - Endpoint or UI hook to submit feedback; records stored in `experiences/feedback.csv`.
  - Feedback tied to `query_id` and model_id.
- Complexity: Low–Medium
- Est. human time: 1 day
- Agent-ease: Moderate
- Progress notes: No implementation present. Progress: 0%

TEST-2: Make `APIWrapper` compatible with OpenAI
- File / reference: `testing/testing.py` (TODO: Make the APIWrapper compatible with OpenAI)
- Description: Ensure the testing module uses `APIWrapper` for OpenAI calls and that returned objects map to the batch parser logic.
- Acceptance criteria:
  - `openai_middleware` created with an `openai` model works end-to-end with `create_batch_request` and `parse_response` formats.
  - Unit tests mock the OpenAI wrapper to confirm flow.
- Complexity: Low
- Est. human time: 4–8 hours
- Agent-ease: Easy
- Progress notes: `APIWrapper` appears to support OpenAI in code; glue needed. Progress: 20%

TEST-3: Prompt variable templating (location, weather, topics)
- File / reference: `testing/testing.py` (TODO: Implement locations, weather, and important topics into agroprompt)
- Description: Inject dynamic variables into `agroprompt` via templating (Jinja2 or simple string replacement) and validate safe handling.
- Acceptance criteria:
  - Templating implemented with safe escaping and defaults.
  - Example unit or integration test demonstrating variable substitution.
- Complexity: Low
- Est. human time: 4–8 hours
- Agent-ease: Easy
- Progress notes: TODO placeholder only. Progress: 0%

TEST-4: Adapt batch testing to use APIWrapper
- File / reference: `testing/testing.py` (TODO: adapt batch testing for the api wrapper)
- Description: Replace direct batch request creation with calls through `APIWrapper` to enable unified logging/metrics.
- Acceptance criteria:
  - `create_batch_request` or equivalent produces the same experience schema when using the `APIWrapper`.
  - Tests validate end-to-end call flow with mock wrappers.
- Complexity: Medium
- Est. human time: 1–2 days
- Agent-ease: Moderate
- Progress notes: Batch tooling exists but is OpenAI-centric. Progress: 0%

---

**Category: Notebooks / Training Experiments**

Aggregate progress: ~0–5%

NB-1: Verify LoRA addition in `unsloth` training flow
- File / reference: `testing/training.ipynb` (TODO: Double check LoRA implementation)
- Description: Review notebook cells implementing LoRA fine-tuning in Unsloth, validate parameter shapes, and run short smoke tests (GPU required).
- Acceptance criteria:
  - Notebook or script demonstrates successful LoRA integration on a tiny sample without OOM.
  - Documented parameters and fallback options for CPU-only environments.
- Complexity: High
- Est. human time: 1–2 days (with GPU access)
- Agent-ease: Hard (requires GPU and experimental validation)
- Progress notes: Notebook has TODOs; no tested code. Progress: 0%

NB-2: Fix scoring & pairwise preference calculations
- File / reference: `testing/training.ipynb` (TODO: Properly calculate score and pairwise preference)
- Description: Implement correct scoring logic and ensure pairwise comparisons are added to dataframe for downstream RLHF or ranking tasks.
- Acceptance criteria:
  - Unit-tested scoring functions with sample inputs and expected outputs.
  - Notebook demonstrates produced dataframe.
- Complexity: Medium
- Est. human time: 1–2 days
- Agent-ease: Moderate
- Progress notes: TODOs present. Progress: 0%

---

**Category: Docs & Maintenance (General)**

DOC-1: Developer guide & quickstart
- File / reference: `innerAI/README.md` and `README_TODOs.md`
- Description: Improve quickstart, add example `APIWrapper` calls, and show batch test minimal example.
- Acceptance criteria:
  - Short install + run steps added and validated locally.
  - Example snippets for APIWrapper usage and how to run a batch test.
- Complexity: Low
- Est. human time: 4 hours
- Agent-ease: Easy
- Progress notes: Base README exists. Progress: 50%

MAINT-1: Logging retention & rotation
- File / reference: `APIWrapper/api_wrapper_impl.py` and project config
- Description: Implement TTL/rotation for `logs/` and make retention configurable.
- Acceptance criteria:
  - Config parameter added (e.g., `LOG_RETENTION_DAYS` or rotation by size).
  - Rotation executed via simple script or on-write checks.
- Complexity: Low
- Est. human time: 1 day
- Agent-ease: Easy
- Progress notes: No implementation. Progress: 0%