"""Baseline -> candidate experiments -> paired confirmation, with resumable artifacts.

An iteration is a completed experiment, not a patch awaiting future training.
New trials use matched fresh SAC initializations, optimizers and empty buffers.
An explicitly supplied historical baseline reuses actors through evaluation only.
No candidate is installed in the user's reward file until final confirmation.
"""
from __future__ import annotations

import copy
import ast
import hashlib
import json
import math
import random
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np

from candidate_validation import (CONTRACT_VERSION, bind_reward, candidate_id,
                                  verify_candidate, REQUIRED_KEYS)
from feedback_parser import DETERMINISTIC_FUEL_BASIS
from prompt_builder import extract_method_source
from reward_patcher import ensure_logging_contract
from policy_evidence import summarize_physics
from adoption_validation import build_policy

PROTOCOL_VERSION = "paired_baseline_refinement_v1"
LR_KEYS = ("lr_critic", "lr_critic_min", "lr_actor", "lr_actor_min", "lr_alpha", "lr_alpha_min",
           "lr_schedule_episodes", "lr_restart_cycles", "lr_warmup_ratio", "const_lr", "auto_lr_on_reward_patch")
_CONTROL_ARGS = {
    "resume_run_root", "resume_additional_iterations", "resume_use_saved_config",
    "ldri_iterations", "llm_api_key", "skip_llm", "skip_patch", "file_v", "ldri_root",
    "llm_provider", "llm_model", "llm_api_key_env", "llm_temperature", "llm_max_tokens",
    "llm_timeout_sec", "agent_type",
    "seed_chunk_dir", "seed_reward_file",
}


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    tmp.replace(path)


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def aggregate_evaluations(records, *, total_episodes=None):
    if not records:
        raise ValueError("No deterministic evaluation evidence")
    tail = records[-max(1, (total_episodes or len(records)) // 10):]
    keys = ("fuel_gkm", "soc_in_bounds", "fc_loss", "batt_loss", "soc_min", "soc_max")
    if any(not math.isfinite(float(row[k])) for row in tail for k in keys):
        raise ValueError("Incomplete/non-finite physical evidence")
    split = max(1, len(tail) // 2)
    return {
        "fuel_gkm": float(np.mean([r["fuel_gkm"] for r in tail])),
        "fuel_early_tail_gkm": float(np.mean([r["fuel_gkm"] for r in tail[:split]])),
        "fuel_late_tail_gkm": float(np.mean([r["fuel_gkm"] for r in tail[split:] or tail])),
        "min_in_bounds": min(r["soc_in_bounds"] for r in tail),
        "fc_loss": float(np.mean([r["fc_loss"] for r in tail])),
        "batt_loss": float(np.mean([r["batt_loss"] for r in tail])),
        "soc_min": min(r["soc_min"] for r in tail),
        "soc_max": max(r["soc_max"] for r in tail),
        "tail_episodes": [r["episode"] for r in tail],
        "fuel_metric_basis": DETERMINISTIC_FUEL_BASIS,
        "physical_evidence": summarize_physics(tail),
    }


class TrialEvaluator:
    def __init__(self, args, run_root, api, manifest):
        self.args, self.root, self.api, self.manifest = args, Path(run_root), api, manifest
        self.conditions_id = _digest(manifest)

    def __call__(self, source, episodes, seed):
        imported = self.manifest.get("imported_baseline")
        reuse_baseline = bool(imported and seed == self.args.seed and candidate_id(source) == imported["candidate_id"])
        identity = {"candidate_id": candidate_id(source), "episodes": int(episodes), "seed": int(seed),
                    "conditions_id": self.conditions_id, "contract_version": CONTRACT_VERSION}
        trial_dir = self.root / "trials" / _digest(identity)[:24]
        result_path = trial_dir / "trial_result.json"
        if result_path.exists():
            cached = json.loads(result_path.read_text())
            if cached.get("identity") == identity and cached.get("status") == "complete":
                chunk = cached["chunk"]
                actor = Path(chunk["model_dir"]) / f"actor_iter001_ep{chunk['end_episode']}.pkl"
                if not actor.exists() or not Path(chunk["log_path"]).exists():
                    raise RuntimeError(f"Cached trial artifacts are missing: {trial_dir}")
                print(f"[trial cache] {identity['candidate_id'][:12]} seed={seed} episodes={episodes}")
                return cached
        trial_dir.mkdir(parents=True, exist_ok=True)
        (trial_dir / "reward.py").write_text(source, encoding="utf-8")
        verification = verify_candidate(source, self.args)
        if verification["status"] != "pass":
            result = {**identity, "identity": identity, "status": "invalid", "verification": verification}
            write_json(result_path, result)
            return result
        from env_ldri import make_env_ldri
        from runner_ldri import RunnerLDRI, ChunkResult
        args = copy.deepcopy(self.args)
        args.seed, args.random_seed = int(seed), False
        args.load_or_not, args.evaluate = False, False
        args.start_episode = 0
        # Fix the LR schedule horizon across pilots and full runs. Each candidate
        # receives exactly the same scheduler and no reward-specific LR tuning.
        args.lr_schedule_episodes = int(args.lr_schedule_episodes) if args.lr_schedule_episodes > 0 else int(args.chunk_episodes)
        args.auto_lr_on_reward_patch = False
        self.api._configure_training_paths(args, trial_dir)
        random.seed(seed)
        np.random.seed(seed)
        env, args = make_env_ldri(args, force_reload_agent=True)
        import inspect
        if Path(inspect.getfile(type(env.agent))).resolve() != Path(args.reward_file).resolve():
            raise RuntimeError("reward_module and reward_file refer to different physics implementations")
        bind_reward(env, source)
        runner = RunnerLDRI(args, env, trial_dir)
        records = []
        evidence_path = trial_dir / "deterministic_evaluations.jsonl"
        trajectory_dir = trial_dir / "deterministic_rollouts"
        trajectory_dir.mkdir(exist_ok=True)
        compact = (getattr(args, "refinement_protocol", "") == "sequential"
                   and getattr(args, "artifact_detail", "compact") == "compact")
        with evidence_path.open("w", encoding="utf-8") as stream:
            def collect(episode, m):
                if int(m["ep_len"]) != int(args.episode_steps) or m["travel"] <= 0 or not m.get("tracking_success", True):
                    # Keep one row per episode so the tail window stays aligned;
                    # aggregate_evaluations rejects a non-finite row inside the tail.
                    nan = float("nan")
                    row = {"episode": int(episode), "fuel_gkm": nan, "soc_in_bounds": nan, "soc_min": nan,
                           "soc_max": nan, "fc_loss": nan, "batt_loss": nan, "incomplete_drive": True,
                           "ep_len": int(m["ep_len"]), "failure_reason": m.get("failure_reason", ""),
                           "power_violations": m.get("power_violations")}
                    stream.write(json.dumps({k: (None if v != v else v) for k, v in row.items()}) + "\n")
                    stream.flush()
                    records.append(row)
                    return
                row = {"episode": int(episode), "fuel_gkm": float(m["paper_fuel"]["equivalent_g_per_km"]),
                       "soc_in_bounds": float(m["soc_in_bounds_rate"]), "soc_min": float(m["soc_min"]),
                       "soc_max": float(m["soc_max"]), "fc_loss": float(1 - m["fcs_soh"]),
                       "batt_loss": float(1 - m["bat_soh"]), "power_violations": m.get("power_violations")}
                trajectory_path = trajectory_dir / f"episode_{episode:05d}.npz"
                m["physical_evidence"]["scalars"].update(
                    fc_energy_efficiency=float(m["paper_fuel"]["fc_efficiency"]),
                    battery_equivalent_hydrogen_g=float(m["paper_fuel"]["batt_eq_h2_g"]),
                    distance_km=float(m["travel"]), fc_soh_final=float(m["fcs_soh"]),
                    battery_soh_final=float(m["bat_soh"]))
                retain_raw = not compact or episode == episodes - 1
                if retain_raw:
                    np.savez_compressed(trajectory_path, **runner.last_validation_rollout,
                                        dt_s=float(env.agent.FCHEV.simtime), soc_initial=float(args.soc0))
                row.update(physical_evidence=m["physical_evidence"], paper_fuel=m["paper_fuel"],
                           trajectory_path=str(trajectory_path) if retain_raw else None,
                           checkpoint_path=str(Path(chunk.model_dir if reuse_baseline else runner.SAC_agent.model_path)
                                               / f"actor_iter001_ep{episode}.pkl") if retain_raw or reuse_baseline else None)
                stream.write(json.dumps(row, allow_nan=False) + "\n")
                stream.flush()
                records.append(row)
            runner.validation_eval_hook = collect
            try:
                if reuse_baseline:
                    import torch
                    chunk = self.api._seed_iteration_from_existing_run(trial_dir, args, 1, ChunkResult)
                    chunk = replace(chunk, start_episode=0, end_episode=episodes - 1)
                    print(f"[baseline reuse] seed={seed}, saved budget={episodes}; evaluation only, no training")
                    with open(chunk.log_path, "a", encoding="utf-8") as log_file:
                        for episode in range(episodes - max(1, episodes // 10), episodes):
                            actor_path = Path(chunk.model_dir) / f"actor_iter001_ep{episode}.pkl"
                            runner.SAC_agent.actor.load_state_dict(torch.load(actor_path, map_location="cpu", weights_only=True))
                            runner.SAC_agent.actor.eval()
                            metrics = runner._evaluate_policy_sac()
                            collect(episode, metrics)
                            runner._log_deterministic_fuel(log_file, episode, metrics)
                else:
                    chunk = runner.train_chunk(iteration=1, chunk_episodes=episodes)
                result = {**identity, "identity": identity, "status": "complete", "chunk": asdict(chunk),
                          "metrics": self._tail_metrics(records, episodes), "reward_source": source,
                          # An incomplete final drive carries NaN placeholders; store them as null like the jsonl.
                          "final_metrics": {**{k: (None if isinstance(v, float) and v != v else v)
                                               for k, v in records[-1].items()},
                                            "fuel_metric_basis": DETERMINISTIC_FUEL_BASIS},
                          "evaluation_evidence": str(evidence_path),
                          "trajectory_dir": str(trajectory_dir),
                          "physical_evidence_path": str(trial_dir / "physical_evidence.json"),
                          "learning_rate_config": {key: getattr(args, key) for key in LR_KEYS},
                          "trained_episodes": 0 if reuse_baseline else len(records),
                          "evaluated_checkpoints": len(records),
                          "policy_quality": self.api._compute_policy_quality_score(chunk.log_path, args)}
                if reuse_baseline:
                    result["baseline_provenance"] = imported
                    result["learning_rate_config"] = imported.get("learning_rate_config", {})
                write_json(trial_dir / "physical_evidence.json", {
                    "identity": identity, "basis": "deterministic_rollouts",
                    "tail": result["metrics"]["physical_evidence"],
                    "windows": [summarize_physics(records[i:i + 10]) for i in range(0, len(records), 10)],
                    "evaluation_evidence": str(evidence_path), "trajectory_dir": str(trajectory_dir),
                    "trajectory_units": {"P_fc": "kW", "P_batt_req": "kW", "I": "A", "SOC": "fraction",
                                         "policy_action": "normalized action", "speed_m_s": "m/s", "dt_s": "s"}})
            except (ValueError, ArithmeticError, KeyError, AttributeError) as exc:
                result = {**identity, "identity": identity, "status": "invalid", "error": repr(exc),
                          "trained_episodes": 0 if reuse_baseline else len(records),
                          "evaluation_evidence": str(evidence_path)}
        write_json(result_path, result)
        return result

    def _tail_metrics(self, records, episodes):
        """Sequential judges the ep399 actor alone; its ep360-399 tail is a diagnostic.

        A failed tail row must not invalidate a valid ep399 (it is counted, never dropped
        silently). The validated protocol keeps requiring a fully valid tail.
        """
        if getattr(self.args, "refinement_protocol", "") != "sequential" or not records:
            return aggregate_evaluations(records, total_episodes=episodes)
        try:
            return aggregate_evaluations(records, total_episodes=episodes)
        except ValueError as exc:
            tail = records[-max(1, episodes // 10):]
            failed = [r["episode"] for r in tail if r.get("incomplete_drive")
                      or not all(math.isfinite(float(r.get(k, float("nan"))))
                                 for k in ("fuel_gkm", "soc_in_bounds", "fc_loss", "batt_loss"))]
            return {"tail_status": "contains_invalid_rows", "tail_error": str(exc),
                    "tail_episodes": [r["episode"] for r in tail], "tail_failed_episodes": failed,
                    "fuel_metric_basis": DETERMINISTIC_FUEL_BASIS, "physical_evidence": summarize_physics(tail)}


def _manifest(args):
    root = Path(__file__).resolve().parent
    # Pin physics, learner and evaluator implementations for resumed/cached comparisons.
    files = list((root.parent / "common").glob("*.py"))
    files += [root.parent / name for name in ("sac.py", "FCHEV_SOH.py", "Battery.py", "power_constraints.py")]
    files += [root / name for name in ("runner_ldri.py", "env_ldri.py", "candidate_validation.py", "validated_workflow.py", "baseline_import.py", "policy_evidence.py", "scenario_validation.py", "cycle_segments.py", "power_behavior.py", "adoption_validation.py")]
    files.append(root / "training_initial_states.py")
    files.append(root / "env_physics_facts.py")
    data_root = root.parent.parent / "project-data"
    cycle = data_root / "standard_driving_cycles" / "mat-data" / f"{args.scenario_name}.mat"
    files.append(cycle)
    for folder in ("FCHEV_data", "Battery_data"):
        files.extend(p for p in (data_root / folder).glob("*") if p.is_file())
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.exists()}
    # Installation changes only EMS.get_reward; pin every other part of the plant.
    tree = ast.parse(Path(args.reward_file).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "EMS":
            node.body = [n for n in node.body if not isinstance(n, ast.FunctionDef) or n.name != "get_reward"]
    hashes[str(Path(args.reward_file))] = _digest(ast.dump(tree, include_attributes=False))
    config = {k: v for k, v in vars(args).items() if k not in _CONTROL_ARGS
              and k not in {"save_dir", "log_dir", "eva_dir"}}
    manifest = {"protocol_version": PROTOCOL_VERSION, "conditions": config, "source_hashes": hashes,
                "fuel_metric_basis": DETERMINISTIC_FUEL_BASIS, "adoption_policy": build_policy(args)}
    if args.seed_chunk_dir:
        from baseline_import import inspect_baseline
        imported = inspect_baseline(args)
        source = ensure_logging_contract(extract_method_source(args.seed_reward_file, "EMS", "get_reward"), REQUIRED_KEYS)
        imported["candidate_id"] = candidate_id(source)
        manifest["imported_baseline"] = imported
    return manifest
