from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class AgentPreset:
    agent_type: str
    provider: str
    model: str
    api_key_env: str


AGENT_PRESETS = {
    "gpt": AgentPreset(
        agent_type="gpt",
        provider="openai",
        model="gpt-5.2",
        api_key_env="OPENAI_API_KEY",
    ),
    "claude": AgentPreset(
        agent_type="claude",
        provider="anthropic",
        model="claude-sonnet-4-6",
        api_key_env="ANTHROPIC_API_KEY",
    ),
    "llama": AgentPreset(
        agent_type="llama",
        provider="huggingface",
        model="meta-llama/Llama-3.1-70B-Instruct",
        api_key_env="HF_TOKEN",
    ),
}


def get_agent_type_choices():
    return tuple(AGENT_PRESETS.keys())


def get_agent_preset(agent_type: str) -> AgentPreset:
    normalized = str(agent_type or "gpt").strip().lower()
    try:
        return AGENT_PRESETS[normalized]
    except KeyError as exc:
        valid = ", ".join(get_agent_type_choices())
        raise ValueError(f"unsupported agent_type: {agent_type!r}. Expected one of: {valid}") from exc


# Per-agent model assignment per provider.
# trainability_scheduler is excluded: replaced by pure Python computation.
AGENT_MODELS: Dict[str, Dict[str, str]] = {
    "anthropic": {
        # Stage 2a: specialist reviewers
        # fuel_soc: structured JSON, rule-heavy → Haiku sufficient
        # fc_durability / battery_degradation: structured JSON, co-objective persona → Haiku sufficient
        # reward_hacking: code structure analysis → Sonnet for reliability
        "fuel_soc":          "claude-haiku-4-5-20251001",
        "fc_durability":     "claude-haiku-4-5-20251001",
        "battery_degradation": "claude-haiku-4-5-20251001",
        "reward_hacking":    "claude-sonnet-4-6",
        # Stage 2.5: trade-off mediator — conflict resolution requires reasoning
        "tradeoff_mediator": "claude-sonnet-4-6",
        # Stage 3: orchestrator — synthesizes all reviewer + mediator outputs into a
        # structured JSON spec. Task is rule-driven + structured-output heavy, so Sonnet
        # (reliable JSON completion, consistent with mediator/proposer) over Opus, which
        # tended to emit verbose prose and truncate the spec mid-must_change.
        "orchestrator":      "claude-sonnet-4-6",
        # Stage 4: proposer — generates actual Python reward code
        "proposer":          "claude-sonnet-4-6",
    },
    "openai": {
        "fuel_soc":          "gpt-5-mini",
        "fc_durability":     "gpt-5-mini",
        "battery_degradation": "gpt-5-mini",
        "reward_hacking":    "gpt-5.2",
        "tradeoff_mediator": "gpt-5.2",
        "orchestrator":      "gpt-5.2",
        "proposer":          "gpt-5.2",
    },
    "huggingface": {
        "fuel_soc":          "meta-llama/Llama-3.1-70B-Instruct",
        "fc_durability":     "meta-llama/Llama-3.1-70B-Instruct",
        "battery_degradation": "meta-llama/Llama-3.1-70B-Instruct",
        "reward_hacking":    "meta-llama/Llama-3.1-70B-Instruct",
        "tradeoff_mediator": "meta-llama/Llama-3.1-70B-Instruct",
        "orchestrator":      "meta-llama/Llama-3.1-70B-Instruct",
        "proposer":          "meta-llama/Llama-3.1-70B-Instruct",
    },
}


def get_agent_model(provider: str, agent_name: str, fallback_model: str) -> str:
    """Return the per-agent model for a given provider.

    Falls back to fallback_model when the provider or agent_name is not in AGENT_MODELS.
    """
    provider_map = AGENT_MODELS.get(str(provider or "").lower().strip(), {})
    return provider_map.get(agent_name, fallback_model)


def get_role_models(provider: str, fallback_model: str) -> Dict[str, str]:
    """Role → model actually requested for a provider (run_config / run-name record).

    Every review/proposal call goes through get_agent_model, so for a provider listed in
    AGENT_MODELS the --llm_model value is never sent; only an unlisted provider uses it.
    """
    provider_map = AGENT_MODELS.get(str(provider or "").lower().strip())
    return dict(provider_map) if provider_map else {"default": fallback_model}
