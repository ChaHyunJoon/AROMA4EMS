"""§16 prompt + 순수 버그 수정 (2026-09-16).

§17~§19 에서 발견된 결함 중 §16 코드에도 그대로 있는 '측정/코드 정합성' 결함만 고정한다.
독트린·프롬프트 문구(바닥선, Pareto, 판단 계약, 방향 권한, TAC 참조 합격선)는 넣지 않는다.

  1. reviewer / mediator 응답 잘림 (max_tokens 2500 / 875 → fallback conf 0.1)     §19.1
  2. 롤백 후 리뷰 층이 '챌린저 지표 + 챔피언 코드' 를 받음 (귀속 오류)             §18.1-1
  3. diagnostic oob_rate 가 chunk 전체 any-OOB 에피소드 비율 (초반 탐색 포함)       §19.1
  4. TAC 에피소드 풀 = in_bounds>=98% 에피소드 = 초반 탐색 구간                     §19.1
  5. champion 연비 비교가 chunk 전체 평균 (미수렴 초반 포함, 평가는 ep499)          §17.3

Run: python3 -m pytest tests/test_s16_bugfixes.py
"""
import glob
import json
import os
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main_ldri_refine as mlr
from feedback_parser import EpisodeSummary, DETERMINISTIC_FUEL_BASIS

_RUNS = Path(__file__).resolve().parents[2] / "ldri_runs"


def _block(n, inb=100.0, soc_min=0.45, h2=1000.0):
    return "\n".join([
        f"epi {n}: travel 48.228km, SOC 0.6000, FCS-SOH 0.999900, Bat-SOH 0.999500",
        f"epi {n}: H2_100km {h2:.1f}g, H2eq_100km {h2:.1f}g (batt 0.0g), g/km 9.9, objective_100km 1000.00",
        f"epi {n}: SOC[min/mean/max]={soc_min:.3f}/0.600/0.700, in_bounds_rate={inb:.1f}%, len=3441",
        f"epi {n}: mean_cost soc 0.100, h2 1.400, fcs 0.120, batt 0.300, obj 1.920",
    ])


class _Chunk:
    def __init__(self, log_path):
        self.log_path = str(log_path)
        self.start_episode, self.end_episode = 0, 19
        self.episode_data_dir, self.model_dir = None, "/m"


def _pkt_args(**kw):
    base = dict(soc_low=0.4, soc_high=0.8, soc0=0.6, feedback_process_episodes=10, w_fc=4.275e6,
                lr_critic=3e-4, lr_critic_min=1e-4, lr_actor=1e-4, lr_actor_min=2e-5,
                lr_alpha=2e-4, lr_warmup_ratio=0.1)
    base.update(kw)
    return types.SimpleNamespace(**base)


_BUNDLE = {"PROCESS_FEEDBACK": "p", "TRAJECTORY_FEEDBACK": "t", "PREFERENCE_FEEDBACK": "f"}


# ── 1. reviewer / mediator max_tokens ────────────────────────────────────────


def _llm_args():
    return types.SimpleNamespace(llm_max_tokens=7000, llm_temperature=0.2, llm_timeout_sec=10)


# ── 2. 학습된 reward vs 편집 베이스 귀속 ─────────────────────────────────────


# ── 3. diagnostic oob_rate = 수렴 꼬리 ──────────────────────────────────────

def _diag_packet(**soc_stats):
    return {"soc_stats": soc_stats, "h2_stats": {}, "recent_episodes": [],
            "training_trend": {"trend_factor": 0.9, "best_episode_ratio": 0.9,
                               "tail_gap_ratio": 0.01},
            "policy_quality": {"mean_soc_swing": 0.26}}


# ── 4. TAC 에피소드 풀 = 수렴 꼬리 ──────────────────────────────────────────

def _ep(n, inb=100.0):
    e = EpisodeSummary(episode=n, order=n)
    e.in_bounds_rate = inb
    e.h2_100km = 1000.0
    return e


def _run_dir(prefix):
    hits = sorted(glob.glob(str(_RUNS / f"{prefix}*")))
    return Path(hits[0]) if hits else None


_R14 = _run_dir("20260914_140904")
BAD_INV_H2 = "def get_reward(self):\n    return float(self.h2_fcs)\n"


# ── 5. champion 연비 = 수렴 꼬리 ────────────────────────────────────────────

def test_policy_quality_reports_tail_fuel(tmp_path):
    log = tmp_path / "train_log.log"
    log.write_text("\n".join(_block(n, h2=1100.0 if n < 18 else 1000.0) for n in range(20)) + "\n",
                   encoding="utf-8")
    with log.open("a") as f:
        for n in range(20):
            h2 = 1100 if n < 18 else 1000
            row = dict(equivalent_g_per_km=h2/100, rollout_soc0=.6, fuel_metric_basis=DETERMINISTIC_FUEL_BASIS)
            f.write(f"epi {n} [eval]: paper_fuel {json.dumps(row)}\n")
    pq = mlr._compute_policy_quality_score(str(log), types.SimpleNamespace(soc0=0.6, soc_target=0.6))
    assert pq["h2eq_corr_tail_mean_g100km"] == pytest.approx(1000.0)   # last max(1, 20//10)=2
    assert pq["h2eq_corr_mean_g100km"] == pytest.approx(1090.0)


_R15 = _run_dir("20260915_074651")


@pytest.mark.skipif(_R15 is None, reason="20260915 run data not available")
def test_e2e_tail_fuel_reproduces_the_recorded_values():
    """같은 창 정의 — §17 이후 run 이 기록한 tail 연비를 그대로 재현해야 한다."""
    checked = 0
    for pq_path in sorted(_R15.glob("iter_00*/policy_quality.json")):
        stored = json.load(open(pq_path))
        if stored.get("fuel_metric_basis") != DETERMINISTIC_FUEL_BASIS:
            continue
        rec = stored.get("h2eq_corr_tail_mean_g100km")
        log = pq_path.parent / "train_log.log"
        if rec is None or not log.exists():
            continue
        args = types.SimpleNamespace(**json.load(open(_R15 / "run_config.json")))
        args.scenario_name = None
        pq = mlr._compute_policy_quality_score(str(log), args)
        assert pq["h2eq_corr_tail_mean_g100km"] == pytest.approx(rec, abs=1e-3), pq_path
        checked += 1
    if not checked:
        pytest.skip("no deterministic corrected fuel records in this legacy run")
