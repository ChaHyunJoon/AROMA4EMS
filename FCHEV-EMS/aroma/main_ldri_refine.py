import json
import re
import sys
from pathlib import Path
import datetime as dt
from typing import Any, Dict

from arguments_ldri import get_ldri_args

from feedback_parser import DETERMINISTIC_FUEL_BASIS
from llm_client import LLMClient, get_api_key


RESUME_RESTORE_KEYS = [
    "search_plan", "development_cycles", "development_max_regression",
    "proposal_attempts", "artifact_detail", "cost_scale_max_ratio",
    "confirmation_seed_list", "edit_base_max_stale", "cost_max_fuel_increase", "cost_max_batt_increase", "cost_max_soc_drift", "reward_term_catalog",
    "failure_cost_per_step", "unserved_cost_per_kw", "obs_norm", "obs_speed_scale", "obs_acc_scale",
    "obs_timing", "training_initial_states",
    "refinement_protocol", "scenario_validation", "cycle_segment_validation", "baseline_reward_file", "candidate_pool_size", "candidate_attempts",
    "seed_chunk_dir", "seed_reward_file",
    "pilot_episodes", "unreviewed_candidate_policy", "confirmation_seeds", "validation_min_improvement_gkm",
    "validation_min_improvement_fraction", "validation_terminal_soc_error",
    "validation_scenario_soc_error", "validation_unaccepted_energy_kwh",
    "validation_unaccepted_peak_kw", "validation_unaccepted_peak_slack_kw",
    "validation_unaccepted_energy_slack_kwh",
    "validation_condition_soc_tolerance", "validation_condition_fuel_regression",
    "validation_max_degradation_ratio", "validation_min_in_bounds",
    "DRL",
    "scenario_name",
    "MODE",
    "soc0",
    "soc_target",
    "w_soc",
    "w_h2",
    "w_fc",
    "w_batt",
    "eq_h2_batt_coef",
    "random_seed",
    "seed",
    "lr_critic",
    "lr_critic_min",
    "lr_actor",
    "lr_actor_min",
    "lr_alpha",
    "lr_schedule_episodes",
    "lr_restart_cycles",
    "lr_warmup_ratio",
    "auto_lr_on_reward_patch",
    "lr_auto_scale_floor",
    "lr_auto_scale_ceiling",
    "lr_auto_warmup_min",
    "lr_auto_warmup_max",
    "lr_auto_warmup_gain",
    # 학습 조건 전부 (2026-09-17): store_true / 기본 0 인자는 resume CLI 에서 빠지면 꺼진 채로
    # 남는다 — 20260916_154729 iter_004/005 가 absolute action · PER off · LayerNorm 없이 학습됨.
    # 새 인자는 tests/test_resume_layernorm.py 에서 복원 여부를 분류해야 테스트가 통과한다.
    "critic_layernorm",
    "actor_layernorm",
    "ramp_limit_kw",
    "per",
    "per_alpha",
    "per_beta0",
    "per_beta_steps",
    "per_eps",
    "policy",
    "max_episodes",
    "start_episode",
    "episode_steps",
    "batch_size",
    "buffer_size",
    "gamma",
    "tau",
    "alpha",
    "auto_tune",
    "policy_delay",
    "target_entropy_scale",
    "lr_alpha_min",
    "const_lr",
    "cuda",
    "chunk_episodes",
    "feedback_process_episodes",
    "reset_agent_on_patch",
    "reward_module",
    "reward_file",
    "llm_provider",
    "llm_model",
    # provider 와 짝 — 빠지면 파싱 기본값(openai)의 OPENAI_API_KEY 가 남아 Anthropic 에 401 (2026-09-17)
    "llm_api_key_env",
    "multi_agent_review",
    "parse_retries",
    "tpe_retries",
    "tpe_soc_in_bounds_floor",
    "soc_low",
    "soc_high",
    # "aligned_min_tac" 는 의도적으로 제외한다 (2026-09-16): 학습 조건이 아니라 게이트 정책
    # 노브다. run_config 에 박힌 구 문턱(0.2)이 resume 에서 되살아나면 새 기본값(0.12)이
    # 조용히 무시된다 — 20260916_074239 iter_002 에서 그 문턱이 21/21 탈락을 만들었다.
    "aligned_dominance_threshold",
    "aligned_soc_dominance_threshold",
    "aligned_min_h2_fraction",
    "aligned_h2_perturbation_ratio",
    "aligned_w_fcs_gt",
    "aligned_w_batt_gt",
]


def _fmt_tag_value(v):
    s = str(v)
    # Keep folder names shell-friendly and compact.
    return s.replace(" ", "").replace("/", "-").replace(".", "p")


def _llm_run_tag(args) -> str:
    # 실제 호출되는 모델로 태그한다 (2026-10-12): 역할별 맵이 llm_model 을 덮어쓰므로
    # llm_model 만 찍으면 한 번도 호출되지 않은 모델(gpt-5.4)이 폴더명에 남는다.
    provider = _fmt_tag_value(getattr(args, "llm_provider", "") or "llm")
    models = _llm_role_models(args).values()
    names = list(dict.fromkeys(_fmt_tag_value(m.split("/")[-1]) for m in reversed(list(models))))
    return f"{provider}_{'+'.join(names)}"


def _llm_role_models(args) -> Dict[str, str]:
    from llm_presets import get_role_models
    return get_role_models(getattr(args, "llm_provider", ""), str(getattr(args, "llm_model", "") or "default"))


def _review_run_tag(args) -> str:
    if bool(getattr(args, "multi_agent_review", False)):
        return "_multiagent"
    return ""


def _create_run_root(args):
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = (
        f"{stamp}_{args.DRL}_{args.scenario_name}"
        f"_wsoc{_fmt_tag_value(args.w_soc)}"
        f"_iter{_fmt_tag_value(args.ldri_iterations)}"
        f"_chunk{_fmt_tag_value(args.chunk_episodes)}"
        f"_fb{_fmt_tag_value(args.feedback_process_episodes)}"
        f"_llm{_llm_run_tag(args)}"
        f"{_review_run_tag(args)}"
        f"_{args.file_v}"
    )
    run_root = Path(args.ldri_root).resolve() / run_name
    run_root.mkdir(parents=True, exist_ok=True)
    return run_root


def _configure_training_paths(args, run_root):
    # isolate AROMA workflow outputs from baseline directories
    args.save_dir = str((run_root / "models").resolve())
    args.log_dir = str((run_root / "tb_logs").resolve())
    args.eva_dir = str((run_root / "eval").resolve())


def _resolve_input_path(path_value: str) -> str:
    """Resolve CLI path robustly for both project-root and AROMA-root executions."""
    p = Path(path_value)
    ldri_dir = Path(__file__).resolve().parent

    if p.is_absolute():
        if p.exists():
            return str(p.resolve())

        remapped_parts = ["aroma" if part == "CARD" else part for part in p.parts]
        remapped_path = Path(*remapped_parts)
        if remapped_path.exists():
            return str(remapped_path.resolve())

        for candidate in (p.parent / p.name, remapped_path.parent / p.name, ldri_dir / p.name):
            if candidate.exists():
                return str(candidate.resolve())
        return str(p)

    # 1) Relative to current working directory (explicit user intent)
    cwd_candidate = (Path.cwd() / p)
    if cwd_candidate.exists():
        return str(cwd_candidate.resolve())

    # 2) Relative to this AROMA module directory (default arguments)
    ldri_candidate = (ldri_dir / p)
    if ldri_candidate.exists():
        return str(ldri_candidate.resolve())

    # 3) Fallback for clear downstream error message.
    return str(cwd_candidate.resolve())


def _init_llm_client(args):
    if args.skip_llm:
        return None
    api_key = get_api_key(args.llm_provider, args.llm_api_key, args.llm_api_key_env)
    return LLMClient(provider=args.llm_provider, model=args.llm_model, api_key=api_key)


def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _resolve_run_root(args):
    resume_run_root = str(getattr(args, "resume_run_root", "") or "").strip()
    if resume_run_root:
        run_root = Path(resume_run_root).resolve()
        if not run_root.exists() or not run_root.is_dir():
            raise RuntimeError(f"invalid --resume_run_root: {run_root}")
        return run_root, True
    return _create_run_root(args), False


def _explicit_cli_keys(argv=None) -> set:
    """CLI 에서 실제로 준 옵션 이름들 (`--w_soc 100`, `--w_soc=100` 둘 다)."""
    import sys as _sys

    tokens = list(_sys.argv[1:] if argv is None else argv)
    keys = set()
    for token in tokens:
        if isinstance(token, str) and token.startswith("--"):
            keys.add(token[2:].split("=", 1)[0].replace("-", "_"))
    return keys


def _apply_resume_run_config(args, run_config: Dict[str, Any], explicit_keys=None):
    """resume 시 저장된 run 조건을 복원한다.

    explicit_keys: 이번 CLI 에서 사용자가 직접 준 키 — 저장값으로 덮지 않는다 (2026-09-16).
    이전에는 무조건 덮어써서, resume 중에는 CLI 로 준 값조차 조용히 무시됐다.
    """
    if not isinstance(run_config, dict):
        raise RuntimeError("invalid run_config.json: expected a JSON object")

    explicit = set(explicit_keys or ())
    # Pre-2026-09-25 metadata did not contain these settings (obs_timing was
    # added later the same day; every run before it observed the previous step). Never silently
    # resume such training with the newer fixed-normalization/shortage defaults.
    legacy = {"obs_norm": "cycle", "obs_speed_scale": 40.0,
              "obs_acc_scale": 4.0, "unserved_cost_per_kw": 0.0, "obs_timing": "lagged"}
    run_config = {**{k: v for k, v in legacy.items() if k not in run_config}, **run_config}
    overridden = []
    for key in RESUME_RESTORE_KEYS:
        if key not in run_config or key in explicit:
            continue
        if not hasattr(args, key):
            continue
        saved_value = run_config.get(key)
        if saved_value is None:
            continue
        current_value = getattr(args, key)
        if current_value != saved_value:
            setattr(args, key, saved_value)
            overridden.append((key, current_value, saved_value))
    return overridden


def _build_run_config(args) -> Dict[str, Any]:
    """run_config.json 페이로드 (스펙 A2: confound 재발 방지).

    기존 화이트리스트 키는 호환 유지하고, 나머지 vars(args) 전부를 병합 기록한다 —
    260901 run에서 --ramp_limit_kw/--per 누락이 미기록이라 절대액션 confound를
    데이터 역산으로만 발견할 수 있었던 문제의 재발 방지. JSON 직렬화 불가 값은
    repr 문자열로 기록한다.
    """
    run_config = {
        "DRL": args.DRL,
        "scenario_name": args.scenario_name,
        "MODE": args.MODE,
        "soc0": args.soc0,
        "soc_target": args.soc_target,
        "w_soc": args.w_soc,
        "w_h2": args.w_h2,
        "w_fc": args.w_fc,
        "w_batt": args.w_batt,
        "eq_h2_batt_coef": args.eq_h2_batt_coef,
        "random_seed": args.random_seed,
        "seed": args.seed,
        "lr_critic": args.lr_critic,
        "lr_critic_min": args.lr_critic_min,
        "lr_actor": args.lr_actor,
        "lr_actor_min": args.lr_actor_min,
        "lr_alpha": args.lr_alpha,
        "lr_schedule_episodes": args.lr_schedule_episodes,
        "lr_restart_cycles": args.lr_restart_cycles,
        "lr_warmup_ratio": args.lr_warmup_ratio,
        "auto_lr_on_reward_patch": args.auto_lr_on_reward_patch,
        "lr_auto_scale_floor": args.lr_auto_scale_floor,
        "lr_auto_scale_ceiling": args.lr_auto_scale_ceiling,
        "lr_auto_warmup_min": args.lr_auto_warmup_min,
        "lr_auto_warmup_max": args.lr_auto_warmup_max,
        "lr_auto_warmup_gain": args.lr_auto_warmup_gain,
        "ldri_iterations": args.ldri_iterations,
        "chunk_episodes": args.chunk_episodes,
        "feedback_process_episodes": args.feedback_process_episodes,
        "reset_agent_on_patch": args.reset_agent_on_patch,
        "reward_module": args.reward_module,
        "reward_file": args.reward_file,
        "llm_provider": args.llm_provider,
        "llm_model": args.llm_model,
        "multi_agent_review": args.multi_agent_review,
        "parse_retries": args.parse_retries,
        "tpe_retries": args.tpe_retries,
        "tpe_soc_in_bounds_floor": args.tpe_soc_in_bounds_floor,
        "soc_low": args.soc_low,
        "soc_high": args.soc_high,
        "aligned_min_tac": args.aligned_min_tac,
        "tac_role": "diagnostic",
        "fuel_metric_basis": DETERMINISTIC_FUEL_BASIS,
        "aligned_dominance_threshold": args.aligned_dominance_threshold,
        "aligned_soc_dominance_threshold": args.aligned_soc_dominance_threshold,
        "aligned_min_h2_fraction": args.aligned_min_h2_fraction,
        "aligned_h2_perturbation_ratio": args.aligned_h2_perturbation_ratio,
        "aligned_w_fcs_gt": args.aligned_w_fcs_gt,
        "aligned_w_batt_gt": args.aligned_w_batt_gt,
        "created_at": dt.datetime.now().isoformat(),
    }
    for key, value in vars(args).items():
        if key in run_config:
            continue
        try:
            json.dumps(value)
        except (TypeError, ValueError):
            value = repr(value)
        run_config[key] = value
    # llm_model 은 역할 맵에 없는 역할의 fallback 일 뿐이다 — 실제 요청 모델은 여기를 본다.
    run_config["llm_role_models"] = _llm_role_models(args)
    return run_config


# ─────────────────────────────────────────────────────────────────────────────
# Priority 6: Independent Policy Evaluator (pure Python, CLoud-style)
# Scores the trained policy on fuel efficiency, SOC stability, and convergence.
# ─────────────────────────────────────────────────────────────────────────────

def _compute_policy_quality_score(log_path: str, args) -> Dict[str, Any]:
    """Python-based policy quality assessment after each training chunk."""
    from feedback_parser import (h2_quality_scores, deterministic_h2eq_corr_for_episode,
                                 DETERMINISTIC_FUEL_BASIS, parse_train_log)

    try:
        episodes = parse_train_log(log_path)
    except Exception as e:
        return {"status": "failed", "error": str(e), "score": None}

    if not episodes:
        return {"status": "empty", "score": None}

    # Prefer DETERMINISTIC eval metrics (mean-action rollout) over the noisy
    # stochastic training rollout. Fall back to stochastic fields for older logs
    # that predate the "[eval]" lines.
    def _h2(ep):
        return ep.eval_h2_100km if ep.eval_h2_100km is not None else ep.h2_100km

    def _inb(ep):
        return ep.eval_in_bounds_rate if ep.eval_in_bounds_rate is not None else ep.in_bounds_rate

    def _obj(ep):
        return ep.eval_objective_100km if ep.eval_objective_100km is not None else ep.objective_100km

    def _smin(ep):
        return ep.eval_soc_min if ep.eval_soc_min is not None else ep.soc_min

    def _smax(ep):
        return ep.eval_soc_max if ep.eval_soc_max is not None else ep.soc_max

    def _rew(ep):
        return ep.eval_r if ep.eval_r is not None else ep.ep_cumulative_r

    uses_eval = any(ep.eval_objective_100km is not None for ep in episodes)
    conv_basis = "deterministic" if uses_eval else "stochastic_fallback"

    # H2 quality (lower h2_100km = better fuel efficiency)
    h2_vals = sorted([float(_h2(ep)) for ep in episodes if _h2(ep) is not None])
    h2_mean = sum(h2_vals) / len(h2_vals) if h2_vals else None
    h2_p10 = h2_vals[max(0, len(h2_vals) // 10 - 1)] if h2_vals else None

    # Fuel quality and champion selection share deterministic dSOC-corrected fuel.
    # Missing evals stay missing: stochastic/raw fuel is not a comparable fallback.
    soc0 = float(getattr(args, "soc0", 0.6))

    def _h2corr(ep):
        return deterministic_h2eq_corr_for_episode(ep, soc0)

    h2corr_vals = [float(_h2corr(ep)) for ep in episodes if _h2corr(ep) is not None]
    # 수렴 꼬리(마지막 10%) 연비 — champion 비교 창 (2026-09-16). 평가가 ep499 정책이므로
    # agent 리셋 직후 탐색 구간이 섞인 chunk 평균으로 순위를 매기지 않는다. §17 이후 run 과 같은 정의.
    _k_tail = max(1, len(episodes) // 10)
    _tail_h2 = [float(_h2corr(ep)) for ep in episodes[-_k_tail:] if _h2corr(ep) is not None]
    # Do not silently compare a partial tail to a complete champion window.
    h2corr_tail_mean = sum(_tail_h2) / _k_tail if len(_tail_h2) == _k_tail else None

    # 물리 하한 [g/100km]: 사이클 순 수요 에너지 x FC 최적 sfc — 환경에서 런타임 유도되는
    # 정책 무관 상수(§13 원칙: 해가 아닌 플랜트의 사실). 유도 실패 시 None -> 일관성 단독.
    h2_floor = None
    _scenario = getattr(args, "scenario_name", None)
    if _scenario:
        try:
            from env_physics_facts import cycle_h2_floor_g_per_100km
            h2_floor = cycle_h2_floor_g_per_100km(_scenario)
        except Exception:
            h2_floor = None

    # SOC quality (higher in-bounds rate = better)
    inbounds_vals = [float(_inb(ep)) for ep in episodes if _inb(ep) is not None]
    inbounds_mean = sum(inbounds_vals) / len(inbounds_vals) if inbounds_vals else None

    # Durability budget signals (per-step degradation costs, this run's own history —
    # recorded into trajectory_memory so reviewers can judge "sustained worsening"
    # across iterations without any external reference)
    fcs_cost_vals = [float(ep.mean_fcs_cost) for ep in episodes if ep.mean_fcs_cost is not None]
    batt_cost_vals = [float(ep.mean_batt_cost) for ep in episodes if ep.mean_batt_cost is not None]
    mean_fcs_cost = sum(fcs_cost_vals) / len(fcs_cost_vals) if fcs_cost_vals else None
    mean_batt_cost = sum(batt_cost_vals) / len(batt_cost_vals) if batt_cost_vals else None

    # Battery buffer utilization
    soc_swings = [
        float(_smax(ep)) - float(_smin(ep))
        for ep in episodes
        if _smin(ep) is not None and _smax(ep) is not None
    ]
    mean_swing = sum(soc_swings) / len(soc_swings) if soc_swings else None

    # Convergence = STABILITY, not peak position. Penalize DEGRADATION: how far the
    # converged (final) policy regresses from the best the policy ever reached. A
    # reward that lets the policy peak and HOLD scores high (even if it converged
    # early); one that peaks then decays scores low. Fast stable convergence is NOT
    # penalized. Measured on the deterministic eval objective (lower = better).
    obj_traj = [float(_obj(ep)) for ep in episodes if _obj(ep) is not None]
    if len(obj_traj) >= 2:
        best_obj = min(obj_traj)
        k = max(1, round(0.1 * len(obj_traj)))      # robust "final" = mean of last 10%
        final_obj = sum(obj_traj[-k:]) / k
        denom = abs(best_obj) if abs(best_obj) > 1e-9 else 1e-9
        degradation = max(0.0, (final_obj - best_obj) / denom)
    else:
        degradation = 0.0
    conv_tol = 0.15  # >=15% regression from best -> conv_score 0 (tunable)
    conv_score = max(0.0, 100.0 * (1.0 - degradation / conv_tol))

    # diagnostic only (no longer feeds the score): where the best eval occurred
    rew_traj = [(i, float(_rew(ep))) for i, ep in enumerate(episodes) if _rew(ep) is not None]
    n = len(rew_traj)
    best_ep_ratio = (max(rew_traj, key=lambda t: t[1])[0] / (n - 1)) if n > 1 else 1.0

    # Scores (0-100). h2_score carries NO external-solution information (DP /
    # baseline policy stays forbidden): the LEVEL component is anchored to the
    # physics floor (cycle demand x best sfc — a fact about the plant, derived at
    # runtime like env_physics_facts), and the CONSISTENCY component to the
    # policy's OWN best decile. Consistency alone was blind: a uniformly BAD
    # policy scored ~100 (p10 ≈ mean) and the orchestrator never saw the fuel
    # failure. Level = 100 x floor / corrected TAIL mean (last 10%) is monotone in consumption.
    # 레벨은 champion 비교와 같은 꼬리 창 기준 (2026-09-17)
    hq = h2_quality_scores(h2corr_vals, h2_floor, level_mean=h2corr_tail_mean)
    h2_score = hq["h2_score"] if hq["h2_score"] is not None else 50.0
    soc_score = float(inbounds_mean) if inbounds_mean is not None else 50.0

    # ramp-tax 실패 시그니처 필드 (FC 고정 + SOC 상향 드리프트 + 열화 초저치 진단용)
    _eff_vals = [float(ep.fce_eff_mean) for ep in episodes if ep.fce_eff_mean is not None]
    _fc_on_vals = [float(ep.fc_on_pct) for ep in episodes if ep.fc_on_pct is not None]
    _soc_target = float(getattr(args, "soc_target", 0.6))
    _drift_vals = [float(ep.soc_end) - _soc_target for ep in episodes if ep.soc_end is not None]

    composite = round(0.40 * h2_score + 0.40 * soc_score + 0.20 * conv_score, 1)

    return {
        "status": "ok",
        "score": composite,
        "h2_score": round(h2_score, 1),
        "soc_score": round(soc_score, 1),
        "convergence_score": round(conv_score, 1),
        "convergence_degradation": round(degradation, 4),
        "convergence_basis": conv_basis,
        "h2_level_score": round(hq["h2_level_score"], 1) if hq["h2_level_score"] is not None else None,
        "h2_level_basis": "tail10" if h2corr_tail_mean is not None else "chunk_mean",
        "h2_consistency_score": round(hq["h2_consistency_score"], 1) if hq["h2_consistency_score"] is not None else None,
        "h2_floor_g100km": round(h2_floor, 3) if h2_floor is not None else None,
        "h2eq_corr_mean_g100km": round(hq["h2_mean"], 3) if hq["h2_mean"] is not None else None,
        "h2eq_corr_tail_mean_g100km": (
            h2corr_tail_mean
        ),
        "equivalent_g_per_km_tail_mean": (h2corr_tail_mean / 100.0 if h2corr_tail_mean is not None else None),
        "fuel_metric_basis": DETERMINISTIC_FUEL_BASIS,
        "fuel_eval_count": len(h2corr_vals),
        "fuel_tail_eval_count": len(_tail_h2),
        "fuel_tail_expected_count": _k_tail,
        "fuel_tail_episodes": [ep.episode for ep in episodes[-_k_tail:]],
        "fce_eff_mean": round(sum(_eff_vals) / len(_eff_vals), 4) if _eff_vals else None,
        "fc_on_pct_mean": round(sum(_fc_on_vals) / len(_fc_on_vals), 1) if _fc_on_vals else None,
        "soc_end_minus_target_mean": round(sum(_drift_vals) / len(_drift_vals), 4) if _drift_vals else None,
        "h2_mean_g100km": round(h2_mean, 3) if h2_mean is not None else None,
        "h2_best_p10": round(h2_p10, 3) if h2_p10 is not None else None,
        "inbounds_rate_mean": round(inbounds_mean, 1) if inbounds_mean is not None else None,
        "mean_fcs_cost": round(mean_fcs_cost, 4) if mean_fcs_cost is not None else None,
        "mean_batt_cost": round(mean_batt_cost, 4) if mean_batt_cost is not None else None,
        "mean_soc_swing": round(mean_swing, 4) if mean_swing is not None else None,
        "battery_underutilized": (mean_swing is not None and mean_swing < 0.05),
        "best_episode_ratio": round(best_ep_ratio, 4),
        "n_episodes": n,
    }


def _seed_iteration_from_existing_run(run_root: Path, args, iteration: int, chunk_result_cls):
    """--seed_chunk_dir 의 기존 학습 산출물을 이 iteration 의 chunk 로 연결한다 (학습 없음).

    baseline SAC 는 이미 같은 설정으로 500 에피소드 학습돼 있으므로 다시 돌리는 것은 계산 낭비다.
    로그는 복사, episode_data 는 symlink, 체크포인트는 eval_sweep.sh 가 찾는
    `<key>_iterNNN_ep<N>.pkl` 이름으로 symlink 한다.
    """
    import shutil

    src = Path(str(getattr(args, "seed_chunk_dir", "") or "")).expanduser().resolve()
    log_src, ep_src, nets_src = src / "train_log.log", src / "episode_data", src / "net_params"
    missing = [str(p) for p in (log_src, ep_src) if not p.exists()]
    if missing:
        raise RuntimeError(f"--seed_chunk_dir is missing training artifacts: {missing}")

    iter_dir = run_root / f"iter_{int(iteration):03d}"
    iter_dir.mkdir(parents=True, exist_ok=True)
    log_dst = iter_dir / "train_log.log"
    shutil.copyfile(log_src, log_dst)
    ep_dst = iter_dir / "episode_data"
    if not ep_dst.exists():
        ep_dst.symlink_to(ep_src, target_is_directory=True)

    model_dir = run_root / "models" / f"iter_{int(iteration):03d}" / args.scenario_name / "net_params"
    model_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"iter{int(iteration):03d}"
    n_linked = 0
    if nets_src.is_dir():
        for f in sorted(nets_src.glob("*_params_ep*.pkl")):
            m = re.fullmatch(r"(?P<key>.+)_params_ep(?P<ep>\d+)\.pkl", f.name)
            if not m:
                continue
            if (getattr(args, "refinement_protocol", "") == "sequential"
                    and (m.group('key') != 'actor' or not
                         args.chunk_episodes - max(1, args.chunk_episodes // 10)
                         <= int(m.group('ep')) < args.chunk_episodes)):
                continue
            dst = model_dir / f"{m.group('key')}_{prefix}_ep{m.group('ep')}.pkl"
            if not dst.exists():
                dst.symlink_to(f.resolve())
            n_linked += 1

    episodes = re.findall(r"^epi\s+(\d+):", log_dst.read_text(encoding="utf-8", errors="ignore"),
                          flags=re.MULTILINE)
    start_episode, end_episode = (
        (int(episodes[0]), int(episodes[-1])) if episodes else (0, int(args.chunk_episodes) - 1)
    )
    _write_json(iter_dir / "seed_source.json", {
        "seed_chunk_dir": str(src),
        "seed_reward_file": str(getattr(args, "seed_reward_file", "") or ""),
        "episodes": [start_episode, end_episode],
        "checkpoints_linked": n_linked,
        "note": "iteration trained OUTSIDE this run (no retraining); artifacts linked",
    })
    return chunk_result_cls(
        iteration=int(iteration),
        start_episode=start_episode,
        end_episode=end_episode,
        log_path=str(log_dst),
        episode_data_dir=str(ep_dst),
        model_dir=str(model_dir),
        chunk_dir=str(iter_dir),
        best_episode=None,
        best_reward=None,
    )


def main():
    args = get_ldri_args()

    if int(getattr(args, "resume_additional_iterations", 0)) < 0:
        raise RuntimeError("--resume_additional_iterations must be >= 0")

    run_root, resume_mode = _resolve_run_root(args)
    run_config_path = run_root / "run_config.json"

    if resume_mode and bool(getattr(args, "resume_use_saved_config", True)):
        if run_config_path.exists():
            overridden = _apply_resume_run_config(
                args, _read_json(run_config_path), explicit_keys=_explicit_cli_keys()
            )
            if overridden:
                print("[resume] restored configuration from run_config.json")
                for key, old_val, new_val in overridden:
                    print(f"  - {key}: {old_val!r} -> {new_val!r}")
        else:
            print(
                "[resume] warning: run_config.json not found; "
                "continuing with current CLI arguments."
            )

    if args.refinement_protocol != "sequential":
        raise RuntimeError("The validated protocol was archived to archive/ldri_unused_20261001/; "
                           "use --refinement_protocol sequential")
    from sequential_workflow import run_sequential_workflow
    return run_sequential_workflow(args, run_root, resume_mode, api=sys.modules[__name__])


if __name__ == "__main__":
    main()
