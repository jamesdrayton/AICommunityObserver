# AICommunityObserver

AICommunityObserver is a middleware observability layer for all GenAI applications. It sits between your application and model calls, automatically collecting and evaluating inputs without changing how you generate or store prompt and response history. Just include the AICommunityObserver in your application and access the Observer or Observable objects to make your API calls, and centralize all of your AI operations to allow unified monitoring, alerting, security, and accessibility management for all GenAI assets within your application.

Code of Conduct for the Community Contributors - https://acrobat.adobe.com/link/track?uri=urn:aaid:scds:US:1cb574fd-0e7e-440e-baf9-2f835c3ab602

## Structure
1. Metrics module. Contains metrics.py with metrics registry and other files running metrics.
metrics/

2. Observer module. Contains code for generalized API wrappers or loggers to pass into metrics.
observer/

3. (optional) Testing module. Contains example applications to run for testing or to demonstrate use cases.
testing/

4. TODO: Custom dashboard for displaying logged metrics. More relevant for unique tests.
dashboard/

5. TODO: Benchmarks module. Contains benchmarks organized in industry or domain-specific directories
benchmarks/
    reasoning/
    coding/
    corruption/
        mining/
        agriculture/

## How to Use

run 'fastapi dev' in the main branch

run 'python -m main' in the Flask branch

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