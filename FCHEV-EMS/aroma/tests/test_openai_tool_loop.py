import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import llm_client


def _fake_http(scripted, recorded):
    """Return a _http_post_json replacement that records bodies and pops
    scripted responses in order."""
    def fake(url, headers, body, timeout_sec, **kwargs):
        recorded.append(body)
        return scripted.pop(0)
    return fake


def _req(prompt="review this", max_tokens=2500):
    return llm_client.LLMRequest(
        provider="openai",
        model="gpt-4.1-mini",
        prompt=prompt,
        api_key="k",
        temperature=0.2,
        max_tokens=max_tokens,
    )


_PARSE_LOG_TOOL = {
    "name": "parse_training_log",
    "description": "parse the log",
    "input_schema": {
        "type": "object",
        "properties": {"n_episodes": {"type": "integer"}},
    },
}


def test_openai_tool_loop_executes_threads_and_accumulates(monkeypatch):
    responses = [
        {  # round 1: model requests a tool call
            "id": "resp_1", "model": "gpt-4.1-mini", "status": "completed",
            "output": [
                {"type": "function_call", "id": "fc_1", "call_id": "call_abc",
                 "name": "parse_training_log", "arguments": "{\"n_episodes\": 5}"}
            ],
            "usage": {"input_tokens": 100, "output_tokens": 20},
        },
        {  # round 2: model returns the final JSON answer
            "id": "resp_2", "model": "gpt-4.1-mini", "status": "completed",
            "output": [
                {"type": "message", "role": "assistant",
                 "content": [{"type": "output_text", "text": "{\"decision\": \"approve\"}"}]}
            ],
            "usage": {"input_tokens": 150, "output_tokens": 40},
        },
    ]
    bodies = []
    monkeypatch.setattr(llm_client, "_http_post_json", _fake_http(responses, bodies))

    calls = []

    def tool_executor(name, inp):
        calls.append((name, inp))
        return "{\"episodes\": 5}"

    completion = llm_client._openai_complete_with_tools(
        _req(), [_PARSE_LOG_TOOL], tool_executor, max_tool_rounds=8
    )

    # tool executed once, with arguments parsed from JSON string into a dict
    assert calls == [("parse_training_log", {"n_episodes": 5})]

    # final assistant text is returned
    assert completion.text == "{\"decision\": \"approve\"}"

    # usage accumulated across BOTH rounds
    assert completion.usage["input_tokens"] == 250
    assert completion.usage["output_tokens"] == 60
    assert completion.usage["total_tokens"] == 310

    # two HTTP round-trips
    assert len(bodies) == 2

    # tools were converted to the OpenAI Responses function format
    sent_tools = bodies[0]["tools"]
    assert sent_tools[0]["type"] == "function"
    assert sent_tools[0]["name"] == "parse_training_log"
    assert sent_tools[0]["parameters"]["properties"]["n_episodes"]["type"] == "integer"

    # round 2 threaded the tool result back as a function_call_output
    outputs = [it for it in bodies[1]["input"] if it.get("type") == "function_call_output"]
    assert len(outputs) == 1
    assert outputs[0]["call_id"] == "call_abc"
    assert outputs[0]["output"] == "{\"episodes\": 5}"


def test_openai_tool_loop_returns_immediately_without_tool_calls(monkeypatch):
    responses = [
        {  # model answers directly, no tool call
            "id": "resp_1", "model": "gpt-4.1-mini", "status": "completed",
            "output": [
                {"type": "message", "role": "assistant",
                 "content": [{"type": "output_text", "text": "{\"decision\": \"reject\"}"}]}
            ],
            "usage": {"input_tokens": 80, "output_tokens": 10},
        },
    ]
    bodies = []
    monkeypatch.setattr(llm_client, "_http_post_json", _fake_http(responses, bodies))

    def tool_executor(name, inp):  # should never be called
        raise AssertionError("tool_executor must not run when model makes no tool call")

    completion = llm_client._openai_complete_with_tools(
        _req(), [_PARSE_LOG_TOOL], tool_executor, max_tool_rounds=8
    )

    assert completion.text == "{\"decision\": \"reject\"}"
    assert len(bodies) == 1  # single round, no second POST


def test_client_complete_with_tools_routes_openai_to_tool_loop(monkeypatch):
    responses = [
        {
            "id": "resp_1", "model": "gpt-4.1-mini", "status": "completed",
            "output": [
                {"type": "message", "role": "assistant",
                 "content": [{"type": "output_text", "text": "ok"}]}
            ],
            "usage": {"input_tokens": 5, "output_tokens": 2},
        },
    ]
    bodies = []
    monkeypatch.setattr(llm_client, "_http_post_json", _fake_http(responses, bodies))

    client = llm_client.LLMClient(provider="openai", model="gpt-4.1-mini", api_key="k")
    completion = client.complete_with_tools(
        prompt="hi",
        tools=[_PARSE_LOG_TOOL],
        tool_executor=lambda n, i: "{}",
    )

    assert completion.text == "ok"
    # went through the Responses tool path, so tools were sent in function format
    assert bodies[0]["tools"][0]["type"] == "function"
