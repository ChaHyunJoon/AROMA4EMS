"""Physical tool definitions and execution engine for the AROMA multi-agent workflow.

Tools wrap existing functions from feedback_parser, reward_patcher, and the filesystem,
giving LLM agents the ability to query live data instead of relying on prompt snapshots.

Groups:
  Group 2 — Feedback & Observation (training log, cost fractions, trajectory)
  Group 3 — Reward Function Manipulation (read / validate / diff)
  Group 4 — Blackboard (shared agent memory)
  Group 5 — Environment Introspection (live EMS config from source file)
"""
from __future__ import annotations

import ast
import json
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from review_evidence import MAX_RESULT_CHARS, query_physical_evidence, register_tool_result


# ─────────────────────────────────────────────────────────────────────────────
# ToolContext — shared mutable state for one run_multi_agent_review call
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ToolContext:
    """Shared live state passed to all tool executions within one review run."""
    log_path: str                        # path to train_log.log
    episode_data_dir: Optional[str]      # path to .mat episode data dir (may be None)
    reward_file: str                     # path to agentEMS_for_feedback.py
    class_name: str                      # "EMS"
    method_name: str                     # "get_reward"
    args: Any                            # argparse.Namespace (soc_low, soc_high, etc.)
    required_info_keys: List[str] = field(default_factory=list)
    blackboard: List[Dict[str, Any]] = field(default_factory=list)  # shared agent memory
    run_dir: Optional[str] = None        # parent of iter_001/, iter_002/, ...
    current_iteration: int = 1           # 1-based index of the current iteration
    evidence_index_path: Optional[str] = None


def _strip_docstrings(node: ast.AST) -> ast.AST:
    for child in ast.walk(node):
        if not isinstance(child, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if not child.body:
            continue
        first = child.body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            child.body = child.body[1:]
    return node


def _executable_method_fingerprint(method_source: str) -> str:
    text = textwrap.dedent(str(method_source or "")).strip()
    if not text:
        return ""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return "\n".join(line.rstrip() for line in text.splitlines()).strip()

    fn_node = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            fn_node = node
            break
        if isinstance(node, ast.ClassDef):
            for sub in node.body:
                if isinstance(sub, ast.FunctionDef):
                    fn_node = sub
                    break
        if fn_node is not None:
            break

    if fn_node is None:
        return "\n".join(line.rstrip() for line in text.splitlines()).strip()

    _strip_docstrings(fn_node)
    return ast.dump(fn_node, annotate_fields=True, include_attributes=False)


# ─────────────────────────────────────────────────────────────────────────────
# Tool schema dicts (Anthropic tool_use format)
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# Per-agent tool sets
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# Tool execution dispatcher
# ─────────────────────────────────────────────────────────────────────────────

def execute_tool(
    tool_name: str,
    tool_input: Dict[str, Any],
    ctx: ToolContext,
    agent_name: str = "unknown",
) -> str:
    """Execute a named tool. Returns a JSON string (result or {\"error\": ...})."""
    try:
        handlers: Dict[str, Any] = {
            "query_physical_evidence": lambda: query_physical_evidence(tool_input, ctx, agent_name),
            "parse_training_log":        lambda: _t_parse_training_log(tool_input, ctx),
            "compute_cost_fractions":    lambda: _t_compute_cost_fractions(tool_input, ctx),
            "get_preference_pair":       lambda: _t_get_preference_pair(tool_input, ctx),
            "get_trajectory_snippet":    lambda: _t_get_trajectory_snippet(tool_input, ctx),
            "read_current_reward":       lambda: _t_read_current_reward(ctx),
            "validate_reward_candidate": lambda: _t_validate_reward_candidate(tool_input, ctx),
            "compute_reward_diff":       lambda: _t_compute_reward_diff(tool_input, ctx),
            "blackboard_post":           lambda: _t_blackboard_post(tool_input, ctx, agent_name),
            "blackboard_read":           lambda: _t_blackboard_read(tool_input, ctx),
            "blackboard_query":          lambda: _t_blackboard_query(tool_input, ctx),
            "query_env_bounds":          lambda: _t_query_env_bounds(ctx),
            "get_iteration_history":     lambda: _t_get_iteration_history(tool_input, ctx),
            "get_debate_history":        lambda: _t_get_debate_history(tool_input, ctx),
        }
        fn = handlers.get(tool_name)
        if fn is None:
            return json.dumps({"error": f"unknown tool '{tool_name}'"})
        # Every result gets a citable query_id (the evidence tool assigns its own).
        return register_tool_result(tool_name, tool_input, fn(), ctx, agent_name)
    except Exception as exc:
        return json.dumps({"error": f"{type(exc).__name__}: {exc}"})


# ─────────────────────────────────────────────────────────────────────────────
# Group 2: Feedback & Observation
# ─────────────────────────────────────────────────────────────────────────────

def _t_parse_training_log(inp: Dict[str, Any], ctx: ToolContext) -> str:
    from feedback_parser import parse_train_log
    n = max(1, min(50, int(inp.get("n_episodes", 20))))
    eps = parse_train_log(ctx.log_path)
    recent = eps[-n:] if len(eps) > n else eps
    rows = []
    for ep in recent:
        rows.append({
            "episode":             ep.episode,
            "h2_100km":            ep.h2_100km,
            "objective_100km":     ep.objective_100km,
            "in_bounds_rate":      ep.in_bounds_rate,
            "mean_h2_cost":        ep.mean_h2_cost,
            "mean_soc_cost":       ep.mean_soc_cost,
            "mean_fcs_cost":       ep.mean_fcs_cost,
            "mean_batt_cost":      ep.mean_batt_cost,
            "mean_objective_cost": ep.mean_objective_cost,
            "soc_min":             ep.soc_min,
            "soc_max":             ep.soc_max,
            "ep_cumulative_r":     ep.ep_cumulative_r,
        })
    return json.dumps({"count": len(rows), "episodes": rows})


def _t_compute_cost_fractions(inp: Dict[str, Any], ctx: ToolContext) -> str:
    from feedback_parser import parse_train_log
    n = max(1, min(50, int(inp.get("n_episodes", 20))))
    eps = parse_train_log(ctx.log_path)
    recent = eps[-n:] if len(eps) > n else eps
    valid = [
        ep for ep in recent
        if (ep.mean_objective_cost or 0.0) > 0
        and ep.mean_h2_cost is not None
        and ep.mean_soc_cost is not None
        and ep.mean_fcs_cost is not None
        and ep.mean_batt_cost is not None
    ]
    if not valid:
        return json.dumps({"error": "no valid episodes with full cost breakdown"})

    def avg(attr: str) -> float:
        return sum(getattr(ep, attr) or 0.0 for ep in valid) / len(valid)

    avg_obj = avg("mean_objective_cost")
    return json.dumps({
        "n_episodes_used":    len(valid),
        "h2_cost_fraction":   avg("mean_h2_cost")  / avg_obj,
        "soc_cost_fraction":  avg("mean_soc_cost")  / avg_obj,
        "fcs_soh_fraction":   avg("mean_fcs_cost")  / avg_obj,
        "batt_soh_fraction":  avg("mean_batt_cost") / avg_obj,
        "avg_objective_cost": avg_obj,
        "avg_h2_100km":       avg("h2_100km") if any(ep.h2_100km is not None for ep in valid) else None,
    }, indent=2)


def _t_get_preference_pair(inp: Dict[str, Any], ctx: ToolContext) -> str:
    from feedback_parser import parse_train_log, select_preference_pair
    floor = float(inp.get("min_in_bounds_rate", 0.9))
    eps = parse_train_log(ctx.log_path)
    preferred, dispreferred, status = select_preference_pair(eps, min_in_bounds_rate=floor)
    if preferred is None:
        return json.dumps({"error": status})

    def ep_dict(ep: Any) -> Dict[str, Any]:
        return {
            "episode_id":      ep.episode,
            "h2_100km":        ep.h2_100km,
            "objective_100km": ep.objective_100km,
            "in_bounds_rate":  ep.in_bounds_rate,
            "ep_cumulative_r": ep.ep_cumulative_r,
        }

    return json.dumps({
        "status":      status,
        "preferred":   ep_dict(preferred),
        "dispreferred": ep_dict(dispreferred),
    }, indent=2)


def _t_get_trajectory_snippet(inp: Dict[str, Any], ctx: ToolContext) -> str:
    from feedback_parser import _summarize_trajectory, parse_train_log
    if not ctx.episode_data_dir:
        return json.dumps({"error": "episode_data_dir not configured"})
    ep_dir = Path(ctx.episode_data_dir)
    episode_id = int(inp["episode_id"])
    role = str(inp.get("role", "episode"))
    mat_path = ep_dir / f"data_ep{episode_id}.mat"
    if not mat_path.exists():
        return json.dumps({"error": f"mat file not found: {mat_path.name}"})
    eps = parse_train_log(ctx.log_path)
    reward_value = next((ep.ep_cumulative_r for ep in eps if ep.episode == episode_id), None)
    soc_low  = float(getattr(ctx.args, "soc_low",  0.4))
    soc_high = float(getattr(ctx.args, "soc_high", 0.8))
    snippet = _summarize_trajectory(episode_id, mat_path, role, reward_value, (soc_low, soc_high))
    return json.dumps({"episode_id": episode_id, "snippet": snippet})


# ─────────────────────────────────────────────────────────────────────────────
# Group 3: Reward Function Manipulation
# ─────────────────────────────────────────────────────────────────────────────

def _t_read_current_reward(ctx: ToolContext) -> str:
    source = Path(ctx.reward_file).read_text(encoding="utf-8")
    tree = ast.parse(source)
    lines = source.splitlines()
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == ctx.class_name:
            for sub in node.body:
                if isinstance(sub, ast.FunctionDef) and sub.name == ctx.method_name:
                    seg = "\n".join(lines[sub.lineno - 1: sub.end_lineno])
                    return json.dumps({
                        "source": textwrap.dedent(seg).strip("\n") + "\n",
                        "file":   ctx.reward_file,
                    })
    return json.dumps({"error": f"{ctx.class_name}.{ctx.method_name} not found", "file": ctx.reward_file})


def _t_validate_reward_candidate(inp: Dict[str, Any], ctx: ToolContext) -> str:
    from reward_patcher import validate_method_source, PatchError
    candidate = str(inp["candidate_source"])
    errors: List[str] = []
    try:
        validate_method_source(
            candidate,
            method_name=ctx.method_name,
            required_info_keys=ctx.required_info_keys,
        )
    except PatchError as exc:
        errors.append(str(exc))
    return json.dumps({"valid": len(errors) == 0, "errors": errors}, indent=2)


def _t_compute_reward_diff(inp: Dict[str, Any], ctx: ToolContext) -> str:
    from reward_patcher import method_diff_preview
    new_src = str(inp["candidate_source"])
    current = json.loads(_t_read_current_reward(ctx))
    if "error" in current:
        return json.dumps({"error": current["error"]})
    diff = method_diff_preview(current["source"], new_src)
    has_executable_changes = (
        _executable_method_fingerprint(current["source"])
        != _executable_method_fingerprint(new_src)
    )
    return json.dumps({
        "diff": diff,
        "has_changes": diff != "(no method changes)",
        "has_executable_changes": has_executable_changes,
        "note": (
            "docstring/comment-only edits are not executable reward changes"
            if not has_executable_changes and diff != "(no method changes)"
            else ""
        ),
    })


# ─────────────────────────────────────────────────────────────────────────────
# Group 4: Blackboard
# ─────────────────────────────────────────────────────────────────────────────

def _t_blackboard_post(inp: Dict[str, Any], ctx: ToolContext, agent_name: str) -> str:
    entry = {"agent": agent_name, "content": inp.get("content", {})}
    ctx.blackboard.append(entry)
    return json.dumps({"posted": True, "entry_index": len(ctx.blackboard) - 1})


def _t_blackboard_read(inp: Dict[str, Any], ctx: ToolContext) -> str:
    agent_filter = inp.get("agent_filter")
    entries = (
        ctx.blackboard if not agent_filter
        else [e for e in ctx.blackboard if e.get("agent") == agent_filter]
    )
    return json.dumps({"count": len(entries), "entries": entries}, indent=2)


def _t_blackboard_query(inp: Dict[str, Any], ctx: ToolContext) -> str:
    flt = inp.get("filter", {})
    results = []
    for entry in ctx.blackboard:
        match = True
        for k, v in flt.items():
            if k == "agent" and entry.get("agent") != v:
                match = False
                break
            if k == "decision":
                content = entry.get("content", {})
                if isinstance(content, dict) and content.get("decision") != v:
                    match = False
                    break
        if match:
            results.append(entry)
    return json.dumps({"count": len(results), "entries": results}, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# Group 5: Environment Introspection
# ─────────────────────────────────────────────────────────────────────────────

def _t_query_env_bounds(ctx: ToolContext) -> str:
    source = Path(ctx.reward_file).read_text(encoding="utf-8")
    tree = ast.parse(source)
    result: Dict[str, Any] = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != ctx.class_name:
            continue
        for sub in node.body:
            if not isinstance(sub, ast.FunctionDef) or sub.name != "__init__":
                continue
            defaults  = sub.args.defaults
            args_list = sub.args.args
            n_def = len(defaults)
            n_arg = len(args_list)
            for i, default in enumerate(defaults):
                arg_name = args_list[n_arg - n_def + i].arg
                if isinstance(default, ast.Constant):
                    result[arg_name] = default.value
                elif isinstance(default, ast.Tuple):
                    vals: List[Any] = []
                    for el in default.elts:
                        if isinstance(el, ast.Constant):
                            vals.append(el.value)
                        elif isinstance(el, ast.UnaryOp) and isinstance(el.op, ast.USub):
                            vals.append(-el.operand.value if isinstance(el.operand, ast.Constant) else None)
                    result[arg_name] = vals
                elif isinstance(default, ast.UnaryOp) and isinstance(default.op, ast.USub):
                    if isinstance(default.operand, ast.Constant):
                        result[arg_name] = -default.operand.value
            break
        break
    result["_note"] = "P_FCS_max / P_batt_max are runtime values from FCHEV_SOH / CellModel1; not in __init__."
    return json.dumps(result, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# Group 6: Cross-Iteration History
# ─────────────────────────────────────────────────────────────────────────────

def _t_get_iteration_history(inp: Dict[str, Any], ctx: ToolContext) -> str:
    if not ctx.run_dir:
        return json.dumps({"error": "run_dir not configured in ToolContext"})
    run_path = Path(ctx.run_dir)
    n = min(int(inp.get("n_iterations", 5)), 20)

    iter_dirs = sorted(
        [d for d in run_path.iterdir() if d.is_dir() and d.name.startswith("iter_")],
        key=lambda d: d.name,
    )
    # Only iterations that completed before the current one
    current_tag = f"iter_{ctx.current_iteration:03d}"
    past_dirs = [d for d in iter_dirs if d.name < current_tag]
    selected = past_dirs[-n:] if len(past_dirs) > n else past_dirs

    records = []
    for idir in selected:
        rec: Dict[str, Any] = {"iteration": idir.name}

        # h2_100km / soc_swing from iteration_summary.json → status_flow POLICY_QUALITY
        summary_path = idir / "iteration_summary.json"
        if summary_path.exists():
            try:
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
                # Validated protocol stores paired physical evidence directly.
                selected_trial = summary.get("selected") or {}
                if selected_trial.get("metrics"):
                    rec["equivalent_g_per_km"] = selected_trial["metrics"].get("fuel_gkm")
                    rec["decision"] = summary.get("decision")
                    rec["full_verdict"] = summary.get("full_verdict")
                    rec["pilot_results"] = summary.get("pilot_results")
                for entry in summary.get("status_flow", []):
                    if entry.get("status") == "POLICY_QUALITY":
                        for part in entry.get("detail", "").split():
                            if part.startswith("h2="):
                                try:
                                    rec["h2_100km"] = float(part[3:])
                                except ValueError:
                                    pass
                            elif part.startswith("swing="):
                                try:
                                    rec["soc_swing"] = float(part[6:])
                                except ValueError:
                                    pass
                        break
            except Exception:
                pass

        # diagnostic: failure mode + trend
        diag_path = idir / "reviews" / "diagnostic_agent.json"
        if diag_path.exists():
            try:
                diag = json.loads(diag_path.read_text(encoding="utf-8"))
                rec["failure_mode"]       = diag.get("failure_mode")
                rec["convergence_quality"] = diag.get("convergence_quality")
                rec["h2_trend_diagnosis"] = diag.get("h2_trend_diagnosis")
                rec["oob_rate"]           = diag.get("oob_rate")
            except Exception:
                pass

        # tradeoff mediator: what was confirmed / blocked
        med_path = idir / "reviews" / "tradeoff_mediator.json"
        if med_path.exists():
            try:
                med = json.loads(med_path.read_text(encoding="utf-8"))
                rec["mediated_priority"] = med.get("mediated_priority")
                rec["confirmed_changes"] = med.get("confirmed_changes")
                rec["blocked_changes"]   = med.get("blocked_changes")
            except Exception:
                pass

        # proposal outcome
        pv_path = idir / "proposal_verification.json"
        if pv_path.exists():
            try:
                pv = json.loads(pv_path.read_text(encoding="utf-8"))
                rec["proposal_passed"] = pv.get("passed")
                rec["best_tpe_delta"]  = pv.get("best_tpe_delta")
            except Exception:
                pass

        records.append(rec)

    return json.dumps({
        "current_iteration": ctx.current_iteration,
        "n_returned": len(records),
        "history": records,
    }, indent=2)


def _t_get_debate_history(inp: Dict[str, Any], ctx: ToolContext) -> str:
    if not ctx.run_dir:
        return json.dumps({"error": "run_dir not configured in ToolContext"})
    run_path = Path(ctx.run_dir)

    iter_num = int(inp.get("iter_num", ctx.current_iteration - 1))
    if iter_num < 1:
        return json.dumps({"error": "no previous iteration available (iter_num < 1)"})
    agent_filter: Optional[str] = inp.get("agent_name")

    idir = run_path / f"iter_{iter_num:03d}"
    if not idir.exists():
        return json.dumps({"error": f"iteration directory not found: {idir.name}"})

    review_dir = idir / "reviews"
    result: Dict[str, Any] = {"iteration": idir.name, "agents": {}}

    # Per-reviewer compact extractions
    _REVIEWER_KEYS: Dict[str, List[str]] = {
        "diagnostic_agent":         ["failure_mode", "convergence_quality", "h2_trend_diagnosis",
                                      "oob_rate", "mean_soc_swing", "best_episode_ratio"],
        "fuel_soc":                 ["decision", "fuel_diagnosis", "charge_sustaining", "buffering_assessment", "soc_adjustment", "joint_assessment"],
        "soc_safety":               ["decision", "risk_flags", "risk_summary"],
        "fuel_efficiency":          ["decision", "h2_trend", "h2_cost_fraction", "battery_buffer_utilized"],
        "reward_hacking":           ["decision", "risk_flags", "risk_summary"],
        "fc_durability":            ["decision", "risk_flags", "risk_summary"],
        "battery_degradation":      ["decision", "batt_degradation_ratio", "batt_cost_trend", "degradation_severity"],
        "tradeoff_mediator":        ["conflict_detected", "mediated_priority", "confirmed_changes",
                                      "blocked_changes", "rationale"],
        "counterfactual_evaluator": ["overall_risk", "must_change_safe", "risk_summary"],
    }
    for agent, keys in _REVIEWER_KEYS.items():
        if agent_filter and agent != agent_filter:
            continue
        fpath = review_dir / f"{agent}.json"
        if not fpath.exists():
            continue
        try:
            data = json.loads(fpath.read_text(encoding="utf-8"))
            compact: Dict[str, Any] = {}
            for k in keys:
                if k in data:
                    v = data[k]
                    if isinstance(v, str) and len(v) > 200:
                        v = v[:197] + "..."
                    compact[k] = v
            result["agents"][agent] = compact
        except Exception as exc:
            result["agents"][agent] = {"error": str(exc)}

    # Orchestrator spec (stored outside reviews/)
    if not agent_filter or agent_filter == "orchestrator":
        orc_path = idir / "orchestrator_spec.json"
        if orc_path.exists():
            try:
                orc = json.loads(orc_path.read_text(encoding="utf-8"))
                compact_orc: Dict[str, Any] = {
                    "overall_decision": orc.get("overall_decision"),
                    "blocking_issues":  orc.get("blocking_issues"),
                }
                spec = orc.get("reward_spec", {})
                if spec:
                    compact_orc["reward_spec_keys"] = (
                        list(spec.keys()) if isinstance(spec, dict) else str(spec)[:120]
                    )
                result["agents"]["orchestrator"] = compact_orc
            except Exception as exc:
                result["agents"]["orchestrator"] = {"error": str(exc)}

    result["n_agents"] = len(result["agents"])
    return json.dumps(result, indent=2)


def bounded_tool_executor(ctx, agent_name):
    """Bound accumulated tool input; retain oversized results as auditable artifacts."""
    consumed = 0
    def run(name, inp):
        nonlocal consumed
        if consumed >= 64000:
            return json.dumps({"error": "Evidence retrieval budget used; conclude from retrieved evidence.",
                               "note": "Unqueried measurements remain unknown."})
        result = execute_tool(name, inp, ctx, agent_name=agent_name)
        if len(result) > MAX_RESULT_CHARS or consumed + len(result) > 64000:
            from uuid import uuid4
            reference = None
            if ctx.run_dir:
                folder = Path(ctx.run_dir) / f"iter_{ctx.current_iteration:03d}" / "tool_results"
                folder.mkdir(parents=True, exist_ok=True)
                path = folder / (uuid4().hex + ".json")
                path.write_text(result, encoding="utf-8")
                reference = str(path)
            try:
                query_id = json.loads(result).get("query_id")
            except (TypeError, ValueError, AttributeError):
                query_id = None
            result = json.dumps({"error": "Tool result too large; narrow the query or reduce n_episodes/limit.",
                                 "full_result": reference, "query_id": query_id})
        consumed += len(result)
        return result
    return run
