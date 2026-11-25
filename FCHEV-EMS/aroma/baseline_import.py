"""Inspect historical SAC artifacts before evaluation-only reuse (never train)."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


def inspect_learning_rates(config, text, args):
    """Reject known LR mismatches; keep unknown historical metadata explicit."""
    saved = {}
    for part in ("critic", "actor", "alpha"):
        match = re.search(rf"^{part} warmup-restart cosine learning rate:\s*(\S+)\s*->\s*(\S+)", text, re.M)
        for key, pos in ((f"lr_{part}", 1), (f"lr_{part}_min", 2)):
            if key in config:
                saved[key] = float(config[key])
            elif match:
                saved[key] = float(match[pos])
    for key, pattern in (("lr_restart_cycles", r"^lr warmup-restart cycles:\s*([\d.]+)"),
                         ("lr_warmup_ratio", r"^lr warmup ratio:\s*([\d.]+)")):
        match = re.search(pattern, text, re.M)
        if key in config or match:
            saved[key] = float(config[key]) if key in config else float(match[1])
    horizon = config.get("lr_schedule_episodes", 0)
    if not horizon:
        match = re.search(r"^max_episodes:\s*(\d+)", text, re.M)
        horizon = config.get("chunk_episodes") or config.get("max_episodes") or (int(match[1]) if match else None)
    if horizon:
        saved["lr_schedule_episodes"] = int(horizon)
    if "const_lr" in config:
        saved["const_lr"] = bool(config["const_lr"])
    elif "warmup-restart cosine learning rate:" in text:
        saved["const_lr"] = False
    for key, value in saved.items():
        requested = getattr(args, key)
        if key == "lr_schedule_episodes" and requested <= 0:
            requested = args.chunk_episodes
        if value != requested:
            raise ValueError(f"Baseline learning-rate mismatch: {key} saved={value}, requested={requested}. "
                             "Use matching settings or omit --seed_chunk_dir to train a fresh control.")
    return saved


def inspect_baseline(args):
    root = Path(args.seed_chunk_dir).expanduser().resolve()
    log = root / "train_log.log"
    if not log.is_file() or not (root / "episode_data").is_dir():
        raise ValueError(f"Baseline requires train_log.log and episode_data/: {root}")
    text = log.read_text(encoding="utf-8", errors="replace")
    config_path = root / "run_config.json"
    config = json.loads(config_path.read_text()) if config_path.exists() else {}
    if getattr(args, "search_plan", "archive") == "fuel_diagnostics_v1":
        for key in ("obs_norm", "obs_speed_scale", "obs_acc_scale", "unserved_cost_per_kw", "obs_timing"):
            if key not in config or config[key] != getattr(args, key):
                raise ValueError(f"Baseline training condition missing/mismatched: {key}. "
                                 "Omit --seed_chunk_dir to train a fresh matched baseline.")
    learning_rates = inspect_learning_rates(config, text, args)
    seed_match = re.search(r"Random seeds have been set to (\d+)", text)
    recorded_seed = config.get("seed", int(seed_match[1]) if seed_match else None)
    if recorded_seed != args.seed:
        raise ValueError(f"Baseline seed mismatch/missing: saved={recorded_seed}, requested={args.seed}")
    cycle_match = re.search(r"^cycle name:\s*(\S+)", text, re.M)
    cycle = config.get("scenario_name", cycle_match[1] if cycle_match else None)
    if cycle != args.scenario_name and not (cycle or "").startswith(args.scenario_name + "_"):
        raise ValueError(f"Baseline cycle mismatch/missing: {cycle}")
    for key, pattern, convert in (
        ("soc0", r"^initial SOC:\s*(\S+)", float),
        ("MODE", r"^SOC-MODE:\s*(\S+)", str),
    ):
        match = re.search(pattern, text, re.M)
        saved = config.get(key, convert(match[1]) if match else None)
        if saved is None or saved != getattr(args, key):
            raise ValueError(f"Baseline {key} mismatch/missing: {saved}")
    # Old runs encode these in their directory name rather than a JSON config.
    for key, pattern in (("w_soc", r"_w([\d.]+)(?:_|$)"),
                         ("ramp_limit_kw", r"_dR([\d.]+)(?:_|$)")):
        match = re.search(pattern, root.name)
        saved = config.get(key, float(match[1]) if match else None)
        if saved is not None and saved != getattr(args, key):
            raise ValueError(f"Baseline {key} mismatch: saved={saved}, requested={getattr(args, key)}")
    for key in ("policy", "critic_layernorm", "actor_layernorm", "soc_target", "soc_low", "soc_high"):
        if key in config and config[key] != getattr(args, key):
            raise ValueError(f"Baseline {key} mismatch: {config[key]}")
    logged_episodes = {int(n) for n in re.findall(r"^epi\s+(\d+):", text, re.M)}
    if not set(range(args.chunk_episodes)).issubset(logged_episodes):
        raise ValueError(f"Baseline does not contain {args.chunk_episodes} completed training episodes")
    selected = set()
    budgets = ((args.chunk_episodes,) if getattr(args, "refinement_protocol", "") == "sequential"
               else (args.pilot_episodes, args.chunk_episodes))
    for budget in budgets:
        selected.update(range(budget - max(1, budget // 10), budget))
    paths = [log, Path(args.seed_reward_file)]
    if config_path.exists():
        paths.append(config_path)
    for episode in sorted(selected):
        path = root / "net_params" / f"actor_params_ep{episode}.pkl"
        if not path.is_file():
            raise ValueError(f"Baseline checkpoint missing (no automatic retraining): {path}")
        paths.append(path)
    return {
        "source_dir": str(root), "seed": recorded_seed, "scenario_name": args.scenario_name,
        "checkpoint_episodes": sorted(selected),
        "hashes": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        "comparison_basis": "historical_baseline_reevaluated_in_current_environment",
        "training_config_fully_verified": False,
        "learning_rate_config": learning_rates,
        "note": "Saved actors are evaluated without training. Historical optimizer/RNG/physics provenance is not fully verified; this is not an identical-training claim.",
    }
