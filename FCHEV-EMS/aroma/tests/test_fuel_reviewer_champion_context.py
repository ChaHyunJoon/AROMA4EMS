"""fuel reviewer 가 champion 비교와 iteration 추이를 실제로 받는다 + 레벨 점수는 꼬리 기준 (2026-09-17).

20260916_154729 iter_002: fuel reviewer 프롬프트에 champion 연비가 없고, prior_iterations_summary 가
{"trajectory": {}} 로 비어 있었다 (래퍼 dict 를 iteration 기록으로 잘못 순회). 그래서 x0.80 이 연비를
악화시켰다는 사실을 모른 채 "더 줄이자" 고 제안했다. 레벨 점수는 탐색 구간이 섞인 chunk 평균 기준이라
baseline 자신도 73.4 (< 75) 로 매 iteration soft_revise 가 강제됐다.

Run: python3 -m pytest tests/test_fuel_reviewer_champion_context.py
"""
import json
import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


CHAMPION_VIEW = {
    "champion_iteration": 1,
    "champion_fuel_g100km": 1021.606,
    "challenger_fuel_g100km": 1028.874,
    "last_decision": "rollback",
    "rejections": ["iter_002: challenger [w_soc_multiplier=0.8] 1028.874 g/100km (+7.3 ...)"],
    "rejected_directions": [{"iteration": 2, "moves": {"soc_weight_inbounds": "down"}}],
}


def _packet():
    return {
        "iteration": 2,
        "policy_quality": {"h2_level_score": 75.8, "h2eq_corr_mean_g100km": 1088.266,
                           "h2eq_corr_tail_mean_g100km": 1028.874, "h2_floor_g100km": 779.683,
                           "soc_end_minus_target_mean": -0.0612},
        "prior_iterations_summary": {
            "trajectory": {
                "iter_001": {"champion_decision": "initialize", "champion_fuel": 1021.606,
                             "challenger_fuel": 1021.606, "h2_level_score": 76.3,
                             "h2eq_corr_mean": 1062.331, "h2eq_corr_tail_mean": 1021.606,
                             "h2_mean": 1051.2, "mean_fcs_cost": 0.19},
            },
            "insights": [{"iteration": 1, "lesson": "x"}],
        },
        "h2_stats": {"note": "n"},
        "recent_episodes": [],
        "feedback": {"preference": "p"},
        "reward_source": "def get_reward(self):\n    return 0.0\n",
        "champion": CHAMPION_VIEW,
    }


def _review_packet_json(prompt):
    return json.loads(prompt[prompt.index("REVIEW_PACKET:") + len("REVIEW_PACKET:"):])


# ── 레벨 점수: 꼬리 기준 ─────────────────────────────────────────────────────

def test_h2_quality_scores_level_uses_the_given_basis():
    from feedback_parser import h2_quality_scores
    # chunk 평균은 탐색 구간 때문에 높고 꼬리는 수렴 — 레벨은 꼬리 기준이어야 한다
    series = [2000.0] * 10 + [1000.0] * 90
    r = h2_quality_scores(series, floor_g100km=800.0, level_mean=1000.0)
    assert r["h2_level_score"] == pytest.approx(80.0)
    assert r["h2_mean"] == pytest.approx(1100.0)          # chunk 평균은 그대로 보고


def test_h2_quality_scores_level_defaults_to_series_mean():
    from feedback_parser import h2_quality_scores
    r = h2_quality_scores([1000.0, 1000.0], floor_g100km=800.0)
    assert r["h2_level_score"] == pytest.approx(80.0)


def test_policy_quality_level_is_tail_based(tmp_path, monkeypatch):
    import feedback_parser as fp
    import main_ldri_refine as mlr

    eps = []
    for i in range(100):
        fuel = 2000.0 if i < 50 else 1000.0
        eps.append(SimpleNamespace(
            episode=i, eval_h2_100km=None, h2_100km=fuel, eval_h2eq_corr_100km=None,
            eval_paper_fuel=dict(equivalent_g_per_km=fuel/100, rollout_soc0=.6,
                                 fuel_metric_basis=fp.DETERMINISTIC_FUEL_BASIS),
            h2eq_corr_100km=fuel, eval_in_bounds_rate=None, in_bounds_rate=100.0,
            eval_objective_100km=None, objective_100km=1.0, eval_soc_min=None, soc_min=0.5,
            eval_soc_max=None, soc_max=0.7, eval_r=None, ep_cumulative_r=-1.0,
            fce_eff_mean=0.5, fc_on_pct=50.0, soc_end=0.6, mean_fcs_cost=0.1,
            mean_batt_cost=0.1, travel_km=48.0))
    monkeypatch.setattr(fp, "parse_train_log", lambda path: eps)
    import env_physics_facts
    monkeypatch.setattr(env_physics_facts, "cycle_h2_floor_g_per_100km", lambda s: 800.0)
    pq = mlr._compute_policy_quality_score(
        str(tmp_path / "log"), SimpleNamespace(scenario_name="X", soc0=0.6, soc_target=0.6))
    assert pq["h2eq_corr_tail_mean_g100km"] == pytest.approx(1000.0)
    assert pq["h2_level_score"] == pytest.approx(80.0)
    assert pq["h2_level_basis"] == "tail10"
