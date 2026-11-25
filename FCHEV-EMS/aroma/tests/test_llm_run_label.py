"""run 폴더명·run_config 의 LLM 라벨은 실제 호출 모델이어야 한다 (2026-10-12).

역할별 맵(llm_presets.AGENT_MODELS)이 llm_model 을 덮어쓰는데 폴더명·run_config 에는
llm_model(gpt-5.4)만 찍혀, gpt-5.2 + gpt-5-mini 로 돈 run 이 "gpt-5.4" 로 읽혔다.

Run: python3 -m pytest tests/test_llm_run_label.py
"""
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main_ldri_refine as mlr
from llm_presets import AGENT_MODELS, get_agent_model, get_agent_preset


def test_run_tag_names_requested_models():
    args = SimpleNamespace(llm_provider="openai", llm_model="gpt-5.4")
    assert mlr._llm_run_tag(args) == "openai_gpt-5p2+gpt-5-mini"
    args = SimpleNamespace(llm_provider="anthropic", llm_model="claude-sonnet-4-6")
    assert mlr._llm_run_tag(args) == "anthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001"


def test_role_models_match_call_path():
    args = SimpleNamespace(llm_provider="openai", llm_model="gpt-5.4")
    recorded = mlr._llm_role_models(args)
    for role in AGENT_MODELS["openai"]:
        assert recorded[role] == get_agent_model("openai", role, args.llm_model)


def test_unlisted_provider_falls_back_to_llm_model():
    args = SimpleNamespace(llm_provider="other", llm_model="org/some-model")
    assert mlr._llm_role_models(args) == {"default": "org/some-model"}
    assert mlr._llm_run_tag(args) == "other_some-model"


def test_gpt_preset_default_is_a_model_the_role_map_uses():
    assert get_agent_preset("gpt").model in AGENT_MODELS["openai"].values()
