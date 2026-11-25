"""resume 시 LLM 키 환경변수 이름도 복원한다 (2026-09-17).

`--resume_run_root` 만 주면 파싱 단계에서 llm_provider 가 기본값 openai 로 잡히고
llm_api_key_env 도 그에 맞춰 OPENAI_API_KEY 로 정해진다. run_config 복원이 provider 는
anthropic 으로 되돌렸지만 llm_api_key_env 는 복원 키가 아니어서 OPENAI_API_KEY 로 남았고,
OpenAI 키가 Anthropic 에 전송돼 HTTP 401 (20260916_154729 재제안, 2회).

Run: python3 -m pytest tests/test_resume_llm_key_env.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main_ldri_refine as mlr
from arguments_ldri import get_ldri_args
from llm_client import get_api_key

_SAVED = {"llm_provider": "anthropic", "llm_model": "claude-sonnet-4-6",
          "llm_api_key_env": "ANTHROPIC_API_KEY"}


def _parse(argv):
    old = sys.argv
    try:
        sys.argv = ["x"] + argv
        return get_ldri_args()
    finally:
        sys.argv = old


def test_resume_restores_the_key_env_with_the_provider(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-key")
    argv = ["--resume_run_root", "r"]
    args = _parse(argv)
    assert args.llm_api_key_env == "OPENAI_API_KEY"          # 파싱 직후 상태 (재현 조건)
    mlr._apply_resume_run_config(args, _SAVED, explicit_keys=mlr._explicit_cli_keys(["x"] + argv))
    assert args.llm_provider == "anthropic"
    assert args.llm_api_key_env == "ANTHROPIC_API_KEY"
    assert get_api_key(args.llm_provider, args.llm_api_key, args.llm_api_key_env) == "anthropic-key"


def test_explicit_key_env_still_wins(monkeypatch):
    argv = ["--resume_run_root", "r", "--llm_api_key_env", "MY_KEY"]
    args = _parse(argv)
    mlr._apply_resume_run_config(args, _SAVED, explicit_keys=mlr._explicit_cli_keys(["x"] + argv))
    assert args.llm_api_key_env == "MY_KEY"
