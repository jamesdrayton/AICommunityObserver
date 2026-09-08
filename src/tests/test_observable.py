from types import SimpleNamespace

import pytest

from AICommunityObserver.observer import observable as observable_module
from AICommunityObserver.observer.observable import Observable


class FakeModels:
    def __init__(self):
        self.generate_calls = []
        self.embed_calls = []
        self.generate_response = SimpleNamespace(
            text="  Generated response  ",
            usage_metadata=SimpleNamespace(total_token_count=12),
        )

    def generate_content(self, **kwargs):
        self.generate_calls.append(kwargs)
        return self.generate_response

    def embed_content(self, **kwargs):
        self.embed_calls.append(kwargs)
        return SimpleNamespace(
            embeddings=[SimpleNamespace(values=[0.1, 0.2, 0.3])]
        )


class FakeClient:
    last_instance = None

    def __init__(self, api_key=None, **kwargs):
        self.api_key = api_key
        self.client_options = kwargs
        self.models = FakeModels()
        FakeClient.last_instance = self


@pytest.fixture
def fake_client(monkeypatch):
    monkeypatch.setattr(observable_module.genai, "Client", FakeClient)
    return FakeClient


@pytest.fixture
def observable(fake_client):
    return Observable(
        provider="google",
        model_name="gemini-test",
        api_key="test-key",
        testing_freq=0,
    )


@pytest.fixture
def disable_metrics(monkeypatch):
    monkeypatch.setattr(
        observable_module,
        "evaluate_metrics",
        lambda **kwargs: None,
    )


def test_init_requires_api_key():
    with pytest.raises(ValueError, match="API key"):
        Observable(provider="google", model_name="test")


def test_init_requires_api_token_configuration():
    with pytest.raises(ValueError, match="api_token"):
        Observable(
            provider="google",
            access_type="api_token",
            token_url="https://example.test/token",
        )


def test_init_normalizes_provider_and_model(fake_client):
    model = Observable(
        provider="GOOGLE",
        model_name="Gemini-Test",
        api_key="test-key",
    )

    assert model.provider == "google"
    assert model.model_name == "gemini-test"
    assert model.api_key == "test-key"


def test_init_passes_client_provider_options(monkeypatch):
    captured = {}

    def fake_client(api_key=None, **kwargs):
        captured["api_key"] = api_key
        captured["kwargs"] = kwargs
        client = FakeClient(api_key, **kwargs)
        return client

    monkeypatch.setattr(observable_module.genai, "Client", fake_client)

    Observable(
        provider="google",
        model_name="test",
        api_key="test-key",
        provider_options={
            "client": {"project": "demo-project"},
            "generate": {},
        },
    )

    assert captured == {
        "api_key": "test-key",
        "kwargs": {"project": "demo-project"},
    }


def test_generate_returns_stripped_text_and_context(
    observable,
    disable_metrics,
):
    response, context = observable.generate(
        prompt="Hello",
        return_context=True,
        do_tests=False,
    )

    assert response == "Generated response"
    assert context.response == "Generated response"
    assert context.prompt == "Hello"
    assert context.tokens_used == 12
    assert context.model == "gemini-test"


def test_generate_passes_prompt_and_provider_options(
    fake_client,
    disable_metrics,
):
    model = Observable(
        provider="google",
        model_name="gemini-test",
        api_key="test-key",
        testing_freq=0,
        provider_options={
            "client": {},
            "generate": {
                "system_instruction": "Be concise",
                "temperature": 0.2,
                "max_output_tokens": 64,
            },
        },
    )

    model.generate("Test prompt", do_tests=False)

    call = fake_client.last_instance.models.generate_calls[0]

    assert call["model"] == "gemini-test"
    assert call["contents"] == "Test prompt"
    assert call["config"].system_instruction == "Be concise"
    assert call["config"].temperature == 0.2
    assert call["config"].max_output_tokens is not None


def test_generate_records_metadata(
    observable,
    monkeypatch,
):
    captured = {}

    monkeypatch.setattr(
        observable_module,
        "evaluate_metrics",
        lambda **kwargs: captured.update(kwargs),
    )

    observable.generate(
        prompt="Hello",
        id="request-123",
        do_tests=False,
        metadata={"maintain_privacy": True},
    )

    assert captured["id"] == "request-123"
    assert captured["metadata"]["tokens_used"] == 12
    assert captured["metadata"]["maintain_privacy"] is True
    assert captured["context"].response == "Generated response"


def test_generate_wraps_provider_errors(observable, disable_metrics):
    def failing_generate_content(**kwargs):
        raise RuntimeError("provider unavailable")

    observable.model.models.generate_content = failing_generate_content

    with pytest.raises(Exception, match="Failure to reach model"):
        observable.generate("Hello", do_tests=False)


def test_embed_returns_vector(observable):
    result = observable.embed(
        text="knowledge text",
        task_type="RETRIEVAL_DOCUMENT",
        embedding_model="gemini-embedding-001",
    )

    assert result == [0.1, 0.2, 0.3]

    call = observable.model.models.embed_calls[0]
    assert call["model"] == "gemini-embedding-001"
    assert call["contents"] == "knowledge text"
    assert call["config"].task_type == "RETRIEVAL_DOCUMENT"


def test_embed_wraps_provider_errors(observable):
    def failing_embed_content(**kwargs):
        raise RuntimeError("embedding unavailable")

    observable.model.models.embed_content = failing_embed_content

    with pytest.raises(Exception, match="Failure to embed"):
        observable.embed("text")


def test_generate_accepts_list_prompt(observable, disable_metrics):
    response = observable.generate(
        prompt=["Earlier message", "Current message"],
        do_tests=False,
    )

    assert response == "Generated response"


# Future test stubs:
#
# def test_generate_uses_per_call_provider_options():
#     """Verify per-call provider_options override instance defaults."""
#     pass
#
# def test_generate_does_not_mutate_instance_provider_options():
#     """Ensure generate() does not modify the configured options dictionary."""
#     pass
#
# def test_generate_respects_configured_max_output_tokens():
#     """Verify max_output_tokens is preserved exactly."""
#     pass
#
# def test_generate_handles_empty_response():
#     """Verify provider responses with empty text are handled safely."""
#     pass
#
# def test_generate_handles_missing_usage_metadata():
#     """Verify missing token usage is represented consistently."""
#     pass
#
# def test_embed_accepts_batch_input():
#     """Verify embedding behavior for a list of strings."""
#     pass
#
# def test_embed_handles_empty_text():
#     """Verify empty embedding input behavior."""
#     pass
#
# def test_unknown_provider_is_rejected():
#     """Verify unsupported providers raise ValueError."""
#     pass