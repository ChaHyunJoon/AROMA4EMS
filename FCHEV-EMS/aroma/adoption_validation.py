"""Frozen ep399 acceptance rules, independent of LLM diagnoses, tail sampling and seed.

Every blocking check is paired against evidence measured BEFORE any candidate exists:
the run's own baseline for absolute floors, the current champion for step regressions.
Only tolerances are constants, so the same policy applies to any seed, cycle or baseline.
Absolute goals (charge sustaining, zero residual, target-band recovery) are recorded in
`targets` and never block, because a floor derived from a deficient baseline is not an
achievement. Measurement modules retain their own accounting; this module owns acceptance.
"""
from __future__ import annotations

import math

from scenario_validation import digest


def build_policy(args):
    policy = {
        "version": "post_training_acceptance_v3", "checkpoint_episode": 399,
        "target_soc": float(args.soc_target),
        "min_improvement_gkm": float(args.validation_min_improvement_gkm),
        "min_improvement_fraction": float(getattr(args, "validation_min_improvement_fraction", .001)),
        "condition_soc_error_increase": float(getattr(args, "validation_condition_soc_tolerance", .005)),
        "condition_fuel_regression_fraction": float(getattr(args, "validation_condition_fuel_regression", .05)),
        "unaccepted_peak_slack_kw": float(getattr(args, "validation_unaccepted_peak_slack_kw", .5)),
        "unaccepted_energy_slack_kwh": float(getattr(args, "validation_unaccepted_energy_slack_kwh", .001)),
        # Unserved demand keeps the measurement layer's numerical-noise level; it is not a budget.
        "unserved_energy_kwh": 1e-6, "unserved_peak_kw": 1e-5,
        "group_fuel_tolerance_g": .05, "scenario_fuel_tolerance_gkm": .01,
        "scenario_duration_steps": 600, "recovery_hold_s": 30,
        "scenario_power_checks": ["unaccepted_power"],
        "minimum_in_bounds_pct": float(args.validation_min_in_bounds),
        "reference": "run baseline ep399, evaluated before any candidate or LLM proposal",
        "aspirational_targets": {
            "terminal_soc_error": float(getattr(args, "validation_terminal_soc_error", .02)),
            "scenario_soc_error": float(getattr(args, "validation_scenario_soc_error", .02)),
            "recovery_band": .02, "recovery_hold_s": 30,
            "unaccepted_peak_kw": float(getattr(args, "validation_unaccepted_peak_kw", 0.)),
            "unaccepted_energy_kwh": float(getattr(args, "validation_unaccepted_energy_kwh", 0.)),
        },
        "note": "Seed-independent engineering budgets, not statistical significance, independent-seed or "
                "unseen-cycle claims. Absolute floors are the run's own baseline plus a fixed tolerance, so a "
                "deficient baseline lowers the floor: read targets before calling any pass an achievement. "
                "A power check pass means the allowed residual budget was met, NOT that a vehicle path "
                "(friction braking or otherwise) for the unaccepted power was demonstrated. "
                "Behavior suspicions and individual segment witnesses remain diagnostic, not automatic vetoes.",
    }
    for key, value in policy.items():
        if isinstance(value, (int, float)) and (not math.isfinite(value) or value < 0):
            raise ValueError(f"Invalid acceptance policy: {key}")
    for key, value in policy["aspirational_targets"].items():
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"Invalid acceptance target: {key}")
    for key in ("min_improvement_fraction", "condition_fuel_regression_fraction", "target_soc",
                "condition_soc_error_increase"):
        if policy[key] > 1:
            raise ValueError(f"Invalid acceptance fraction: {key}")
    policy["policy_hash"] = digest(policy)
    return policy
