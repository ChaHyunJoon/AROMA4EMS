"""resume 시 학습 조건(네트워크 구조·액션 모드·PER·SAC 하이퍼파라미터)을 전부 복원한다 (2026-09-17).

`--critic_layernorm`/`--per` 는 store_true, `--ramp_limit_kw` 는 기본 0.0 이라 `--resume_run_root` 만
주면 꺼진 채로 파싱되고, 복원 키가 아니어서 그대로 남았다. 20260916_154729 는 04:03 resume 이후
iter_004/005 를 absolute action · PER off · LayerNorm 없는 critic 으로 학습했다 — iter_002/003 과
학습 조건이 달라 reward 비교가 성립하지 않는다.

Run: python3 -m pytest tests/test_resume_layernorm.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main_ldri_refine as mlr
from arguments_ldri import get_ldri_args

# 20260916_154729 run_config.json 의 학습 조건 (iter_002/003 이 실제로 학습한 값)
_SAVED_TRAINING = {
    "critic_layernorm": True, "actor_layernorm": False,
    "ramp_limit_kw": 19.0,
    "per": True, "per_alpha": 0.6, "per_beta0": 0.4, "per_beta_steps": 1717940, "per_eps": 1e-06,
    "policy": "Gaussian", "batch_size": 256, "buffer_size": 1000000, "gamma": 0.995, "tau": 0.005,
    "alpha": 1.0, "auto_tune": True, "policy_delay": 1, "target_entropy_scale": 1.0,
    "lr_alpha_min": 5e-05, "const_lr": False, "max_episodes": 500, "start_episode": 0,
    "episode_steps": None, "cuda": True,
}

# resume 에서 의도적으로 복원하지 않는 인자 — 학습 조건이 아니다.
NOT_RESTORED = {
    # resume 제어 / 외부 체크포인트 로드 (이번 호출이 정한다)
    "resume_run_root", "resume_additional_iterations",
    "resume_use_saved_config", "ldri_iterations",
    "load_or_not", "load_episode", "load_scenario_name", "load_dir",
    # 경로 / 이름
    "ldri_root", "file_v",
    # LLM 호출 옵션 (학습과 무관, 비밀값 포함)
    "agent_type", "llm_api_key", "llm_temperature", "llm_max_tokens", "llm_timeout_sec",
    "skip_llm", "skip_patch", "debate_rounds",
    # L4 는 명시적으로 켜는 단계 — resume 마다 이번 호출이 정한다
    "run_confirmation",
    # fork 는 새 run 을 만드는 단계 — baseline 출처는 run_summary.forked_from 에 기록된다
    "fork_from_run_root",
    # 게이트 정책 노브 — 새 기본값이 resume 에서 적용돼야 한다 (aligned_min_tac 주석 참고)
    "aligned_min_tac", "aligned_tac_tail_fraction", "aligned_mt_envelope_quantile",
    "aligned_mt_seed", "aligned_mt_sobol", "aligned_mt_top_k", "aligned_mt_de_maxiter",
    "aligned_mt_de_popsize", "aligned_mt_eps_up", "aligned_mt_min_sensitivity_h2",
    "aligned_mt_min_sensitivity_fcs", "aligned_mt_min_sensitivity_batt",
    "aligned_mt_min_sensitivity_soc", "aligned_mt_soc_oob_offset",
    "tpe_fp_pool_size", "tpe_fp_topk", "tpe_fp_bottomk",
}


def _parse(argv):
    old = sys.argv
    try:
        sys.argv = ["x"] + argv
        return get_ldri_args()
    finally:
        sys.argv = old


def _resume(argv, saved):
    args = _parse(argv)
    mlr._apply_resume_run_config(args, saved, explicit_keys=mlr._explicit_cli_keys(["x"] + argv))
    return args


def test_resume_restores_every_training_condition():
    args = _resume(["--resume_run_root", "r"], _SAVED_TRAINING)
    assert {k: getattr(args, k) for k in _SAVED_TRAINING} == _SAVED_TRAINING


def test_resume_restores_delta_action_and_per():
    args = _resume(["--resume_run_root", "r"], {"ramp_limit_kw": 19.0, "per": True,
                                                  "critic_layernorm": True})
    assert args.ramp_limit_kw == 19.0
    assert args.per is True
    assert args.critic_layernorm is True


def test_saved_false_stays_false():
    args = _resume(["--resume_run_root", "r"], {"critic_layernorm": False, "actor_layernorm": False,
                                                  "per": False})
    assert args.critic_layernorm is False
    assert args.actor_layernorm is False
    assert args.per is False


def test_explicit_cli_value_still_wins():
    args = _resume(["--resume_run_root", "r", "--ramp_limit_kw", "10"], {"ramp_limit_kw": 19.0})
    assert args.ramp_limit_kw == 10.0


def test_resume_preserves_baseline_import_for_pilot_and_final_comparison():
    saved = {"seed_chunk_dir": "/saved/baseline", "seed_reward_file": "/saved/reward.py"}
    args = _resume(["--resume_run_root", "r"], saved)
    assert args.seed_chunk_dir == saved["seed_chunk_dir"]
    assert args.seed_reward_file == saved["seed_reward_file"]
    overridden = _resume(["--seed_chunk_dir", "/explicit/baseline"], saved)
    assert overridden.seed_chunk_dir == "/explicit/baseline"


def test_every_argument_is_classified():
    """새 인자를 추가하면 복원 여부를 정해야 한다 — 조용히 누락되는 학습 조건 방지."""
    parsed = set(vars(_parse([])))
    restored = set(mlr.RESUME_RESTORE_KEYS)
    assert not (restored & NOT_RESTORED)
    assert parsed - restored - NOT_RESTORED == set()
