"""Input-frozen segmentation of complete original training-cycle ep399 rollouts.

No reset, speed transformation, retraining, or checkpoint search is performed here.
Joint load/motion segments partition time; marginal groups overlap across axes.
"""
from __future__ import annotations


import power_behavior


RULES = {
    "version": "original_cycle_segments_v2", "checkpoint_episode": 399,
    "positive_load_quantiles": [1 / 3, 2 / 3], "acceleration_threshold_m_s2": 0.1,
    "power_tolerance_kw": 1e-5, "entry_soc_difference_notice": 0.02,
    "battery_capacity_kwh": 1.56, "h2_lhv_kwh_per_kg": 33.33,
    "soc_correction_fc_efficiency": 0.5,
    "classification": "load: low <= q33, high >= q67, otherwise medium; nonpositive is low. "
                      "motion: regen (negative motor demand) takes precedence, then acceleration, deceleration, steady.",
    "boundaries": "maximal contiguous runs of joint load/motion labels; [start, stop); no short-run removal",
    "accounting": "fixed common SOC correction efficiency for additive matched diagnostics; NOT the adoption fuel metric",
    "role": "diagnostic_only",
}


DELTA_METRICS = ("hydrogen_g", "soc_correction_g", "equivalent_hydrogen_g", "equivalent_fuel_gkm",
                 "fc_conversion_loss_kwh", "battery_ohmic_loss_kwh", "battery_throughput_kwh",
                 "soc_initial", "soc_final", "soc_delta", "mean_target_error", "target_error_change",
                 "unserved_energy_kwh", "unaccepted_energy_kwh", "fc_total_variation_kw")


def compare_reports(candidate, control):
    for key in ("manifest_hash", "checkpoint_episode", "conditions_id", "seed"):
        if candidate.get(key) is None or candidate[key] != control.get(key):
            raise ValueError(f"Unmatched original-cycle comparison: {key}")
    if candidate["checkpoint_episode"] != 399:
        raise ValueError("Only ep399 comparisons are supported")

    def pair(c, b):
        delta = {k: c[k] - b[k] if c.get(k) is not None and b.get(k) is not None else None for k in DELTA_METRICS}
        return {"candidate": c, "control": b, "delta_candidate_minus_control": delta,
                "entry_soc_differs": abs(delta["soc_initial"]) > RULES["entry_soc_difference_notice"] if delta["soc_initial"] is not None else None,
                "both_fuel_comparable": bool(c.get("fuel_comparable") and b.get("fuel_comparable"))}

    output = {"manifest_hash": candidate["manifest_hash"], "checkpoint_episode": 399,
              "candidate_actor_hash": candidate["actor_hash"], "control_actor_hash": control["actor_hash"],
              "role": "diagnostic_only", "whole_cycle": pair(candidate["whole_cycle"], control["whole_cycle"])}
    for section, key in (("segments", "segment_id"), ("groups", "group_id")):
        baseline = {r[key]: r for r in control[section]}
        if (len(baseline) != len(control[section]) or len(candidate[section]) != len(baseline)
                or set(baseline) != {r[key] for r in candidate[section]}):
            raise ValueError("Segment/group coverage differs")
        output[section] = []
        for row in candidate[section]:
            other = baseline[row[key]]
            metadata = {k: v for k, v in row.items() if k != "metrics"}
            if metadata != {k: v for k, v in other.items() if k != "metrics"}:
                raise ValueError("Segment boundaries/labels differ")
            output[section].append({**metadata, **pair(row["metrics"], other["metrics"])})
    # Separate witnesses for each measured regression; no arbitrary composite score.
    output["regression_witnesses"] = {}
    for metric in ("equivalent_hydrogen_g", "battery_ohmic_loss_kwh", "fc_conversion_loss_kwh", "mean_target_error"):
        rows = [r for r in output["segments"] if (r["delta_candidate_minus_control"].get(metric) or 0) > 1e-12]
        rows.sort(key=lambda r: (-r["delta_candidate_minus_control"][metric], r["start_step"]))
        output["regression_witnesses"][metric] = [{"segment_id": r["segment_id"], "delta": r["delta_candidate_minus_control"][metric]} for r in rows[:5]]
    output["note"] = ("Same time/load, not identical entry SOC or FC state: differences include preceding control history. "
                      "Groups overlap across axes; sum only within one axis. Fuel excludes power-infeasible groups/segments; "
                      "retain whole-cycle failures. Positive loss/error deltas are measured regressions, not causal diagnoses.")
    if candidate.get("power_behavior") and control.get("power_behavior"):
        output["power_behavior"] = power_behavior.compare(candidate["power_behavior"], control["power_behavior"])
    return output
