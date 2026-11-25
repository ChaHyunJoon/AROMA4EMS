"""Executable reward contracts and candidate-specific, evidence-based review.

These checks establish eligibility for an experiment, never fuel improvement.
LLM objections reference this registry; they cannot invent a blocking threshold.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import math
from pathlib import Path
from types import MethodType, SimpleNamespace

import numpy as np


from reward_patcher import validate_method_source

CONTRACT_VERSION = "reward_contract_v1"
REQUIRED_KEYS = ["EMS_reward", "h2_fcs", "h2_batt", "h2_equal", "soc_cost",
                 "h2_cost", "fcs_soh_cost", "batt_soh_cost", "objective_cost", "soc_in_bounds"]
COST_KEYS = ["soc_cost", "h2_cost", "fcs_soh_cost", "batt_soh_cost"]
_BUILTINS = {"abs": abs, "bool": bool, "float": float, "int": int, "len": len,
             "max": max, "min": min, "pow": pow, "round": round, "sum": sum}
_NUMERIC = {"abs", "fabs", "exp", "expm1", "log", "log1p", "sqrt", "square", "power",
            "clip", "minimum", "maximum", "where", "tanh", "sign", "isfinite", "float64"}


def candidate_id(source):
    return hashlib.sha256(source.encode()).hexdigest()


def _path(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return _path(node.value) + "." + node.attr
    if isinstance(node, ast.Subscript):
        return _path(node.value) + "[]"
    return ""


def compile_reward(source):
    validate_method_source(source, required_info_keys=REQUIRED_KEYS)
    tree = ast.parse(source)
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        raise ValueError("Only one get_reward function is allowed")
    fn = tree.body[0]
    if (len(fn.args.args) != 1 or fn.args.defaults or fn.args.kwonlyargs
            or fn.args.vararg or fn.args.kwarg or fn.decorator_list):
        raise ValueError("Expected get_reward(self) without decorators or defaults")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.For, ast.While, ast.AsyncFor,
                             ast.With, ast.AsyncWith, ast.Lambda, ast.ClassDef, ast.Global,
                             ast.Nonlocal, ast.Delete, ast.ListComp, ast.SetComp, ast.DictComp,
                             ast.GeneratorExp, ast.NamedExpr, ast.Try, ast.Raise)):
            raise ValueError(f"Unsupported reward operation: {type(node).__name__}")
        if isinstance(node, ast.FunctionDef) and node is not fn:
            raise ValueError("Nested functions are not allowed")
        if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            raise ValueError("Private attribute access is not allowed")
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                for item in ast.walk(target):
                    if isinstance(item, (ast.Attribute, ast.Subscript)) and isinstance(item.ctx, ast.Store):
                        if not (isinstance(item, ast.Subscript) and _path(item.value) == "self.info"):
                            raise ValueError("Only self.info[key] may be written")
                    if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Store) and item.id in {"self", "np", "math", "numpy"}:
                        raise ValueError("Reward input names cannot be rebound")
        if isinstance(node, ast.Call):
            name = _path(node.func)
            if name in _BUILTINS or name in {"self.info.update", "self.info.setdefault"}:
                continue
            if name.startswith(("np.", "numpy.", "math.")) and name.split(".", 1)[1] in _NUMERIC:
                continue
            raise ValueError(f"Unsupported call: {name}")
    namespace = {"__builtins__": _BUILTINS, "np": np, "numpy": np, "math": math}
    exec(compile(tree, "<candidate_reward>", "exec"), namespace)
    return namespace["get_reward"]


def checked_reward(fn, state):
    """Also runs on every real simulator step, including evaluation.

    Expose scalar inputs and numeric tuples only, with a separate info dict.
    Mutable plant objects/arrays cannot be reached even via numpy's out arguments.
    """
    inputs = {k: v for k, v in vars(state).items()
              if isinstance(v, (int, float, bool, np.number))
              or (isinstance(v, tuple) and all(isinstance(x, (int, float, np.number)) for x in v))}
    probe = SimpleNamespace(**inputs)
    original_info = dict(state.info)
    probe.info = copy.deepcopy(original_info)
    reward = float(fn(probe))
    vals = {key: float(probe.info[key]) for key in REQUIRED_KEYS}
    if not all(math.isfinite(v) for v in [reward, *vals.values()]):
        raise ValueError("finite_reward: non-finite output")
    close = lambda a, b: math.isclose(float(a), float(b), rel_tol=1e-8, abs_tol=1e-9)
    if not (close(reward, vals["EMS_reward"]) and close(-reward, vals["objective_cost"])):
        raise ValueError("logging_consistency: reward/objective mismatch")
    for key in ("h2_fcs", "h2_batt", "h2_equal"):
        if not close(vals[key], getattr(state, key)):
            raise ValueError(f"logging_consistency: physical {key} changed")
    low, high = state.soc_bounds
    if vals["soc_in_bounds"] != int(low < state.SOC < high):
        raise ValueError("logging_consistency: SOC boundary flag changed")
    for key, value in original_info.items():
        if key not in REQUIRED_KEYS and key in probe.info:
            original, proposed = np.asarray(value), np.asarray(probe.info[key])
            numeric = original.dtype.kind in 'biufc' and proposed.dtype.kind in 'biufc'
            if not np.array_equal(original, proposed, equal_nan=numeric):
                raise ValueError(f"logging_consistency: physical telemetry {key} changed")
    # Only the declared reward log outputs are accepted from the candidate.
    state.info.update({key: probe.info[key] for key in REQUIRED_KEYS})
    return reward


def bind_reward(env, source):
    fn = compile_reward(source)
    env.agent.get_reward = MethodType(lambda state: checked_reward(fn, state), env.agent)


def _probe_state(case, args):
    from multi_agent_review import _make_reward_probe_state
    state = _make_reward_probe_state(case)
    for attr in ("w_soc", "w_h2", "w_fc", "w_batt", "eq_h2_batt_coef"):
        setattr(state, attr, float(getattr(args, attr)))
    state.SOC_target = float(args.soc_target)
    state.SOC_init = float(args.soc0)
    state.soc_bounds = (float(args.soc_low), float(args.soc_high))
    state.P_FCS_max, state.P_batt_max = 95.0, 100_000.0
    # Model-derived probes carry the plant's own current and ohmic loss; the grid uses rough stand-ins.
    state.P_batt_loss_kw = float(case.get("P_batt_loss_kw", abs(state.P_batt) / 1000.0 * .02))
    state.I_batt = float(case.get("I_batt", state.P_batt / 300.0))
    # Motor electrical power (W): P_batt = P_mot - FC (DC/DC) power, with FC output standing in for DC/DC.
    state.P_mot = float(case.get("P_mot", state.P_batt + 1000.0 * state.P_FCS))
    return state


def fc_event_probes():
    """FC events at the magnitudes of the loaded plant model, across SOC and battery load.

    The behavior grid's dSOH_FCS stops at 7e-7; one FC start is 1.96e-5 here, so a reward
    that is finite on the grid can still overflow on the first real start.
    """
    from env_physics_facts import fc_event_cases
    return [dict(event, SOC=soc, P_batt=p_batt, dSOH_batt=4e-7)
            for event in fc_event_cases() for soc in (0.0, 0.35, 0.60, 0.85, 1.0)
            for p_batt in (-30_000.0, 30_000.0)]


def battery_event_probes():
    """Battery operating points of the loaded model up to rated power, at a mid FC load.

    The behavior grid's dSOH_batt stops at 4e-7 (about the p95 of a real rollout); the model
    reaches ~2e-6 at 30 kW and ~6e-6 at rated power inside the SOC band.
    """
    from env_physics_facts import battery_event_cases
    return [dict(case, h2_fcs=0.85, P_FCS=20.0, dSOH_FCS=1e-7) for case in battery_event_cases()]


def verify_direction(source, current_method, role, args):
    """Ablation design check, separate from the physical acceptance contract."""
    from multi_agent_review import _reward_behavior_grid
    candidate, control = compile_reward(source), compile_reward(current_method)
    changed, target = False, role["cost_key"]
    for case in _reward_behavior_grid():
        new, old = _probe_state(case, args), _probe_state(case, args)
        checked_reward(candidate, new)
        checked_reward(control, old)
        for key in COST_KEYS:
            different = not math.isclose(new.info[key], old.info[key], rel_tol=1e-8, abs_tol=1e-9)
            if different and key != target:
                return {"status": "fail", "reason": f"{role['name']} must preserve {key}"}
            if key == target and different:
                if target == "soc_cost":
                    if not args.soc_low < new.SOC < args.soc_high:
                        return {"status": "fail", "reason": "SOC tracking must preserve out-of-bounds cost"}
                changed = True
    return {"status": "pass" if changed else "fail", "reason": "target cost changed" if changed else "target cost unchanged on probes"}


def verify_candidate(source, args, extra_probes=()):
    from multi_agent_review import _reward_behavior_grid
    result = {"candidate_id": candidate_id(source), "contract_version": CONTRACT_VERSION,
              "status": "pass", "checks": {}, "evidence": []}
    try:
        fn = compile_reward(source)
    except Exception as exc:
        result.update(status="fail", checks={"code_contract": "fail"}, evidence=[str(exc)])
        return result
    result["checks"]["code_contract"] = "pass"
    count = 0
    # These broad probes are smoke tests, not a claim that every physical state is covered.
    cases = _reward_behavior_grid()
    cases.extend(fc_event_probes())
    cases.extend(battery_event_probes())
    cases.extend(extra_probes)
    for case in cases:
        state = _probe_state(case, args)
        try:
            checked_reward(fn, state)
            count += 1
        except AttributeError as exc:
            result.update(status="inconclusive", evidence=[str(exc), case])
            result["checks"]["finite_reward"] = "inconclusive"
            return result
        except Exception as exc:
            key = "logging_consistency" if str(exc).startswith("logging_consistency") else "finite_reward"
            result.update(status="fail", evidence=[str(exc), case])
            result["checks"][key] = "fail"
            return result
    result["checks"].update(finite_reward="pass", logging_consistency="pass")
    result["probe_count"] = count
    return result


def _replay_states(trajectory_path, args):
    """Yield the real EMS state at every step of a stored deterministic rollout."""
    import env_ldri  # noqa: F401  (puts the project root, which holds the plant modules, on sys.path)
    from agentEMS_val_base import EMS
    data = np.load(trajectory_path)
    state = EMS(args.w_soc, args.soc0, args.MODE, float(getattr(args, "obs_speed_scale", 40.)),
                float(getattr(args, "obs_acc_scale", 4.)), w_h2=args.w_h2, w_fc=args.w_fc, w_batt=args.w_batt,
                eq_h2_batt_coef=args.eq_h2_batt_coef, soc_target=args.soc_target,
                soc_bounds=(args.soc_low, args.soc_high), ramp_limit_kw=getattr(args, "ramp_limit_kw", 0.))
    fc_soh = np.asarray(data["FCS_SOH"], dtype=float)
    columns = {"SOC": data["SOC"], "SOH_batt": data["SOH"], "SOH_FCS": fc_soh,
               "dSOH_FCS": -np.diff(np.r_[1.0, fc_soh]), "dSOH_batt": data["dsoh"],
               "P_FCS": data["fc_applied_kw"], "P_batt": 1000 * np.asarray(data["battery_delivered_kw"]),
               "I_batt": data["I"], "P_batt_loss_kw": data["P_batt_loss_kw"], "P_mot": 1000 * np.asarray(data["P_mot"]),
               "h2_fcs": data["h2_fcs"], "h2_batt": data["h2_batt"], "h2_equal": data["h2_equal"],
               "car_spd": data["speed_m_s"], "car_acc": data["acceleration_m_s2"], "travel": data["travel"]}
    for step in range(len(columns["SOC"])):
        for key, values in columns.items():
            setattr(state, key, float(values[step]))
        state.info = {}
        yield state


def measure_cost_scale(source, trajectory_path, args):
    """Per-step cost magnitudes of a candidate reward replayed on a stored (baseline) rollout.

    Besides the logged terms it measures how far the reward's non-SOC objective is from the true
    operating cost at the selection prices (operating_cost.py), expressed in reward units
    (w_h2 per gram of H2): price_deviation = (objective_cost - soc_cost) - w_h2 * (h2_fcs
    + g_per_unit_fc * dSOH_FCS + g_per_unit_batt * dSOH_batt). Rescaling a logged dSOH term and adding
    an extra term are thereby measured by one yardstick.
    """
    from operating_cost import USD_PER_BATT_LOSS, USD_PER_FC_LOSS, USD_PER_H2_G
    if not trajectory_path or not Path(trajectory_path).is_file():
        return {"status": "unavailable", "reason": "no stored baseline rollout"}
    fn = compile_reward(source)
    g_fc, g_batt = USD_PER_FC_LOSS / USD_PER_H2_G, USD_PER_BATT_LOSS / USD_PER_H2_G
    terms, extra, deviation, selection = {}, [], [], []
    reference = []
    for step, state in enumerate(_replay_states(trajectory_path, args)):
        inputs = {k: v for k, v in vars(state).items()
                  if isinstance(v, (int, float, bool, np.number))
                  or (isinstance(v, tuple) and all(isinstance(x, (int, float, np.number)) for x in v))}
        probe = SimpleNamespace(**inputs, info={})
        try:
            fn(probe)
            values = [float(probe.info[key]) for key in COST_KEYS + ["objective_cost"]]
            if not all(math.isfinite(v) for v in values):
                raise ArithmeticError("non-finite cost")
        except AttributeError as exc:
            return {"status": "unavailable", "reason": f"input not in stored rollout: {exc}"}
        except (ArithmeticError, ValueError) as exc:
            # Real magnitudes (an FC start is far above the probe grid) can break a reward the probes passed.
            measured = {k: inputs[k] for k in ("SOC", "P_FCS", "P_batt", "I_batt", "h2_fcs", "dSOH_FCS", "dSOH_batt")}
            return {"status": "fail", "reason": f"finite_reward: {exc!r} at step {step} of the baseline ep399 "
                                                "rollout with measured inputs " + json.dumps(measured)}
        standard = sum(values[:-1])
        extra.append(values[-1] - standard)
        reference.append(float(args.w_h2) * state.h2_fcs)
        priced = float(args.w_h2) * (state.h2_fcs + g_fc * state.dSOH_FCS + g_batt * state.dSOH_batt)
        selection.append(priced)
        deviation.append(values[-1] - values[0] - priced)  # objective minus soc_cost minus true price
        for key, value in probe.info.items():
            if key in REQUIRED_KEYS and key not in COST_KEYS + ["objective_cost"]:
                continue
            number = _finite_float_or_none(value)
            if number is not None:
                terms.setdefault(key, []).append(number)
    extra, deviation = np.asarray(extra), np.asarray(deviation)
    return {"status": "measured", "basis": "candidate reward replayed on the baseline ep399 deterministic rollout",
            "trajectory": str(trajectory_path), "steps": int(len(extra)),
            "baseline_h2_cost_mean": float(np.mean(reference)),
            "selection_cost_mean": float(np.mean(selection)),
            "price_deviation_mean_abs": float(np.mean(np.abs(deviation))),
            "price_deviation_max_abs": float(np.max(np.abs(deviation))),
            "extra_cost_mean_abs": float(np.mean(np.abs(extra))), "extra_cost_max_abs": float(np.max(np.abs(extra))),
            "term_mean_per_step": {k: float(np.mean(v)) for k, v in terms.items()}}


def _finite_float_or_none(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def verify_cost_scale(source, trajectory_path, args):
    """The non-SOC objective must stay near the true operating cost at the selection prices.

    One yardstick for every way of reshaping cost: a multiplier on a logged dSOH term, a new extra
    term, or both. The per-step mean of |(objective_cost - soc_cost) - selection-priced cost| on the
    baseline rollout may be at most `cost_scale_max_ratio` times the mean selection-priced cost.
    Moving the FC/battery weights toward the selection prices shrinks the deviation; an oversized
    penalty (e.g. an ohmic term 100x the hydrogen cost) grows it.
    """
    limit = float(getattr(args, "cost_scale_max_ratio", 1.0))
    measured = measure_cost_scale(source, trajectory_path, args)
    if measured["status"] != "measured":
        return {**measured, "limit_ratio": limit}
    ratio = measured["price_deviation_mean_abs"] / max(measured["selection_cost_mean"], 1e-12)
    # soc_cost is exempt from the deviation but not from scale: catalog CS terms live in it.
    soc_ratio = abs(measured["term_mean_per_step"].get("soc_cost", 0.0)) / max(measured["selection_cost_mean"], 1e-12)
    status = "pass" if limit <= 0 or (ratio <= limit and soc_ratio <= limit) else "fail"
    result = {**measured, "status": status, "price_deviation_ratio": ratio, "soc_cost_ratio": soc_ratio,
              "limit_ratio": limit}
    if status == "fail" and ratio <= limit:
        result["reason"] = (f"cost_scale: soc_cost averages {measured['term_mean_per_step']['soc_cost']:.4g} per "
                            f"step on the baseline rollout = {soc_ratio:.3g}x the mean selection-priced cost "
                            f"{measured['selection_cost_mean']:.4g} (limit {limit:g}x). Charge-sustaining terms "
                            "are exempt from the price deviation, not from scale. Measured per-step means: "
                            + json.dumps({k: round(v, 6) for k, v in measured["term_mean_per_step"].items()})
                            + ". Rescale the charge-sustaining terms from these measured values.")
    elif status == "fail":
        result["reason"] = (f"cost_scale: the reward's non-SOC objective deviates from the selection-priced "
                            f"operating cost by {measured['price_deviation_mean_abs']:.4g} per step on average on "
                            f"the baseline rollout = {ratio:.3g}x the mean selection-priced cost "
                            f"{measured['selection_cost_mean']:.4g} (limit {limit:g}x). This counts multipliers on "
                            "the logged terms and extra terms alike. Measured per-step means: "
                            + json.dumps({k: round(v, 6) for k, v in measured["term_mean_per_step"].items()})
                            + ". Rescale from these measured values toward the selection prices.")
    return result
