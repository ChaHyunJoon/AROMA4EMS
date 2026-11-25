"""환경(FCHEV_SOH)에서 물리 사실을 런타임에 유도해 프롬프트로 주입한다.

왜 유도하는가
-------------
프롬프트에 "efficient band = 40-80% P_max" 같은 **상수를 손으로 적어 넣으면**
(1) 그 값이 이 차량의 효율맵과 맞지 않을 때 조용히 틀린 지침이 되고 — 실제로 그랬다 —
(2) 차량/맵을 바꾸면 같이 안 바뀌며
(3) 프레임워크에 사전 지식을 주입하는 셈이 되어 "사전 지식 없이 reward 를 찾는다"는
    전제를 깬다.

여기서는 아무 상수도 적지 않고 `FCHEV_SOH` 모델 자체를 **측정**한다:
- 효율 밴드: `fce_eff` 보간 곡선을 훑어 최적점과 "최적 대비 x% 이내" 구간을 찾는다.
- 열화 단가: `run_FC_SOH` 를 원인별로 격리 호출해 dSOH 를 직접 재고 w_fc 를 곱한다.

따라서 이 모듈이 내놓는 숫자는 전부 "지금 로드된 환경이 실제로 그렇다"는 사실이며,
해(解)에 대한 정보(DP/baseline 성능)는 일절 포함하지 않는다.
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.append(_ROOT)

from FCHEV_SOH import FCHEV_SOH  # noqa: E402

H2_LHV_KJ_PER_G = 120.0
_EFF_BAND_TOL = 1.05      # 최적 비연료소비의 5% 이내를 "효율 밴드"로 본다


def _fc_efficiency_facts(fchev: FCHEV_SOH, n_grid: int = 951) -> Dict[str, Any]:
    """효율 곡선을 훑어 최적 운전점과 효율 밴드를 찾는다 (상수 없음)."""
    p_max = float(fchev.P_FC_max)
    grid = np.linspace(0.0, p_max, n_grid)
    on = grid >= float(fchev.P_FC_off)
    p_on = grid[on]

    eta = np.asarray(fchev.fce_eff(p_on), dtype=np.float64).reshape(-1)
    p_sys = np.asarray(fchev.P_fce(p_on), dtype=np.float64).reshape(-1)
    valid = np.isfinite(eta) & (eta > 1e-6) & np.isfinite(p_sys) & (p_sys > 0.0)
    p_on, eta, p_sys = p_on[valid], eta[valid], p_sys[valid]

    # 비연료소비 [g H2 / kWh] = 3600 / (eta * LHV)
    sfc = 3600.0 / (eta * H2_LHV_KJ_PER_G)
    i_best = int(np.argmin(sfc))
    band = sfc <= sfc[i_best] * _EFF_BAND_TOL

    return {
        "p_fc_max_kw": p_max,
        "best_point_kw": float(p_on[i_best]),
        "best_point_pct_of_max": float(p_on[i_best] / p_max * 100.0),
        "best_efficiency": float(eta[i_best]),
        "best_specific_consumption_g_per_kwh": float(sfc[i_best]),
        "efficient_band_kw": [float(p_on[band].min()), float(p_on[band].max())],
        "efficient_band_pct_of_max": [
            float(p_on[band].min() / p_max * 100.0),
            float(p_on[band].max() / p_max * 100.0),
        ],
        "band_tolerance_pct": (_EFF_BAND_TOL - 1.0) * 100.0,
        # 곡선 모양을 그대로 보여주기 위한 표본 (LLM 이 직접 읽고 판단할 수 있도록)
        "sfc_samples_g_per_kwh": {
            "%.1f kW (%.0f%%)" % (p, p / p_max * 100.0):
                round(float(3600.0 / (float(fchev.fce_eff(p)) * H2_LHV_KJ_PER_G)), 1)
            for p in (np.array([0.02, 0.05, 0.10, 0.20, 0.40, 0.60, 0.80, 1.00]) * p_max)
            if float(fchev.fce_eff(p)) > 1e-6
        },
    }


def _degradation_unit_costs(fchev: FCHEV_SOH, w_fc: float) -> Dict[str, Any]:
    """run_FC_SOH 를 원인별로 격리 호출해 1회(또는 1스텝)당 비용을 직접 측정한다."""
    off = float(fchev.P_FC_off)
    low = float(fchev.P_FC_low)
    high = float(fchev.P_FC_high)
    thresh = float(fchev.P_FC_load_change_rate_thresh)

    def probe(p_old: float, p_new: float) -> Dict[str, float]:
        saved = fchev.P_FC_old
        try:
            fchev.P_FC_old = p_old
            dsoh, info = fchev.run_FC_SOH(p_new)
            return {"dsoh": float(dsoh), **{k: float(info[k]) for k in
                                            ("d_s_s", "d_low", "d_high", "d_l_c")}}
        finally:
            fchev.P_FC_old = saved

    # 각 원인만 켜지도록 동작점을 고른다
    mid = 0.5 * (low + high)                       # 저출력도 고출력도 아닌 지점
    cases = {
        # off -> on, 램프는 임계 이하, 저출력 아님
        "start_stop": probe(0.0, min(low + 0.25 * thresh, mid)),
        # 계속 on, 저출력 유지, 램프 0
        "low_power": probe(0.5 * low, 0.5 * low),
        # 계속 on, 고출력 유지, 램프 0
        "high_power": probe(min(high + 1.0, fchev.P_FC_max), min(high + 1.0, fchev.P_FC_max)),
        # 계속 on, 중간출력, 램프만 임계 초과
        "load_change": probe(mid, min(mid + 2.0 * thresh, high - 1.0)),
    }

    out = {
        "load_change_rate_threshold_kw_per_s": thresh,
        "fc_off_threshold_kw": off,
        "low_power_threshold_kw": low,
        "high_power_threshold_kw": high,
        "w_fc_used": float(w_fc),
        "unit_cost_krw": {},
        "unit_dsoh": {},
        "isolation_check": {},
    }
    for name, r in cases.items():
        out["unit_cost_krw"][name] = round(float(w_fc) * r["dsoh"], 6)
        out["unit_dsoh"][name] = r["dsoh"]
        out["isolation_check"][name] = {k: r[k] for k in ("d_s_s", "d_low", "d_high", "d_l_c")}
    return out


def fc_event_cases(fchev: FCHEV_SOH | None = None) -> list:
    """현재 모델에서 유도한 FC 이벤트별 (P_FCS, h2_fcs, dSOH_FCS) — reward 사전 검증 probe 용.

    off / start / start+load-change / start+low-power / stop / low hold / high hold /
    high+load-change. 크기를 손으로 적지 않고 run_FC_SOH·run_fuel_cell 을 직접 호출한다
    (start 1회 손실이 /3600 제거로 커진 것처럼, 모델이 바뀌면 probe 도 같이 바뀐다).
    """
    fchev = fchev or FCHEV_SOH()
    off, low, high = float(fchev.P_FC_off), float(fchev.P_FC_low), float(fchev.P_FC_high)
    thresh, p_max = float(fchev.P_FC_load_change_rate_thresh), float(fchev.P_FC_max)
    mid, idle = 0.5 * (low + high), 0.5 * (off + low)
    transitions = {
        "off": (0.0, 0.0),
        "start": (0.0, min(low + 0.25 * thresh, mid)),
        "start_load_change": (0.0, mid),
        "start_low_power": (0.0, idle),
        "stop": (mid, 0.0),
        "low_power": (idle, idle),
        "high_power": (p_max, p_max),
        "high_power_load_change": (high - 2.0 * thresh, p_max),
    }
    saved, cases = fchev.P_FC_old, []
    try:
        for name, (p_old, p_new) in transitions.items():
            fchev.P_FC_old = p_old
            dsoh, _ = fchev.run_FC_SOH(p_new)
            _, h2, _ = fchev.run_fuel_cell(p_new)
            cases.append({"event": name, "P_FCS": float(p_new), "h2_fcs": float(h2), "dSOH_FCS": float(dsoh)})
    finally:
        fchev.P_FC_old = saved
    return cases


def battery_event_cases() -> list:
    """현재 배터리 모델에서 유도한 SOC x 전력별 (SOC, P_batt, I_batt, P_batt_loss_kw, dSOH_batt) probe.

    run_battery 를 직접 호출한다. 정격 전력까지 포함하므로 baseline 궤적이 가 보지 않은
    고전류 영역의 dSOH_batt 크기(운용 SOC 대역에서 ~6e-6)도 사전 검증이 다룬다.
    값의 정의는 power_constraints.execute 와 같다: SOC 는 스텝 이후, P_batt 는 clamp 된 전력(W),
    P_batt_loss_kw = r0(스텝 이전 SOC) * I^2 / 1000.
    """
    from Battery import CellModel1
    battery = CellModel1()
    rated = float(battery.batt_maxpower)
    powers = [0.0] + [sign * p for p in (1e3, 1e4, 3e4, rated) for sign in (1.0, -1.0)]
    cases = []
    for soc in (0.05, 0.20, 0.40, 0.60, 0.80, 0.95):
        for power in powers:
            resistance = float(battery.r0_func(soc))
            paras, dsoh, current, _, info = battery.run_battery(power, [soc, 1.0, float(battery.ocv_func(soc))])
            cases.append({"event": "battery_%+.0fkW_soc%.2f" % (power / 1000, soc), "SOC": float(paras[0]),
                          "P_batt": float(info["P_batt_req"]) * 1000, "I_batt": float(current),
                          "P_batt_loss_kw": resistance * float(current) ** 2 / 1000, "dSOH_batt": float(dsoh)})
    return cases


# 현재 실행 모델(power_constraints.execute, FCHEV_SOH.T_W_axle/run_motor)의 서술.
# 모델을 바꾸면 이 문장도 같이 고친다 — tests/test_plant_model_note.py 가 수치로 대조한다.
MOTOR_MODEL_LINES = (
    "Road-load torque is referred to the motor shaft with driveline efficiency 0.98 when motoring "
    "(T/0.98) and 0.95 when generating (T*0.95), then limited to the motor torque envelope.",
    "Electrical power = shaft power / eta_motor when motoring and shaft power * eta_motor when regenerating, "
    "using the torque after limiting.",
    "No measured regenerative map exists: regenerative efficiency is ASSUMED equal to the motoring "
    "efficiency at the same speed and |torque|. This is a modeling assumption, not measured data.",
    "Motor electrical demand depends only on the driving cycle; the policy only splits it between FC and battery.",
)
POWER_BALANCE_LINES = (
    "The FC runs at the commanded power (ramp-limited per step when ramp_limit_kw > 0, clipped to "
    "[0, P_FC_max]); it is NOT projected onto a feasible supply range.",
    "The battery takes the remainder, clamped to its rated power; the residual is recorded as unserved "
    "(shortfall) or unaccepted (surplus) power and is not fed back into the plant.",
    "Only the battery's physical SOC limit ends the drive; a power shortfall does not.",
    "Outside get_reward and not editable by reward search: a failure cost on termination and a per-kW "
    "price on unserved power during learning. An unaccepted surplus is not priced; its hydrogen is already burned.",
    "The adoption gate rejects any ep399 policy that leaves requested traction power undelivered at any step.",
    "Fuel and FC degradation use the applied FC power.",
)


def render_plant_model_note(w_fc: float = 4.275e6, facts: Dict[str, Any] | None = None) -> str:
    """리뷰어·orchestrator·proposer 공통으로 붙이는 짧은 현재-모델 설명 (수치는 런타임 측정)."""
    d = (facts or collect_env_physics_facts(w_fc))["fc_degradation"]
    u, c = d["unit_dsoh"], d["unit_cost_krw"]
    return (
        "PLANT MODEL (current simulator; every listed measurement was produced by it). "
        "Traction: " + " ".join(MOTOR_MODEL_LINES) + " "
        "Power balance: " + " ".join(POWER_BALANCE_LINES) + " "
        "FC SOH loss per occurrence, probed from the model (cost = w_fc * dSOH_FCS at w_fc %.4g): "
        "start (off->on, off below %.2f kW) %.3g = %.4g per start; "
        "load change (|dP_FCS| > %.2f kW/s) %.3g = %.4g per event; "
        "low power (on, below %.2f kW) %.3g = %.4g per second; "
        "high power (>= %.2f kW) %.3g = %.4g per second. "
        "Events add within a step. One start costs the FC SOH of %.0f s of low-power operation "
        "or %.0f load changes."
        % (d["w_fc_used"], d["fc_off_threshold_kw"], u["start_stop"], c["start_stop"],
           d["load_change_rate_threshold_kw_per_s"], u["load_change"], c["load_change"],
           d["low_power_threshold_kw"], u["low_power"], c["low_power"],
           d["high_power_threshold_kw"], u["high_power"], c["high_power"],
           u["start_stop"] / u["low_power"], u["start_stop"] / u["load_change"]))


_CYCLE_DEMAND_CACHE: Dict[Any, Dict[str, Any]] = {}


def cycle_demand_facts(cycle_name: str, time_step: float = 1.0) -> Dict[str, Any]:
    """사이클의 순 전기 수요를 차량 모델(T_W_axle -> run_motor)로 유도한다 (정책 무관).

    속도 프로파일이 모터 버스 전력 P_mot 를 결정하고, FC/배터리 분배(action)는 여기
    개입하지 않는다. 따라서 아래 수치는 '어떤 정책이든 공급해야 하는 에너지'라는
    환경 사실이며, 해(DP/baseline)의 정보가 아니다.
    """
    key = (str(cycle_name), float(time_step))
    if key in _CYCLE_DEMAND_CACHE:
        return _CYCLE_DEMAND_CACHE[key]
    from common.utils import get_acc_limit, get_driving_cycle
    speed = np.asarray(get_driving_cycle(cycle_name), dtype=np.float64)
    acc = np.asarray(get_acc_limit(speed), dtype=np.float64)
    fchev = FCHEV_SOH()
    p_mot_w = np.empty(len(speed), dtype=np.float64)
    for i, (v, a) in enumerate(zip(speed, acc)):
        t_axle, w_axle, p_axle = fchev.T_W_axle(float(v), float(a))
        _, _, _, p_mot = fchev.run_motor(t_axle, w_axle, p_axle)
        p_mot_w[i] = float(p_mot)                      # W (전기, 회생은 음수)
    to_kwh = float(time_step) / 3.6e6
    facts = {
        "cycle_name": str(cycle_name),
        "steps": int(len(speed)),
        "distance_km": float(speed.sum() * time_step / 1000.0),
        "net_elec_demand_kwh": float(p_mot_w.sum() * to_kwh),
        "positive_elec_demand_kwh": float(p_mot_w[p_mot_w > 0.0].sum() * to_kwh),
        "regen_elec_kwh": float(-p_mot_w[p_mot_w < 0.0].sum() * to_kwh),
    }
    _CYCLE_DEMAND_CACHE[key] = facts
    return facts


def cycle_h2_floor_g_per_100km(cycle_name: str,
                               best_sfc_g_per_kwh: float | None = None,
                               time_step: float = 1.0) -> float:
    """물리 하한: 순 수요 에너지를 전부 FC 최적점에서(무손실 버퍼 가정) 만들 때의
    수소 소비 [g/100km].

    도달 불가능한 하한이지만 정책 무관 상수이므로, 이 값을 분자로 둔
    100 x floor / consumption 은 소비량에 단조인 '레벨' 점수가 된다.
    """
    facts = cycle_demand_facts(cycle_name, time_step)
    if best_sfc_g_per_kwh is None:
        best_sfc_g_per_kwh = _fc_efficiency_facts(
            FCHEV_SOH())["best_specific_consumption_g_per_kwh"]
    dist = float(facts["distance_km"])
    if dist <= 0.0:
        return 0.0
    e_net = max(0.0, float(facts["net_elec_demand_kwh"]))
    return float(e_net * float(best_sfc_g_per_kwh) / dist * 100.0)


def collect_env_physics_facts(w_fc: float = 4.275e6) -> Dict[str, Any]:
    fchev = FCHEV_SOH()
    return {
        "fc_efficiency": _fc_efficiency_facts(fchev),
        "fc_degradation": _degradation_unit_costs(fchev, w_fc),
    }


def render_env_physics_block(facts: Dict[str, Any] | None = None,
                             w_fc: float = 4.275e6) -> str:
    """프롬프트에 그대로 끼워 넣는 텍스트 블록. 모든 수치는 환경에서 측정된 값."""
    f = facts or collect_env_physics_facts(w_fc)
    e = f["fc_efficiency"]
    d = f["fc_degradation"]
    uc = d["unit_cost_krw"]

    ranked = sorted(uc.items(), key=lambda kv: -kv[1])
    top, second = ranked[0], ranked[1]
    ratio = (top[1] / second[1]) if second[1] > 0 else float("inf")

    lines = [
        "MEASURED ENVIRONMENT PHYSICS (derived at runtime from the loaded FCHEV_SOH model —",
        "these are facts about the plant you control, not about any reference solution):",
        "",
        "A) FC efficiency vs operating point (P_FC_max = %.1f kW):" % e["p_fc_max_kw"],
        "   - BEST operating point: %.1f kW = %.1f%% of P_FC_max (eta %.4f, %.1f g H2/kWh)"
        % (e["best_point_kw"], e["best_point_pct_of_max"],
           e["best_efficiency"], e["best_specific_consumption_g_per_kwh"]),
        "   - EFFICIENT BAND (within %.0f%% of best specific consumption): %.1f - %.1f kW"
        " = %.1f%% - %.1f%% of P_FC_max"
        % (e["band_tolerance_pct"], e["efficient_band_kw"][0], e["efficient_band_kw"][1],
           e["efficient_band_pct_of_max"][0], e["efficient_band_pct_of_max"][1]),
        "   - specific consumption across the range (g H2/kWh, lower = better):",
    ]
    for k, v in e["sfc_samples_g_per_kwh"].items():
        lines.append("       %-18s %6.1f" % (k, v))
    lines += [
        "   NOTE: this curve peaks at LOW absolute power and degrades monotonically above the band.",
        "   Running the FCS at a HIGH fraction of P_FC_max is NOT efficient on this plant.",
        "",
        "B) FC degradation cost per occurrence (w_fc = %.4g KRW, measured by probing run_FC_SOH):"
        % d["w_fc_used"],
    ]
    for name, cost in ranked:
        unit = "per event" if name in ("start_stop", "load_change") else "per second held"
        lines.append("   - %-12s %12.4f KRW %s" % (name, cost, unit))
    lines += [
        "   - load-change counts when |dP_fc/dt| > %.2f kW/s; low_power when P_fc < %.2f kW;"
        % (d["load_change_rate_threshold_kw_per_s"], d["low_power_threshold_kw"]),
        "     high_power when P_fc >= %.2f kW; start_stop on each off->on transition"
        " (off below %.2f kW)." % (d["high_power_threshold_kw"], d["fc_off_threshold_kw"]),
        "   CONSEQUENCE: '%s' costs %.0fx more than '%s'. Treat these as DISTINCT mechanisms —"
        % (top[0], ratio, second[0]),
        "   do NOT lump start-stop cycling and load-rate transients together; on this plant they",
        "   differ by orders of magnitude and require different corrective levers.",
        "",
    ]
    lines += [
        "C) Power balance (clamp model, shared by baseline SAC and AROMA):",
    ]
    lines += ["   - " + text for text in POWER_BALANCE_LINES]
    lines += [
        "   - The CS target/operating band is a separate objective; a completed drive does not imply CS.",
        "",
        "D) Traction motor model:",
    ]
    lines += ["   - " + text for text in MOTOR_MODEL_LINES]
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    import json
    facts = collect_env_physics_facts()
    print(json.dumps(facts, indent=2, ensure_ascii=False))
    print()
    print(render_env_physics_block(facts))
