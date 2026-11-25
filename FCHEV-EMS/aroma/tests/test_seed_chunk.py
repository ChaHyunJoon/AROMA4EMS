"""이미 학습된 run 으로 iteration 1 을 채운다 (2026-09-16).

baseline SAC 학습 결과(train_log / episode_data / net_params)가 이미 있는데 LLM bootstrap 으로
reward 를 새로 만들고 다시 학습하는 것은 계산 낭비다. --seed_chunk_dir 가 주어지면
  * bootstrap(reward_generation_prompt.md) 을 건너뛰고 reward 파일을 --seed_reward_file 의
    get_reward 로 패치한다 (reward history 에는 bootstrap 후보로 등록 → 같은 reward 재제안 차단),
  * iteration 1 은 학습하지 않고 기존 run 의 산출물을 chunk 로 쓴다
    (로그 복사, episode_data symlink, 체크포인트는 iter001 이름으로 symlink).
이후 policy_quality / champion 초기화 / 리뷰 / 패치 / iteration 2 학습은 기존 루프 그대로.

Run: python3 -m pytest tests/test_seed_chunk.py
"""
import inspect
import json
import os
import shutil
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main_ldri_refine as mlr
from runner_ldri import ChunkResult

_LDRI = Path(__file__).resolve().parents[1]
_ROOT = _LDRI.parent
_BASE61 = _ROOT / "runs_dR19_pure_h2_SAC_CS_Gaussian" / "Standard_WLTC_WVUINTER_w100_LR3e-04_dR19_per_seed61_v1"


def _block(n, h2=1000.0):
    return "\n".join([
        f"epi {n}: travel 48.228km, SOC 0.6000, FCS-SOH 0.999900, Bat-SOH 0.999500",
        f"epi {n}: H2_100km {h2:.1f}g, H2eq_100km {h2:.1f}g (batt 0.0g), g/km 9.9, objective_100km 1000.00",
        f"epi {n}: SOC[min/mean/max]=0.450/0.600/0.700, in_bounds_rate=100.0%, len=3441",
    ])


def _fake_seed_dir(tmp_path):
    src = tmp_path / "baseline_run"
    (src / "episode_data").mkdir(parents=True)
    (src / "net_params").mkdir()
    (src / "train_log.log").write_text("\n".join(_block(n) for n in range(3)) + "\n", encoding="utf-8")
    (src / "episode_data" / "data_ep2.mat").write_bytes(b"x")
    for key in ("actor", "critic", "alpha"):
        (src / "net_params" / f"{key}_params_ep2.pkl").write_bytes(key.encode())
    (src / "net_params" / "actor_best.pkl").write_bytes(b"b")
    return src


def _args(**kw):
    base = dict(scenario_name="Standard_WLTC_WVUINTER", chunk_episodes=500, seed_chunk_dir="",
                seed_reward_file="")
    base.update(kw)
    return types.SimpleNamespace(**base)


# ── CLI ──────────────────────────────────────────────────────────────────────

def test_seed_args_are_registered_and_off_by_default(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog"])
    from arguments_ldri import get_ldri_args
    a = get_ldri_args()
    assert a.seed_chunk_dir == "" and a.seed_reward_file == ""


# ── iteration 1 산출물 연결 ──────────────────────────────────────────────────

def test_seed_iteration_links_the_existing_run_as_the_chunk(tmp_path):
    src = _fake_seed_dir(tmp_path)
    run_root = tmp_path / "run"
    chunk = mlr._seed_iteration_from_existing_run(
        run_root, _args(seed_chunk_dir=str(src)), iteration=1, chunk_result_cls=ChunkResult)

    it = run_root / "iter_001"
    assert Path(chunk.log_path) == it / "train_log.log"
    assert (it / "train_log.log").read_text() == (src / "train_log.log").read_text()
    assert Path(chunk.episode_data_dir).resolve() == (src / "episode_data").resolve()
    assert (chunk.start_episode, chunk.end_episode) == (0, 2)

    nets = run_root / "models" / "iter_001" / "Standard_WLTC_WVUINTER" / "net_params"
    assert Path(chunk.model_dir) == nets
    # eval_sweep.sh 가 찾는 이름: actor_iter001_ep<N>.pkl
    for key in ("actor", "critic", "alpha"):
        link = nets / f"{key}_iter001_ep2.pkl"
        assert link.is_symlink() and link.read_bytes() == key.encode()
    assert json.load(open(it / "seed_source.json"))["seed_chunk_dir"] == str(src.resolve())


def test_seed_iteration_rejects_a_directory_without_training_artifacts(tmp_path):
    with pytest.raises(RuntimeError, match="seed_chunk_dir"):
        mlr._seed_iteration_from_existing_run(
            tmp_path / "run", _args(seed_chunk_dir=str(tmp_path / "nope")),
            iteration=1, chunk_result_cls=ChunkResult)


# ── reward 파일 = seed reward, bootstrap 후보로 등록 ─────────────────────────


# ── main 배선 ────────────────────────────────────────────────────────────────


# ── 실데이터: seed61 baseline SAC run ────────────────────────────────────────
