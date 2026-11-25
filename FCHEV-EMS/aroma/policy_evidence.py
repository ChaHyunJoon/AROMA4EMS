"""Physical evidence from deterministic rollouts; independent of reward weights.

Scalar summaries go to reviewers. Full time series stay in per-checkpoint NPZs.
Missing/non-finite sensors are reported explicitly, never silently replaced by zero.
"""
from __future__ import annotations

import numpy as np


def operating_regimes(data, *, soc0, dt_s):
    """Overlapping, fixed input-based diagnostics; never sum groups or rank by group raw H2.

    Thresholds are independent of the policy. Missing sensors remain explicit. SOC change
    accounts for every selected transition, including noncontiguous groups.
    """
    speed = np.asarray(data.get("speed_m_s", []), dtype=float).reshape(-1)
    n = len(speed)
    required = ("acceleration_m_s2", "P_mot", "P_fce", "h2_fcs", "SOC",
                "P_batt_req", "P_batt_loss_kw")
    arrays = {k: np.asarray(data.get(k, []), dtype=float).reshape(-1) for k in required}
    missing = [k for k, a in arrays.items() if len(a) != n or not np.isfinite(a).all()]
    if not n or not np.isfinite(speed).all():
        missing.append("speed_m_s")
    if missing:
        return {"available": False, "missing_sensors": missing}
    power, acc = arrays["P_mot"], arrays["acceleration_m_s2"]
    groups = {"stopped": speed < .1, "low_load": (power >= 0) & (power < 10),
              "acceleration": acc > .1, "regeneration": power < 0,
              "high_speed": speed >= 22.2222222222}
    soc = arrays["SOC"]
    delta = soc - np.r_[soc0, soc[:-1]]
    result = {}
    for name, mask in groups.items():
        count = int(mask.sum())
        row = {"steps": count, "available": count > 0}
        if count:
            energy = lambda a: float(a[mask].sum() * dt_s / 3600)
            h2 = float(arrays["h2_fcs"][mask].sum() * dt_s)
            fc = arrays["P_fce"]
            row.update(duration_s=count * dt_s, hydrogen_g=h2, fc_energy_kwh=energy(fc),
                       fc_energy_efficiency=energy(fc) / (h2 * 33.33 / 1000) if h2 > 0 else None,
                       fc_low_output_pct=float(np.mean((fc[mask] > 0) & (fc[mask] < 10)) * 100),
                       battery_throughput_kwh=energy(np.abs(arrays["P_batt_req"])),
                       battery_ohmic_loss_kwh=energy(arrays["P_batt_loss_kw"]),
                       soc_mean=float(soc[mask].mean()), soc_delta=float(delta[mask].sum()))
        result[name] = row
    return {"available": True, "groups": result, "missing_sensors": [],
            "basis": "overlapping_input_regimes_diagnostic_only",
            "thresholds": {"stopped_m_s": .1, "low_load_kw": 10., "acceleration_m_s2": .1,
                           "high_speed_m_s": 22.2222222222},
            "note": "Groups overlap; raw H2 alone is not charge-sustaining fuel economy."}


def rollout_physics(data, *, soc0, soc_target, soc_bounds, dt_s, fc_off_kw, ramp_threshold_kw_s):
    values, missing = {}, []

    def sensor(key):
        arr = np.asarray(data.get(key, []), dtype=float).reshape(-1)
        if not arr.size or not np.isfinite(arr).all():
            missing.append(key)
            return None
        return arr

    def stats(name, arr):
        if arr is not None:
            values.update({name + "_min": float(arr.min()), name + "_mean": float(arr.mean()),
                           name + "_max": float(arr.max()), name + "_p95": float(np.quantile(arr, .95))})

    soc = sensor("SOC")
    if soc is not None:
        values.update(soc_initial=float(soc0), soc_first_logged=float(soc[0]), soc_final=float(soc[-1]),
                      soc_final_minus_initial=float(soc[-1] - soc0),
                      soc_final_minus_target=float(soc[-1] - soc_target), soc_swing=float(np.ptp(soc)),
                      soc_below_steps=int(np.sum(soc <= soc_bounds[0])),
                      soc_above_steps=int(np.sum(soc >= soc_bounds[1])))
        stats("soc", soc)
    pfc = sensor("P_fc")
    ramp = None
    if pfc is not None:
        stats("fc_power_kw", pfc)
        ramp = np.diff(np.r_[0., pfc]) / dt_s  # plant reset starts at P_FC=0
        stats("fc_abs_ramp_kw_s", np.abs(ramp))
        values.update(fc_on_pct=float(100 * np.mean(pfc >= fc_off_kw)),
                      fc_ramp_threshold_kw_s=float(ramp_threshold_kw_s),
                      fc_ramp_exceed_steps=int(np.sum(np.abs(ramp) > ramp_threshold_kw_s)),
                      fc_total_variation_kw=float(np.abs(ramp).sum() * dt_s))
    components = {}
    for name, key in (("start_stop", "d_s_s"), ("low_power", "d_low"),
                      ("high_power", "d_high"), ("load_change", "d_l_c")):
        arr = sensor(key)
        if arr is not None:
            values["fc_" + name + "_count"] = int(np.sum(arr > 0))
            # FCHEV_SOH.run_FC_SOH: De_i is percent, then divided by 100 (fraction). d_s_s and d_l_c are
            # percent per event; d_low and d_high are %/h rates, converted to per second.
            scale = {"d_s_s": 1e-3, "d_l_c": 1e-5}.get(key, 1e-3 / 3600)
            loss = float(arr.sum() * scale / 100)
            values["fc_" + name + "_soh_loss"] = loss
            components[name] = loss
    for name, key in (("fc_step_soh_loss", "FCS_De"), ("battery_step_soh_loss", "dsoh")):
        arr = sensor(key)
        if arr is not None:
            values[name + "_sum"] = float(arr.sum())
    pbatt = sensor("P_batt_req")  # plant logging uses kW, not self.P_batt (W)
    stats("battery_power_kw", pbatt)
    if pbatt is not None:
        values.update(battery_discharge_kwh=float(np.maximum(pbatt, 0).sum() * dt_s / 3600),
                      battery_charge_kwh=float(np.maximum(-pbatt, 0).sum() * dt_s / 3600),
                      battery_throughput_kwh=float(np.abs(pbatt).sum() * dt_s / 3600))
    for name, key in (("battery_current_a", "I"), ("battery_c_rate", "I_c"),
                      ("battery_voltage_v", "pack_Vt"), ("action", "policy_action")):
        stats(name, sensor(key))
    fuel = sensor("h2_fcs")
    for key in ("unserved_power_kw", "unaccepted_power_kw"):
        if key in data:
            arr = sensor(key)
            stats(key, arr)
            if arr is not None:
                values[key + "_integral_kwh"] = float(arr.sum() * dt_s / 3600)
    if "power_constraint_failed" in data:
        arr = sensor("power_constraint_failed")
        if arr is not None:
            values["power_constraint_failed_steps"] = int(np.count_nonzero(arr))
    if fuel is not None:
        values["fc_hydrogen_g"] = float(fuel.sum() * dt_s)
    for name, key in (("motor_power_kw", "P_mot"), ("battery_ohmic_loss_kw", "P_batt_loss_kw")):
        arr = sensor(key)
        stats(name, arr)
        if arr is not None:
            values[name + "_integral_kwh"] = float(arr.sum() * dt_s / 3600)
    witnesses = []
    if soc is not None and pfc is not None and len(soc) == len(pfc):
        # Named extrema plus largest ramps: indices point into the saved NPZ.
        indices = {0, len(soc) - 1, int(soc.argmin()), int(soc.argmax())}
        indices.update(int(i) for i in np.argsort(np.abs(ramp))[-5:])
        for i in sorted(indices):
            witnesses.append({"step": i, "time_s": i * dt_s, "soc": float(soc[i]),
                              "p_fc_kw": float(pfc[i]), "ramp_kw_s": float(ramp[i]),
                              "p_batt_kw": float(pbatt[i]) if pbatt is not None else None})
    regimes = operating_regimes(data, soc0=soc0, dt_s=dt_s)
    net_fc = np.asarray(data.get("P_fce", []), dtype=float).reshape(-1)
    if net_fc.size and np.isfinite(net_fc).all():
        values["fc_low_output_pct"] = float(np.mean((net_fc > 0) & (net_fc < 10)) * 100)
    regen = regimes.get("groups", {}).get("regeneration", {})
    if regen.get("available"):
        values["fc_regeneration_energy_kwh"] = regen["fc_energy_kwh"]
    return {"scalars": values, "regimes": regimes,
            "missing_sensors": sorted(set(missing)), "witness_steps": witnesses,
            "dominant_fc_degradation": max(components, key=components.get) if any(components.values()) else None,
            "count_definition": "start_stop counts starts; low/high_power count active steps; load_change counts threshold-exceeding steps"}


def summarize_physics(records):
    available = [r for r in records if r.get("physical_evidence")]
    keys = sorted({k for r in available for k in r["physical_evidence"]["scalars"]})
    scalars = {}
    for key in keys:
        vals = [r["physical_evidence"]["scalars"][key] for r in available
                if key in r["physical_evidence"]["scalars"]]
        scalars[key] = {"mean": float(np.mean(vals)), "min": float(min(vals)),
                        "max": float(max(vals)), "count": len(vals)}
    examples = {}
    if available and all(k in r for r in available for k in ("fc_loss", "soc_in_bounds", "fuel_gkm")):
        for label, key, order in (("largest_fc_loss", "fc_loss", max), ("lowest_soc_in_bounds", "soc_in_bounds", min),
                                  ("largest_fuel", "fuel_gkm", max)):
            row = order(available, key=lambda r: r[key])
            examples[label] = {"episode": row["episode"], "fuel_gkm": row["fuel_gkm"],
                               "fc_loss": row["fc_loss"], "soc_in_bounds": row["soc_in_bounds"],
                               "trajectory_path": row.get("trajectory_path"), "checkpoint_path": row.get("checkpoint_path"),
                               "witness_steps": row["physical_evidence"].get("witness_steps", [])}
    return {"basis": "deterministic_rollouts", "record_count": len(records),
            "available_count": len(available), "episodes": [r["episode"] for r in records],
            "scalars": scalars,
            "representative_rollouts": examples,
            "missing_sensors": sorted({s for r in available for s in r["physical_evidence"]["missing_sensors"]})}
