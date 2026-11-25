"""TAC 합격선 기본값 0.12 (2026-09-16, 사용자 결정).

20260916_074239 run iter_002 측정: seed 시작으로 수렴한 꼬리(연비 sd 0.21%, in_bounds 전부 100%)
에서는 이 chunk 를 학습시킨 reward 자신이 tau=0.162, baseline SAC reward 도 0.162 로 구 기본값
0.20 을 넘지 못했다 (같은 reward 를 전체 chunk 창으로 재면 0.661). 즉 0.20 은 수렴한 정책의
tail 창에서 만족 불가능한 문턱이었다. 기본값을 0.12 로 낮춘다.

기본값이 세 곳에 흩어져 있어(인자 정의 / 게이트 _DEFAULTS / 호출부 폴백) 전부 잠근다.

Run: python3 -m pytest tests/test_gate_threshold_default.py
"""
import inspect
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main_ldri_refine as mlr

EXPECTED = 0.12


def test_cli_default_is_0_12(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog"])
    from arguments_ldri import get_ldri_args
    assert get_ldri_args().aligned_min_tac == EXPECTED


def test_the_trained_reward_of_the_seeded_chunk_would_now_pass():
    """실측 근거: 학습 reward 자신의 tau 0.162 / baseline 0.162 가 기본값 위에 있다."""
    assert 0.162 > EXPECTED


# ── resume 에서도 아무것도 명시하지 않아도 새 기본값이 쓰인다 ────────────────
# `_apply_resume_run_config` 는 저장값이 다르면 무조건 덮어썼다 — run_config.json 에 박힌
# 구 문턱 0.2 가 되살아나고, `--aligned_min_tac 0.12` 를 CLI 에 줘도 그것마저 덮였다.

def _saved_config():
    return {"aligned_min_tac": 0.2, "w_soc": 200.0, "seed": 61}


def _resume_args():
    return types.SimpleNamespace(aligned_min_tac=EXPECTED, w_soc=100.0, seed=1)


def test_gate_threshold_is_not_pinned_by_resume():
    args = _resume_args()
    mlr._apply_resume_run_config(args, _saved_config())
    assert args.aligned_min_tac == EXPECTED      # 새 기본값이 살아남는다
    assert args.w_soc == 200.0                   # 학습 조건은 그대로 복원된다
    assert args.seed == 61


def test_aligned_min_tac_is_not_a_resume_restore_key():
    assert "aligned_min_tac" not in mlr.RESUME_RESTORE_KEYS


def test_explicitly_given_cli_values_beat_the_saved_config():
    """resume 중에도 사용자가 CLI 로 준 값이 우선한다 (구현 전에는 조용히 덮였다)."""
    args = _resume_args()
    mlr._apply_resume_run_config(args, _saved_config(), explicit_keys={"w_soc"})
    assert args.w_soc == 100.0                   # 명시값 유지
    assert args.seed == 61                       # 명시하지 않은 키는 복원


def test_main_passes_the_explicitly_given_cli_keys():
    assert "explicit_keys=" in inspect.getsource(mlr.main)
