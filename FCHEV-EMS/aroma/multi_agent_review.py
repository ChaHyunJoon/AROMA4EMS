"""Multi-agent reward review pipeline for AROMA.

Architecture (six-priority multi-agentic workflow):
  context_builder → diagnostic_agent (Python)
  → [fuel_soc | reward_hacking | fc_durability | battery_degradation] (LLM x4)
  + scale_reviewer (Python) + trainability_scheduler (Python)
  → tradeoff_mediator (LLM) → orchestrator (LLM x1)
  → counterfactual_evaluator (Python) → proposer (LLM x1..N) → TPE/aligned-gate verifier

Priority 1: Training Diagnostic Agent (Python — pre-review failure classification)
Priority 2: Specialist Agents — fc_durability and battery_degradation as bounded-secondary durability-budget reviewers (fuel-first)
Priority 3: Trade-off Mediator — resolves reviewer conflicts; fuel efficiency > SOC tightening
Priority 4: Counterfactual Evaluator — flags high-risk orchestrator_spec changes
Priority 5: Iteration Memory — trajectory_memory + insight_memory passed via iteration_memory kwarg
Priority 6: Policy Quality — Python metric score computed externally in main_ldri_refine

CRITICAL: Fuel efficiency (g/km, h2_100km) is ALWAYS the primary objective.
          SOC is a constraint to ENABLE fuel efficiency, not an end in itself.

Entry point: run_multi_agent_review()
Returns the same dict shape as _run_llm_with_tpe_retry().

Risk precedence (fuel efficiency is PRIMARY):
  fuel_soc hard_reject > reward_hacking hard_reject > scale_reviewer hard_reject
  > fuel_soc joint diagnosis > trainability_scheduler

Per-agent model selection:
  Provider-specific tiers are defined in llm_presets.AGENT_MODELS.
  scale_reviewer, trainability_scheduler, diagnostic_agent, counterfactual_evaluator
  are pure Python (no LLM calls).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from ldri_observer import _write_json
from review_evidence import EvidenceClient




# ─────────────────────────────────────────────────────────────────────────────
# Historical reward guard helpers
# ─────────────────────────────────────────────────────────────────────────────


class _RewardProbeStub:
    pass


def _make_reward_probe_state(case: Dict[str, float]) -> _RewardProbeStub:
    stub = _RewardProbeStub()
    eq_h2_batt_coef = 0.0164
    for key, value in case.items():
        setattr(stub, key, value)
    stub.SOC_target = 0.60
    stub.soc_target = 0.60
    stub.soc_bounds = (0.40, 0.80)
    stub.soc_low = 0.40
    stub.soc_high = 0.80
    stub.w_soc = 100.0
    stub.w_h2 = 10.0
    stub.w_fc = 4_275_000.0
    stub.w_batt = 1_116_000.0
    stub.eq_h2_batt_coef = eq_h2_batt_coef
    stub.time_step = 1.0
    stub.P_batt_req = float(case.get("P_batt", 0.0))
    stub.h2_batt = float(stub.P_batt) / 1000.0 * eq_h2_batt_coef
    stub.h2_equal = float(stub.h2_fcs) + float(stub.h2_batt)
    stub.info = {}
    return stub


def _reward_behavior_grid() -> List[Dict[str, float]]:
    """중복 판정용 조밀한 probe — SOC 0~1 전 구간 × 부하 3종.

    _reward_probe_cases 5개는 "무언가 바뀌었나"를 싸게 보는 용도라 SOC 0.35~0.85 만 본다.
    "이미 학습한 reward 와 같은가"는 더 넓게 봐야 한다 — 한 구간만 다른 reward 를 같다고
    판정하면 새 제안을 잘못 막는다.
    """
    loads = (
        {"h2_fcs": 0.10, "P_batt": 0.0, "P_FCS": 10.0, "dSOH_FCS": 1e-8, "dSOH_batt": 1e-8},
        {"h2_fcs": 0.85, "P_batt": 30_000.0, "P_FCS": 20.0, "dSOH_FCS": 1e-7, "dSOH_batt": 3e-7},
        {"h2_fcs": 1.80, "P_batt": -30_000.0, "P_FCS": 85.0, "dSOH_FCS": 7e-7, "dSOH_batt": 4e-7},
    )
    socs = sorted({round(i / 80.0, 4) for i in range(81)} | {0.35, 0.40, 0.45, 0.60, 0.75, 0.80, 0.85})
    return [dict(load, SOC=soc) for soc in socs for load in loads]


# ─────────────────────────────────────────────────────────────────────────────
# Scale reviewer: pure Python (no LLM)
# Extracts numeric scaling coefficients from reward source and checks them
# against _SCALE_CAPS and per-iteration change-rate limits.
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# Priority 1: Training Diagnostic Agent (pure Python, pre-review)
# Classifies failure mode before LLM reviewers so they share a common context.
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# JSON extraction
# ─────────────────────────────────────────────────────────────────────────────


def _llm_usage_totals(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    totals: Dict[str, Any] = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "total_cost_usd": 0.0,
        "has_unpriced_calls": False,
    }
    for rec in records:
        usage = rec.get("usage") or {}
        cost = rec.get("cost") or {}
        totals["input_tokens"] += int(usage.get("input_tokens", usage.get("prompt_tokens")) or 0)
        totals["output_tokens"] += int(usage.get("output_tokens", usage.get("completion_tokens")) or 0)
        totals["total_tokens"] += int(usage.get("total_tokens") or cost.get("total_tokens") or 0)
        if cost.get("total_cost") is None:
            totals["has_unpriced_calls"] = True
        else:
            totals["total_cost_usd"] += float(cost.get("total_cost") or 0.0)
    return totals


def _write_llm_usage_log(path: Path, records: List[Dict[str, Any]]) -> None:
    _write_json(path, {
        "records": records,
        "totals": _llm_usage_totals(records),
        "pricing_note": (
            "Set LLM_PRICE_USD_PER_1M_JSON to estimate USD cost, e.g. "
            "'{\"provider:model\":{\"input\":3,\"output\":15}}'. "
            "Rates are USD per 1M tokens."
        ),
    })


def _complete_and_record(*, call, usage_records, usage_path, stage, **kwargs):
    """Make one completion request and record its usage."""
    completion = call(**kwargs)
    record = {
        "stage": stage, "provider": completion.provider, "model": completion.model,
        "requested_model": kwargs.get("model"), "temperature": kwargs["temperature"],
        "max_tokens": kwargs["max_tokens"], "prompt_chars": len(kwargs["prompt"]),
        "response_chars": len(completion.text), "usage": completion.usage,
        "cost": completion.cost,
    }
    if "tools" in kwargs:
        record["note"] = "tool_use"
    usage_records.append(record)
    _write_llm_usage_log(usage_path, usage_records)
    return completion.text


def _tracked_complete(
    *, client, usage_records, usage_path, stage, prompt, temperature,
    max_tokens, timeout_sec, model=None,
) -> str:
    if isinstance(client, EvidenceClient):
        client = client.for_stage(stage)
    kwargs = dict(prompt=prompt, temperature=temperature, max_tokens=max_tokens,
                  timeout_sec=timeout_sec, model=model)
    if hasattr(client, "complete_with_usage"):
        return _complete_and_record(call=client.complete_with_usage, usage_records=usage_records,
                                    usage_path=usage_path, stage=stage, **kwargs)
    text = client.complete(**kwargs)
    usage_records.append({
        "stage": stage, "provider": getattr(client, "provider", None),
        "model": model or getattr(client, "model", None), "temperature": temperature,
        "max_tokens": max_tokens, "prompt_chars": len(prompt), "response_chars": len(text),
        "usage": {}, "cost": {"currency": "USD", "total_cost": None, "pricing_source": None},
        "note": "client does not expose complete_with_usage",
    })
    _write_llm_usage_log(usage_path, usage_records)
    return text


# ─────────────────────────────────────────────────────────────────────────────
# Context builder (no LLM)
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# Reviewer prompts (each reviewer receives a focused slice of the packet)
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# Blackboard MAS: observation scope + blackboard/conflict schema injection
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# Trainability reviewer: pure Python (no LLM)
# Mirrors reward_lr_tuner._training_trend_summary + auto_tune_lrs logic.
# Runs before the proposer, so reward_scale_ratio is not yet computable.
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# Reviewer runner
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# Priority 3: Trade-off Mediator
# Resolves conflicts between specialist reviewers.
# Equivalent hydrogen and charge sustaining are jointly diagnosed before tradeoffs.
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# Priority 4: Counterfactual Risk Checker (pure Python)
# Evaluates orchestrator_spec.must_change for high-risk changes before proposer.
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# Proposer
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# Aligned gate feedback builder
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────
