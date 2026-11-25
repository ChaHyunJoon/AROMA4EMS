"""Confound 재발 방지 감사 추적 — 설계 스펙 A2 (2026-09-02).

260901 run에서 --ramp_limit_kw/--per가 launch CLI에서 누락된 채 run 태그에만
"dR19_per"가 들어갔고, run_config.json이 화이트리스트 방식이라 미기록 → 절대액션
confound를 데이터 역산으로만 발견 가능했다. 재발 방지:
  1) run_config.json에 전체 vars(args) 기록 (화이트리스트 키 호환 유지)
  2) 학습 로그 헤더에 action mode / PER 한 줄 출력

Run: python3 -m pytest tests/test_run_config_audit.py
"""
import inspect
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main_ldri_refine as mlr


# ── run_config 전체 기록 ─────────────────────────────────────────────────────

def _default_args(monkeypatch):
    from arguments_ldri import get_ldri_args
    monkeypatch.setattr(sys, "argv", ["prog"])
    return get_ldri_args()


def test_build_run_config_records_action_and_policy_args(monkeypatch):
    args = _default_args(monkeypatch)
    cfg = mlr._build_run_config(args)
    # 스펙 A2 최소 요구: 액션 파라미터라이제이션 관련 키가 반드시 기록된다
    for key in ("ramp_limit_kw", "per", "policy", "target_entropy_scale"):
        assert key in cfg, f"{key} missing from run_config"
    # 기존 화이트리스트 키 호환 유지
    for key in ("w_soc", "w_h2", "scenario_name", "ldri_iterations", "created_at"):
        assert key in cfg, f"whitelist key {key} missing from run_config"


def test_build_run_config_serializes_non_json_values(monkeypatch):
    args = _default_args(monkeypatch)
    args.strange_object = object()
    cfg = mlr._build_run_config(args)
    assert isinstance(cfg["strange_object"], str)
    import json
    json.dumps(cfg)  # 전체가 JSON 직렬화 가능해야 run_config.json에 기록된다


# ── 학습 로그 action mode 헤더 ───────────────────────────────────────────────

def test_action_mode_line_delta_with_per():
    import runner_ldri
    args = types.SimpleNamespace(ramp_limit_kw=19.0, per=True)
    assert runner_ldri._action_mode_line(args) == "action mode: delta (R=19.0 kW/s), PER: on"


def test_action_mode_line_absolute_without_per():
    import runner_ldri
    args = types.SimpleNamespace(ramp_limit_kw=0.0, per=False)
    assert runner_ldri._action_mode_line(args) == "action mode: absolute, PER: off"


def test_train_chunk_header_logs_action_mode():
    import runner_ldri
    src = inspect.getsource(runner_ldri.RunnerLDRI.train_chunk)
    assert "_action_mode_line" in src
