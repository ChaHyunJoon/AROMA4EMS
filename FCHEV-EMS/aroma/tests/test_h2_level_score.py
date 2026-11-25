"""h2_score 레벨 인지화: 물리 하한(사이클 수요 x 최적 sfc) 정규화 + 일관성 블렌드.

원칙(§13/§14): DP/baseline 해의 성능은 사용 금지. 물리 하한은 환경(차량 모델 + 속도
프로파일)에서 런타임 유도되는 상수이므로 전제를 지킨다.
"""
import glob
from pathlib import Path
import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CYCLE = "Standard_WLTC_WVUINTER"


# ── env_physics_facts: 사이클 수요/물리 하한 ─────────────────────────────────

def test_cycle_demand_facts_positive_and_consistent():
    from env_physics_facts import cycle_demand_facts
    f = cycle_demand_facts(CYCLE)
    assert f["distance_km"] > 40.0                      # WLTC+WVUINTER ~ 48 km
    assert 0.0 < f["net_elec_demand_kwh"] <= f["positive_elec_demand_kwh"]
    # 캐시/재계산 안정성
    f2 = cycle_demand_facts(CYCLE)
    assert f2["net_elec_demand_kwh"] == f["net_elec_demand_kwh"]


def test_cycle_h2_floor_bounds_and_linear_in_sfc():
    from env_physics_facts import cycle_h2_floor_g_per_100km
    floor = cycle_h2_floor_g_per_100km(CYCLE)
    assert 200.0 < floor < 2000.0                       # 물리적으로 그럴듯한 범위
    f100 = cycle_h2_floor_g_per_100km(CYCLE, best_sfc_g_per_kwh=100.0)
    f200 = cycle_h2_floor_g_per_100km(CYCLE, best_sfc_g_per_kwh=200.0)
    assert abs(f200 - 2.0 * f100) < 1e-9                # sfc 에 선형


# ── feedback_parser: 점수 헬퍼 ───────────────────────────────────────────────

def test_h2_quality_scores_level_separates_uniform_policies():
    from feedback_parser import h2_quality_scores
    good = h2_quality_scores([100.0] * 50, floor_g100km=100.0)
    bad = h2_quality_scores([200.0] * 50, floor_g100km=100.0)
    # 기존 p10/mean 은 둘 다 100 을 줬다(한결같이 나쁜 정책의 눈멀음) — 레벨이 갈라야 한다
    assert good["h2_consistency_score"] == pytest.approx(100.0)
    assert bad["h2_consistency_score"] == pytest.approx(100.0)
    assert good["h2_level_score"] == pytest.approx(100.0)
    assert bad["h2_level_score"] == pytest.approx(50.0)
    assert good["h2_score"] > bad["h2_score"] + 20.0


def test_h2_quality_scores_without_floor_falls_back_to_consistency():
    from feedback_parser import h2_quality_scores
    r = h2_quality_scores([120.0, 100.0, 110.0, 90.0, 130.0], floor_g100km=None)
    assert r["h2_level_score"] is None
    # 기존 관례: sorted 후 index max(0, n//10 - 1) = 최솟값(p10) / mean
    assert r["h2_score"] == pytest.approx(r["h2_consistency_score"])
    assert r["h2_consistency_score"] == pytest.approx(100.0 * 90.0 / 110.0)


def test_h2_quality_scores_empty_series():
    from feedback_parser import h2_quality_scores
    r = h2_quality_scores([], floor_g100km=800.0)
    assert r["h2_score"] is None


# ── main_ldri_refine 통합: 실제 train_log 로 policy_quality ──────────────────

def _finished_logs():
    """Completed chunks only.

    The glob hits live ``ldri_runs/``, so an in-progress training run would
    otherwise be picked up as the fixture and its empty tail window collapses
    every score to 0.0 (a spurious failure that has nothing to do with the code
    under test). ``chunk finished`` is written once the chunk ends.
    """
    hits = sorted(glob.glob(os.path.join(
        os.path.dirname(__file__), "..", "..", "ldri_runs",
        "*", "iter_*", "train_log.log")))
    out = []
    for p in hits:
        try:
            if "chunk finished" in Path(p).read_text(errors="ignore"):
                out.append(p)
        except OSError:
            pass
    return out


_LOGS = _finished_logs()


@pytest.mark.skipif(not _LOGS, reason="no ldri_runs train_log fixture available")
def test_policy_quality_reports_level_fields():
    from main_ldri_refine import _compute_policy_quality_score
    args = SimpleNamespace(scenario_name=CYCLE, soc0=0.6, soc_target=0.6)
    pq = _compute_policy_quality_score(_LOGS[-1], args)
    assert pq["status"] == "ok"
    for key in ("h2_level_score", "h2_consistency_score", "h2_floor_g100km",
                "h2eq_corr_mean_g100km", "fce_eff_mean", "fc_on_pct_mean",
                "soc_end_minus_target_mean"):
        assert key in pq, key
    assert pq["h2_floor_g100km"] and pq["h2_floor_g100km"] > 0
    assert 0.0 <= pq["h2_score"] <= 100.0
    if pq["h2_level_score"] is not None:
        assert 0.0 < pq["h2_level_score"] <= 100.0
