"""multi_agent_review.py deadband 독트린 정렬 — 설계 스펙 A1 (2026-09-02).

reward_generation_prompt.md 확정 기조(모든 단계 db=0 기본, refinement 예외 db <= 0.02
+ 명시적 연비 증거)와 refinement 프롬프트를 일치시킨다. 260903 seed1 v2 run에서
iter_001이 리뷰 프롬프트의 db∈[0.02,0.10] 광고를 따라 db=0.08을 도입, 전 iteration
고착 → WVUSUB_HWFET iter5 SOC 폭주의 구조적 원인.

Run: python3 -m pytest tests/test_review_prompt_deadband_alignment.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


_BANNED_EVERYWHERE = (
    "0.03–0.08",
    "0.03-0.08",
    "[0.02, 0.10]",
    "any width",
    "never above 0.10",
    "db <= 0.10",
    "db ≤ 0.10",
    "add_deadband",
)


def _soc_packet():
    return {
        "iteration": 2,
        "soc_bounds": {"low": 0.4, "high": 0.8},
        "soc_stats": {"out_of_bounds_episodes": 1, "total_episodes": 50},
        "recent_episodes": [
            {"episode": 499, "soc_min": 0.52, "soc_max": 0.66, "in_bounds_rate_pct": 100.0}
        ],
        "reward_source": "def get_reward(self):\n    return 0.0\n",
    }


def _batt_packet():
    return {
        "iteration": 2,
        "h2_stats": {},
        "reward_source": "def get_reward(self):\n    return 0.0\n",
        "recent_episodes": [
            {"episode": 499, "mean_batt_cost": 0.25, "mean_h2_cost": 1.48, "h2_100km": 1000.0}
        ],
        "diagnostic_result": {"reviewer_hints": {"battery_degradation": "h"}},
    }


def _hacking_packet():
    return {
        "iteration": 2,
        "reward_source": "def get_reward(self):\n    return 0.0\n",
    }


# ── deadband 광고 문구 0건 (수락 기준 1) ─────────────────────────────────────


# ── db=0 기본 + db <= 0.02 예외 독트린 존재 ──────────────────────────────────


# ── 파서 폴백 (_synthesize_must_change) 도 독트린 준수 ───────────────────────


# ── 소스 전체 sweep — 수락 기준 1: deadband 광고 문구 0건 ────────────────────

def test_module_source_has_no_deadband_advertising():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(here, "multi_agent_review.py"), encoding="utf-8") as f:
        src = f.read()
    for banned in _BANNED_EVERYWHERE + ("db <= 0.10", "beyond 0.10", "toward db <= 0.1"):
        assert banned not in src, f"{banned!r} still present in multi_agent_review.py source"


# ── swing 독트린은 유지 (스펙 A1 주의사항) ───────────────────────────────────
