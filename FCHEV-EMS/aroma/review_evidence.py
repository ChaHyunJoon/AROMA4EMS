"""Small LLM inputs and bounded, auditable access to deterministic physical evidence.

This presentation layer never changes stored rollouts, training or acceptance gates.
"""
from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

DEFAULT_METRICS = ["soc_initial", "soc_final", "soc_final_minus_target", "fc_hydrogen_g",
                   "battery_equivalent_hydrogen_g", "distance_km", "fc_energy_efficiency",
                   "battery_ohmic_loss_kw_integral_kwh", "battery_throughput_kwh",
                   "fc_load_change_count", "fc_abs_ramp_kw_s_max"]
MAX_RESULT_CHARS = 16000
EVIDENCE_INSTRUCTIONS = (
    "Physical evidence is stored on disk, not embedded here. Use query_physical_evidence "
    "with an evidence_id: catalog lists metric names and representative episodes; summary "
    "returns selected tail metrics; episodes returns selected checkpoint metrics and witness "
    "steps; trajectory returns a bounded sensor slice; reward returns the trained reward; "
    "scenarios returns up to 3 frozen training-cycle validation cases per page. "
    "segments returns original-cycle fixed-checkpoint load/motion groups or contiguous segments; "
    "segment_comparison requires control_evidence_id and returns matched candidate/control deltas. "
    "Use segment_section=groups (default) or segments, and optional segment_id for a witness. "
    "behavior and behavior_comparison expose fixed-window cycling/handoff diagnoses (comparison requires control_evidence_id); "
    "behavior_events exposes individual events. Optional window_id selects a fixed window. "
    "Scenario evidence uses the recorded fixed checkpoint only and is diagnostic: compare the same manifest and "
    "scenario_id, inspect power failures before fuel, and prioritize charge sustaining. "
    "Inspect relevant candidate AND matched control before explaining a physical failure. "
    "Cite evidence_id, episode/step and query_id. Missing evidence is unknown, not zero. "
    "Distinguish measured behavior from hypotheses about its cause."
)
EVIDENCE_TOOL = {
    "name": "query_physical_evidence",
    "description": EVIDENCE_INSTRUCTIONS,
    "input_schema": {
        "type": "object",
        "properties": {
            "evidence_id": {"type": "string"},
            "view": {"type": "string", "enum": ["catalog", "summary", "episodes", "trajectory", "reward", "scenarios", "segments", "segment_comparison", "behavior", "behavior_comparison", "behavior_events"]},
            "control_evidence_id": {"type": "string", "description": "Matched control for segment_comparison or behavior_comparison."},
            "window_id": {"type": "string", "description": "Exact fixed power-behavior window ID."},
            "segment_section": {"type": "string", "enum": ["groups", "segments"]},
            "segment_id": {"type": "string", "description": "Exact contiguous segment witness ID; use segment_section=segments."},
            "metrics": {"type": "array", "items": {"type": "string"}, "maxItems": 12},
            "episode": {"type": "integer", "description": "Checkpoint episode, required for trajectory."},
            "offset": {"type": "integer", "minimum": 0, "description": "Episode-row offset, or trajectory step offset."},
            "limit": {"type": "integer", "minimum": 1, "description": "At most 3 episodes or 40 trajectory steps."},
            "fields": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
        },
        "required": ["evidence_id", "view"],
        "additionalProperties": False,
    },
}


def _brief(trial, evidence_id):
    result = {k: trial.get(k) for k in ("candidate_id", "seed", "episodes", "status", "trained_episodes",
                                       "conditions_id", "learning_rate_config", "scenario_validation", "cycle_segments")}
    result["evidence_id"] = evidence_id
    result["metrics"] = {k: v for k, v in (trial.get("metrics") or {}).items()
                         if k != "physical_evidence"}
    return result


def _registered_path(value, root):
    if not value:
        raise ValueError("Evidence file was not recorded for this trial")
    path = Path(value).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Evidence file is outside the registered run directory")
    return path


def _selected(values, names):
    return {key: values.get(key) for key in names}


def _query(inp, ctx):
    index_path = Path(ctx.evidence_index_path)
    index = json.loads(index_path.read_text(encoding="utf-8"))
    evidence_id = inp.get("evidence_id")
    trial = index["trials"].get(evidence_id)
    if trial is None and evidence_id == "proposal":
        return {"error": "proposal is an untrained candidate and has no physical evidence. Its source is in "
                         "the prompt; its fuel/SOC/degradation outcomes are unknown until pilot/full training.",
                "evidence_id": "proposal", "status": "untrained"}
    if trial is None:
        return {"error": "Unknown evidence_id", "available_ids": list(index["trials"])}
    metrics = inp.get("metrics", DEFAULT_METRICS)
    if not isinstance(metrics, list) or len(metrics) > 12 or any(not isinstance(k, str) for k in metrics):
        raise ValueError("metrics must contain at most 12 metric names")
    root = Path(ctx.run_dir).resolve()
    result = _brief(trial, evidence_id)
    facts = index.get("experiment_facts") or {}
    if evidence_id in facts.get("trials", {}):
        result["recorded_settings"] = facts["trials"][evidence_id]["settings"]
        result["physical_assessment"] = facts["trials"][evidence_id].get("physical_assessment", {})
        result["comparison_pairs"] = {k: v for k, v in facts.get("pairs", {}).items()
                                      if evidence_id in (v["candidate_evidence_id"], v["control_evidence_id"])}
    result["source"] = trial.get("physical_evidence_path")
    physical = (trial.get("metrics") or {}).get("physical_evidence") or {}
    view = inp.get("view", "summary")
    if view == "catalog":
        result.update(available_metrics=sorted(physical.get("scalars", {})),
                      evaluated_tail_episodes=physical.get("episodes", []),
                      representative_episodes={k: v.get("episode") for k, v in
                                               physical.get("representative_rollouts", {}).items()})
        # These are field names only, never the full trajectory.
        directory = trial.get("trajectory_dir")
        if directory:
            import numpy as np
            paths = sorted(_registered_path(directory, root).glob("episode_*.npz"))
            if paths:
                with np.load(_registered_path(paths[0], root), allow_pickle=False) as data:
                    result["trajectory_fields"] = data.files
    elif view == "summary":
        result.update(basis=physical.get("basis"), evaluated_tail_episodes=physical.get("episodes", []),
                      scalars=_selected(physical.get("scalars", {}), metrics),
                      missing_sensors=physical.get("missing_sensors", []),
                      learning_rate_config=trial.get("learning_rate_config"))
    elif view == "scenarios":
        registered = trial.get("scenario_validation")
        if not registered:
            return {"error": "No fixed-checkpoint scenario validation recorded for this trial", "evidence_id": evidence_id}
        path = _registered_path(registered["result_path"], root)
        report = json.loads(path.read_text(encoding="utf-8"))
        if any(report.get(k) != registered.get(k) for k in ("manifest_hash", "actor_hash", "checkpoint_episode")):
            raise ValueError("Scenario evidence identity mismatch")
        offset = max(0, int(inp.get("offset", 0)))
        limit = min(3, max(1, int(inp.get("limit", 3))))
        rows = report["results"][offset:offset + limit]
        result.update(source=str(path), basis="fixed-checkpoint training-cycle scenarios; diagnostic only",
                      rows=rows, total=len(report["results"]),
                      next_offset=offset + len(rows) if offset + len(rows) < len(report["results"]) else None)
    elif view in ("segments", "segment_comparison", "behavior", "behavior_comparison", "behavior_events"):
        from cycle_segments import compare_reports
        from scenario_validation import file_hash

        def segment_report(registered_trial):
            registered = registered_trial.get("cycle_segments")
            if not registered:
                raise ValueError("No original-cycle fixed-checkpoint segmentation recorded for this trial")
            path = _registered_path(registered["result_path"], root)
            report = json.loads(path.read_text())
            if any(report.get(k) != registered.get(k) for k in
                   ("manifest_hash", "actor_hash", "trajectory_hash", "checkpoint_episode")):
                raise ValueError("Segment evidence identity mismatch")
            for key in ("seed", "conditions_id"):
                if report.get(key) != registered_trial.get(key):
                    raise ValueError("Segment evidence trial mismatch")
            trajectory = _registered_path(report["trajectory_path"], root)
            if file_hash(trajectory) != registered["trajectory_hash"]:
                raise ValueError("Segment trajectory changed")
            return report

        report = segment_report(trial)
        if view in ("segment_comparison", "behavior_comparison"):
            control_id = inp.get("control_evidence_id")
            if control_id not in index["trials"]:
                raise ValueError("comparison requires a registered control_evidence_id")
            control_report = segment_report(index["trials"][control_id])
            result.update(control_evidence_id=control_id, control_source=control_report["result_path"])
            measured = compare_reports(report, control_report)
            result.update(regression_witnesses=measured["regression_witnesses"], comparison_note=measured["note"])
        else:
            measured = report
        behavior_view = view.startswith("behavior")
        if behavior_view:
            behavior = measured.get("power_behavior")
            if not behavior:
                raise ValueError("No power-behavior diagnostics recorded; legacy segment evidence is unknown")
            section = "events" if view == "behavior_events" else "windows"
            rows = behavior[section]
            if "window_id" in inp:
                valid_ids = {w["window_id"] for w in report["power_behavior"]["windows"]}
                if inp["window_id"] not in valid_ids:
                    raise ValueError("Unknown behavior window_id")
                rows = [r for r in rows if r["window_id"] == inp["window_id"]]
            result.update(behavior_rules=behavior["rules"], behavior_summary=behavior["summary"],
                          suspect_windows=behavior.get("suspect_windows", []),
                          behavior_note=behavior.get("note", "Events may overlap; never sum witness energies."))
            # Keep this event-focused view bounded without repeating unrelated summaries.
            result.pop("regression_witnesses", None)
            result.pop("metrics", None)
            result.pop("cycle_segments", None)
            result.pop("scenario_validation", None)
        else:
            section = inp.get("segment_section", "groups")
            if section not in ("groups", "segments"):
                raise ValueError("segment_section must be groups or segments")
            rows = measured[section]
        if "segment_id" in inp:
            if section != "segments":
                raise ValueError("segment_id requires segment_section=segments")
            rows = [r for r in rows if r["segment_id"] == inp["segment_id"]]
            if not rows:
                raise ValueError("Unknown segment_id")
        offset, limit = max(0, int(inp.get("offset", 0))), min(3, max(1, int(inp.get("limit", 3))))
        page = rows[offset:offset + limit]
        result.update(source=report["result_path"], basis="original training cycle, recorded fixed checkpoint, diagnostic_only",
                      accounting=report["accounting"], whole_cycle=measured["whole_cycle"],
                      missing_sensors=report["missing_sensors"], section=section, rows=page, total=len(rows),
                      next_offset=offset + len(page) if offset + len(page) < len(rows) else None)
        if behavior_view:
            # Whole-cycle power failures must remain visible on every page.
            keys = ("power_feasible", "unserved_energy_kwh", "unaccepted_energy_kwh", "equivalent_hydrogen_g", "mean_target_error")
            whole = measured["whole_cycle"]
            result["whole_cycle"] = ({side: _selected(whole[side], keys) for side in ("candidate", "control")}
                                     if view == "behavior_comparison" else _selected(whole, keys))
        # Real-valued physics rows are substantially larger than synthetic fixtures.
        # Shrink the page without dropping the whole-cycle failures or pair identity.
        while len(page) > 1 and len(json.dumps(result, ensure_ascii=False)) > MAX_RESULT_CHARS - 128:
            page.pop()
            result["next_offset"] = offset + len(page)
    elif view == "reward":
        source = trial.get("reward_source")
        if not source and trial.get("physical_evidence_path"):
            # TrialEvaluator's sibling result includes the exact bound reward.
            path = _registered_path(trial["physical_evidence_path"], root).parent / "trial_result.json"
            if path.exists():
                source = json.loads(_registered_path(path, root).read_text()).get("reward_source")
        result["reward_source"] = source
        if source is None:
            result["unavailable"] = "Trained reward source not recorded in index/trial_result.json"
    elif view in ("episodes", "trajectory"):
        path = _registered_path(trial.get("evaluation_evidence"), root)
        with path.open(encoding="utf-8") as stream:
            rows = [json.loads(line) for line in stream if line.strip()]
        result["source"] = str(path)
        if "episode" in inp:
            rows = [row for row in rows if row["episode"] == int(inp["episode"])]
            if not rows:
                raise ValueError("Requested episode was not evaluated for this evidence_id")
        offset = max(0, int(inp.get("offset", 0)))
        if view == "episodes":
            limit = max(1, min(3, int(inp.get("limit", 1))))
            result["total_rows"] = len(rows)
            result["next_offset"] = offset + limit if offset + limit < len(rows) else None
            result["rows"] = []
            for row in rows[offset:offset + limit]:
                physics = row.get("physical_evidence") or {}
                out = {k: v for k, v in row.items() if k not in ("physical_evidence", "paper_fuel")}
                out.update(scalars=_selected(physics.get("scalars", {}), metrics),
                           witness_steps=physics.get("witness_steps", []),
                           missing_sensors=physics.get("missing_sensors", []),
                           dominant_fc_degradation=physics.get("dominant_fc_degradation"),
                           count_definition=physics.get("count_definition"))
                result["rows"].append(out)
        else:
            if "episode" not in inp:
                raise ValueError("trajectory requires an episode from catalog/episodes")
            import numpy as np
            fields = inp.get("fields", ["SOC", "P_fc", "P_batt_req", "policy_action"])
            if not isinstance(fields, list) or len(fields) > 8 or any(not isinstance(k, str) for k in fields):
                raise ValueError("fields must contain at most 8 sensor names")
            path = _registered_path(rows[0].get("trajectory_path"), root)
            limit = max(1, min(40, int(inp.get("limit", 20))))
            with np.load(path, allow_pickle=False) as data:
                result.update(source=str(path), episode=int(inp["episode"]), step_offset=offset,
                              dt_s=float(data["dt_s"]), fields={}, missing_fields=[])
                lengths = []
                for key in fields:
                    if key not in data:
                        result["missing_fields"].append(key)
                        continue
                    arr = data[key]
                    if arr.ndim == 0:
                        result["fields"][key] = arr.item()
                    elif arr.ndim == 1:
                        result["fields"][key] = arr[offset:offset + limit].tolist()
                        lengths.append(len(arr))
                    else:
                        raise ValueError("Only scalar/one-dimensional sensors are supported")
                result["next_offset"] = offset + limit if lengths and offset + limit < max(lengths) else None
            result["units"] = {"SOC": "fraction", "P_fc": "kW", "P_batt_req": "kW",
                               "I": "A", "policy_action": "normalized action", "speed_m_s": "m/s"}
    else:
        raise ValueError("Unknown evidence view")
    return result


def query_physical_evidence(inp, ctx, agent_name):
    query_id = uuid4().hex[:12]
    try:
        result = _query(inp, ctx)
    except Exception as exc:
        result = {"error": f"{type(exc).__name__}: {exc}"}
    result["query_id"] = query_id
    result = json.loads(json.dumps(result, default=str))
    if ctx.evidence_index_path:
        audit = Path(ctx.evidence_index_path).parent / "evidence_queries.jsonl"
        with audit.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"query_id": query_id, "agent": agent_name,
                                     "request": inp, "result": result}, ensure_ascii=False) + "\n")
    encoded = json.dumps(result, ensure_ascii=False)
    if len(encoded) > MAX_RESULT_CHARS:
        return json.dumps({"query_id": query_id, "error": "Result too large; request fewer metrics, fields or rows.",
                           "full_result": str(audit)})
    return encoded


def register_tool_result(tool_name, inp, encoded, ctx, agent_name):
    """Give any other tool result a citable query_id in the same audited log as evidence queries."""
    if not getattr(ctx, "evidence_index_path", None):
        return encoded
    try:
        result = json.loads(encoded)
    except (TypeError, ValueError):
        return encoded
    if not isinstance(result, dict) or "query_id" in result:
        return encoded
    result["query_id"] = uuid4().hex[:12]
    result.setdefault("evidence_basis", f"tool {tool_name}: training-log/feedback files of the reviewed chunk")
    audit = Path(ctx.evidence_index_path).parent / "evidence_queries.jsonl"
    with audit.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"query_id": result["query_id"], "agent": agent_name, "tool": tool_name,
                                 "request": inp, "result": result}, ensure_ascii=False, default=str) + "\n")
    return json.dumps(result, ensure_ascii=False, default=str)


class EvidenceClient:
    """Give existing candidate-generation/review calls the same retrieval interface.

    Keeping this adapter in the presentation layer preserves evaluator cache identities.
    """
    def __init__(self, client, ctx, stage="candidate"):
        self.client, self.ctx, self.stage = client, ctx, stage
        self.provider, self.model = client.provider, client.model

    def for_stage(self, stage):
        return EvidenceClient(self.client, self.ctx, stage)

    def complete_with_usage(self, **kwargs):
        from ems_tools import bounded_tool_executor
        return self.client.complete_with_tools(
            **kwargs, tools=[EVIDENCE_TOOL],
            tool_executor=bounded_tool_executor(self.ctx, self.stage))
