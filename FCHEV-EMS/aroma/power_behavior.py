"""Frozen descriptive event rules; matched-window diagnoses are not causal proof.

Power balance is checked by cycle_segments. Counts alone never establish waste.
All event energies are descriptive; overlapping event witnesses must not be summed.
"""
from __future__ import annotations



def windows(n, dt, rules):
    size = max(1, int(round(rules["window_s"] / dt)))
    return [{"window_id": f"behavior_{a // size:04d}", "start_step": a, "stop_step": min(a + size, n),
             "start_s": a * dt, "stop_s": min(a + size, n) * dt} for a in range(0, n, size)]


def diagnose(candidate, control, rules):
    c, b = candidate["metrics"], control["metrics"]
    ca, ba = candidate["behavior"], control["behavior"]
    diagnostics = {}
    for kind in ("low_load_cycling", "fc_battery_handoff"):
        reasons, status = [], "no_extra_activity_detected"
        if not ca.get("available") or not ba.get("available"):
            diagnostics[kind] = {"status": "unknown", "reasons": ["missing_power_sensors"]}
            continue
        if kind == "low_load_cycling":
            activity = ca["low_load_return_count"] > 0 and (
                ca["low_load_return_count"] > ba["low_load_return_count"] or
                ca["low_load_circulation_kwh"] > ba["low_load_circulation_kwh"] + rules["energy_tolerance_kwh"])
        else:
            activity = ca["handoff_reversal_count"] > 0 and (
                ca["handoff_reversal_count"] > ba["handoff_reversal_count"] or
                ca["opposing_variation_kw"] > ba["opposing_variation_kw"] + rules["variation_tolerance_kw"])
        needed = ("equivalent_hydrogen_g", "battery_ohmic_loss_kwh", "fc_conversion_loss_kwh",
                  "soc_initial", "soc_final", "mean_target_error", "final_target_error", "target_error_change",
                  "fc_initial_kw", "fc_total_variation_kw", "fc_load_change_count")
        if c.get("power_feasible") is not True or b.get("power_feasible") is not True:
            status, reasons = "unknown", ["power_infeasible_or_unknown"]
        elif any(c.get(k) is None or b.get(k) is None for k in needed):
            status, reasons = "unknown", ["missing_energy_soc_or_fc_evidence"]
        elif not activity:
            pass
        elif (abs(c["soc_initial"] - b["soc_initial"]) > rules["entry_soc_tolerance"] or
              abs(c["fc_initial_kw"] - b["fc_initial_kw"]) > rules["entry_fc_tolerance_kw"]):
            status, reasons = "confounded_entry_state", ["entry_soc_or_fc_differs"]
        elif ca["cross_boundary_event_count"]:
            status, reasons = "needs_neighbor_window", ["event_started_before_matched_window"]
        else:
            fuel_benefit = c["equivalent_hydrogen_g"] < b["equivalent_hydrogen_g"] - rules["fuel_tolerance_g"]
            # Entry SOC is matched within tolerance, but offset still matters:
            # include recovery gain as well as absolute error, not only end SOC.
            soc_benefit = (c["mean_target_error"] < b["mean_target_error"] - rules["soc_tolerance"] or
                           c["final_target_error"] < b["final_target_error"] - rules["soc_tolerance"] or
                           c["target_error_change"] < b["target_error_change"] - rules["soc_tolerance"])
            fc_benefit = (c["fc_total_variation_kw"] < b["fc_total_variation_kw"] - rules["variation_tolerance_kw"] or
                          c["fc_load_change_count"] < b["fc_load_change_count"])
            higher_loss = (c["battery_ohmic_loss_kwh"] + c["fc_conversion_loss_kwh"] >
                           b["battery_ohmic_loss_kwh"] + b["fc_conversion_loss_kwh"] + rules["energy_tolerance_kwh"])
            reasons = [name for name, yes in (("equivalent_fuel_benefit", fuel_benefit), ("soc_recovery_or_tracking_benefit", soc_benefit),
                       ("fc_smoothing_benefit", fc_benefit), ("higher_total_conversion_and_ohmic_loss", higher_loss)) if yes]
            if fuel_benefit or soc_benefit or fc_benefit:
                status = "benefit_or_tradeoff"
            elif higher_loss:
                status = "suspected_avoidable_cycling" if kind == "low_load_cycling" else "suspected_excessive_handoff"
            else:
                status = "extra_activity_without_measured_loss_increase"
        diagnostics[kind] = {"status": status, "extra_activity": bool(activity), "reasons": reasons}
    return diagnostics


def compare(candidate, control):
    if candidate["rules"] != control["rules"]:
        raise ValueError("Different power-behavior rules")
    controls = {r["window_id"]: r for r in control["windows"]}
    if len(controls) != len(control["windows"]) or len(controls) != len(candidate["windows"]) or set(controls) != {r["window_id"] for r in candidate["windows"]}:
        raise ValueError("Different power-behavior window coverage")
    rows = []
    for c in candidate["windows"]:
        b = controls[c["window_id"]]
        keys = ("window_id", "start_step", "stop_step", "start_s", "stop_s")
        if any(c[k] != b[k] for k in keys):
            raise ValueError("Different power-behavior window boundaries")
        delta = {k: c["metrics"][k] - b["metrics"][k] for k in c["metrics"]
                 if isinstance(c["metrics"][k], (int, float)) and not isinstance(c["metrics"][k], bool)
                 and isinstance(b["metrics"].get(k), (int, float))}
        behavior_delta = {k: c["behavior"][k] - b["behavior"][k] for k in c["behavior"]
                          if isinstance(c["behavior"][k], (int, float)) and not isinstance(c["behavior"][k], bool)
                          and isinstance(b["behavior"].get(k), (int, float))}
        rows.append({**{k: c[k] for k in keys}, "candidate": {k: c[k] for k in ("metrics", "behavior", "event_ids")},
                     "control": {k: b[k] for k in ("metrics", "behavior", "event_ids")},
                     "metric_delta": delta, "behavior_delta": behavior_delta,
                     "diagnoses": diagnose(c, b, candidate["rules"])})
    summary = {}
    for kind in ("low_load_cycling", "fc_battery_handoff"):
        statuses = [r["diagnoses"][kind]["status"] for r in rows]
        summary[kind] = {s: statuses.count(s) for s in sorted(set(statuses))}
    return {"rules": candidate["rules"], "windows": rows, "summary": summary,
            "suspect_windows": [{"window_id": r["window_id"], "kind": k} for r in rows for k, d in r["diagnoses"].items()
                                if d["status"].startswith("suspected_")],
            "note": "Fixed same-time windows; local suspected inefficiency, not causal proof or whole-cycle rejection. "
                    "Event witnesses can overlap; do not sum their energies. Inspect entry state, neighbor windows and whole-cycle outcomes."}
