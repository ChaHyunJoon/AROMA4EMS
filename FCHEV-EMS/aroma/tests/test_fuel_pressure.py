"""연비 압력 (2026-09-18, 사용자 결정).

20260917_120329 에서 연비 압력이 약해진 지점:
  * fuel reviewer 합격선이 절대 점수(h2_level_score >= 75) 라 iter_002 가 pass → 바꿀 근거가 없는데도
    orchestrator 가 must_change 를 채우느라 h2 배수를 1.12 -> 1.11 로 **낮추라**고 지시했다.
  * 같은 reward 를 다시 학습한 iter_005 와 champion(iter_002) 의 학습 꼬리 연비가 2.9% 벌어졌다.

사용자 결정: 합격은 champion 대비 **조금이라도 좋으면** 통과(여유 없음), 보폭 강제는 하지 않는다,
연비가 병목일 때 h2 가중치 인하만 막는다.

Run: python3 -m pytest tests/test_fuel_pressure.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


_TAIL = "h2eq_corr_tail_mean_g100km"


def _packet(tail_fuel, champion_fuel=1018.812):
    return {
        "iteration": 3,
        "policy_quality": {"h2_level_score": 76.5, "h2_level_basis": "tail10",
                           _TAIL: tail_fuel, "h2eq_corr_mean_g100km": 1050.0,
                           "h2_floor_g100km": 779.683},
        "prior_iterations_summary": {"trajectory": {}, "insights": []},
        "h2_stats": {"note": "n"},
        "recent_episodes": [],
        "feedback": {"preference": "p"},
        "reward_source": "def get_reward(self):\n    return 0.0\n",
        "champion": {"champion_iteration": 2, "champion_fuel_g100km": champion_fuel,
                     "challenger_fuel_g100km": tail_fuel, "last_decision": "replace",
                     "rejections": [], "rejected_directions": []},
    }


# ── 1. 합격 기준: champion 보다 좋으면 통과, 아니면 soft_revise ────────────────


# ── 2. 연비가 병목일 때 h2 가중치 인하 금지 ──────────────────────────────────

_BASE = """def get_reward(self):
    soc = float(self.SOC)
    soc_low, soc_high = self.soc_bounds
    soc_err = (soc - self.SOC_target) ** 2
    w_soc = np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10, self.w_soc * 1.0)
    soc_cost = w_soc * soc_err
    h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal
    h2_cost = float(self.w_h2) * {h2} * h2_fcs
    fcs_soh_cost = self.w_fc * float(self.dSOH_FCS)
    batt_soh_cost = self.w_batt * float(self.dSOH_batt)
    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost
    return float(-objective_cost)
"""
CURRENT = _BASE.format(h2="1.12")
CUT = _BASE.format(h2="1.11")          # iter_002 orchestrator 가 실제로 지시한 변경
RAISE = _BASE.format(h2="1.30")


def _champ(challenger_fuel, champion_fuel=1018.812, rejected=()):
    return {"champion_fuel_g100km": champion_fuel, "challenger_fuel_g100km": challenger_fuel,
            "challenger_beat_champion": challenger_fuel < champion_fuel,
            "rejected_directions": list(rejected)}


_FUEL_KEEP = {"proposals": [{"target": "w_h2", "direction": "keep", "reason": "r"}]}
_FUEL_CUT = {"proposals": [{"target": "w_h2 effective multiplier", "direction": "decrease_small",
                            "reason": "overpriced"}]}


# ── 3. LR 자동 조정 기본값 off ───────────────────────────────────────────────

def test_auto_lr_default_is_off():
    from arguments_ldri import get_ldri_args
    old = sys.argv
    try:
        sys.argv = ["x"]
        args = get_ldri_args()
    finally:
        sys.argv = old
    assert args.auto_lr_on_reward_patch is False


def test_auto_lr_can_still_be_switched_on():
    from arguments_ldri import get_ldri_args
    old = sys.argv
    try:
        sys.argv = ["x", "--auto_lr_on_reward_patch", "true"]
        args = get_ldri_args()
    finally:
        sys.argv = old
    assert args.auto_lr_on_reward_patch is True


# ── 4. 교체(replace) 직후: champion 이 자기 자신이라 "못 이겼다" 로 읽히면 안 된다 ──

def _summary(decisions):
    """champion_trajectory 를 만든다: [(iteration, decision, challenger_fuel, champion_fuel), ...]"""
    return {
        "champion": {"iteration": decisions[-1][0], "fuel_g100km": decisions[-1][3],
                     "reward_source": CURRENT},
        "champion_trajectory": [
            {"iteration": it, "decision": d, "challenger_fuel_g100km": cf, "champion_fuel_g100km": mf}
            for it, d, cf, mf in decisions],
    }
