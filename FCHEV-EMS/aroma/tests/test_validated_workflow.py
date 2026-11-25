"""Contract, candidate selection, matched controls and resume/confirmation regressions."""
import copy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import candidate_validation as cv
import validated_workflow as vw
from reward_patcher import patch_method_in_file
import main_ldri_refine as main
from arguments_ldri import get_ldri_args
from prompt_builder import extract_method_source


@pytest.fixture
def args(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["test", "--refinement_protocol", "validated"])
    args = get_ldri_args()
    args.scenario_validation = False  # These fixtures have synthetic checkpoint paths.
    args.cycle_segment_validation = False
    return args


@pytest.fixture
def baseline():
    return extract_method_source(str(Path(cv.__file__).parent / "agentEMS_val_base.py"), "EMS", "get_reward")


def test_baseline_and_different_weight_directions_are_eligible(args, baseline):
    for scale in (.8, 1., 1.2):
        source = baseline.replace("h2_cost = self.w_h2", f"h2_cost = {scale} * self.w_h2")
        result = cv.verify_candidate(source, args)
        assert result["status"] == "pass", result
        assert result["probe_count"] == 243 + len(cv.fc_event_probes()) + len(cv.battery_event_probes())


@pytest.mark.parametrize("injection", ["self.SOC = 0.6", "self.info['SOC'] = 0.6; self.SOC = 0.6",
                                       "np.random.seed(0)", "while True: pass"])
def test_physics_mutation_and_non_arithmetic_code_rejected(args, baseline, injection):
    source = baseline.replace("    soc =", "    " + injection + "\n    soc =", 1)
    assert cv.verify_candidate(source, args)["checks"]["code_contract"] == "fail"


def test_nonfinite_and_forged_logs_fail(args, baseline):
    nan = baseline.replace("return reward", "return float('nan')")
    assert cv.verify_candidate(nan, args)["status"] == "fail"
    forged = baseline.replace("'objective_cost': float(objective_cost)", "'objective_cost': 0.0")
    assert cv.verify_candidate(forged, args)["checks"]["logging_consistency"] == "fail"


def test_missing_probe_attribute_is_inconclusive_not_pass(args, baseline):
    source = baseline.replace("soc = float(self.SOC)", "soc = float(self.unknown_sensor)")
    assert cv.verify_candidate(source, args)["status"] == "inconclusive"


def trial(fuel, seed=61, episodes=400, **metrics):
    return {"status": "complete", "seed": seed, "episodes": episodes,
            "conditions_id": "same", "candidate_id": str(fuel),
            "metrics": {"fuel_gkm": fuel, "fuel_early_tail_gkm": fuel,
                        "fuel_late_tail_gkm": fuel, "min_in_bounds": 100,
                        "soc_min": .5, "soc_max": .7, "fc_loss": .0001, "batt_loss": .00001,
                        "fuel_metric_basis": vw.DETERMINISTIC_FUEL_BASIS, **metrics}}


def test_imported_tail_is_not_reduced_to_last_ten_percent_twice():
    records = [dict(episode=n, fuel_gkm=float(n), soc_in_bounds=100,
                    fc_loss=.0001, batt_loss=.00001, soc_min=.5, soc_max=.7)
               for n in range(360, 400)]
    result = vw.aggregate_evaluations(records, total_episodes=400)
    assert result["tail_episodes"] == list(range(360, 400))
    assert result["fuel_gkm"] == 379.5


def test_manifest_ignores_installed_reward_but_detects_physics_change(args, baseline, tmp_path):
    args.reward_file = str(tmp_path / "plant.py")
    Path(args.reward_file).write_text("class EMS:\n    value = 1\n" + "\n".join("    " + l for l in baseline.splitlines()))
    before = vw._manifest(args)
    patch_method_in_file(args.reward_file, baseline.replace("self.w_h2", "self.w_h2 * 1.1"))
    assert vw._manifest(args) == before
    Path(args.reward_file).write_text(Path(args.reward_file).read_text().replace("value = 1", "value = 2"))
    assert vw._manifest(args) != before


def test_real_cpu_trials_are_isolated_and_reward_scaling_does_not_fake_fuel(
        args, baseline, tmp_path, monkeypatch):
    """Real plant + SAC initialization + checkpoints, 64 steps, no gradient updates.

    Changing a cost coefficient cannot change physical evaluation without learning.
    This also exercises runtime logging checks and trial artifact/cache wiring.
    """
    import env_ldri
    original_make_env = env_ldri.make_env_ldri
    def short_env(args, force_reload_agent=True):
        env, args = original_make_env(args, force_reload_agent)
        env.speed_list = env.speed_list[:64]
        env.acc_list = env.acc_list[:64]
        args.episode_steps = 64
        return env, args
    monkeypatch.setattr(env_ldri, "make_env_ldri", short_env)
    args.cuda = False
    args.seed = 61
    args.buffer_size = 512
    args.chunk_episodes = 2
    args.reward_file = main._resolve_input_path(args.reward_file)
    evaluator = vw.TrialEvaluator(args, tmp_path, main, {"test": "short_cpu"})
    before = Path(args.reward_file).read_bytes()
    control = evaluator(baseline, 2, 61)
    source = baseline.replace("h2_cost = self.w_h2", "h2_cost = 1.1 * self.w_h2")
    candidate = evaluator(source, 2, 61)
    assert control["status"] == candidate["status"] == "complete"
    assert control["metrics"]["fuel_gkm"] == candidate["metrics"]["fuel_gkm"]
    assert Path(control["chunk"]["model_dir"]) != Path(candidate["chunk"]["model_dir"])
    assert evaluator(baseline, 2, 61) == control
    assert Path(args.reward_file).read_bytes() == before
    assert control["learning_rate_config"] == candidate["learning_rate_config"]
    assert control["learning_rate_config"]["lr_schedule_episodes"] == args.chunk_episodes
    rows = [json.loads(line) for line in Path(control["evaluation_evidence"]).read_text().splitlines()]
    import numpy as np
    for row in rows:
        assert Path(row["checkpoint_path"]).is_file()
        with np.load(row["trajectory_path"]) as trace:
            assert len(trace["policy_action"]) == 64
            assert row["physical_evidence"]["scalars"]["soc_final"] == trace["SOC"][-1]
            assert row["physical_evidence"]["scalars"]["fc_load_change_count"] == int(np.sum(trace["d_l_c"] > 0))
    assert Path(control["physical_evidence_path"]).is_file()

    # Import those real checkpoints. Baseline import and subsequent cache reuse
    # must never call train_chunk, even for the pilot control or final baseline.
    import shutil
    import runner_ldri
    from reward_patcher import ensure_logging_contract
    original = tmp_path / "saved_baseline"
    (original / "net_params").mkdir(parents=True)
    (original / "episode_data").symlink_to(control["chunk"]["episode_data_dir"], target_is_directory=True)
    for episode in (0, 1):
        shutil.copyfile(Path(control["chunk"]["model_dir"]) / f"actor_iter001_ep{episode}.pkl",
                        original / "net_params" / f"actor_params_ep{episode}.pkl")
    (original / "train_log.log").write_text(
        "Random seeds have been set to 61 !\ncycle name: Standard_WLTC_WVUINTER\n"
        "initial SOC: 0.6\nSOC-MODE: CS\nepi 0: data\nepi 1: data\n")
    args.seed_chunk_dir = str(original)
    args.seed_reward_file = str(Path(cv.__file__).parent / "agentEMS_val_base.py")
    args.pilot_episodes = 1
    manifest = vw._manifest(args)
    source = ensure_logging_contract(baseline, cv.REQUIRED_KEYS)
    def forbidden_training(*a, **kw):
        pytest.fail("Imported baseline must not train")
    monkeypatch.setattr(runner_ldri.RunnerLDRI, "train_chunk", forbidden_training)
    imported_evaluator = vw.TrialEvaluator(args, tmp_path / "import_run", main, manifest)
    original_log = (original / "train_log.log").read_bytes()
    imported = imported_evaluator(source, 2, 61)
    assert imported["status"] == "complete", imported
    assert imported["trained_episodes"] == 0
    # Identical physical measurements, with distinct provenance paths for reevaluation.
    def without_paths(value):
        if isinstance(value, dict):
            return {k: without_paths(v) for k, v in value.items() if not k.endswith("_path")}
        if isinstance(value, list):
            return [without_paths(v) for v in value]
        return value
    assert without_paths(imported["metrics"]) == without_paths(control["metrics"])
    imported_rows = [json.loads(line) for line in Path(imported["evaluation_evidence"]).read_text().splitlines()]
    assert all(Path(row["checkpoint_path"]).is_file() for row in imported_rows)
    assert imported["baseline_provenance"] == manifest["imported_baseline"]
    pilot = imported_evaluator(source, 1, 61)
    assert pilot["status"] == "complete"
    assert pilot["trained_episodes"] == 0
    assert imported_evaluator(source, 2, 61) == imported
    assert (original / "train_log.log").read_bytes() == original_log
    assert Path(args.reward_file).read_bytes() == before


@pytest.mark.parametrize("incomplete_episode, expected", [(0, "complete"), (9, "invalid")])
def test_incomplete_eval_drive_only_invalidates_the_tail(
        args, baseline, tmp_path, monkeypatch, incomplete_episode, expected):
    """An untrained ep0 policy that fails the drive must not abort the pilot
    (20260923 seed41: every candidate died at ep0); an incomplete tail drive
    must still make the trial invalid."""
    import env_ldri
    import runner_ldri
    original_make_env = env_ldri.make_env_ldri
    def short_env(args, force_reload_agent=True):
        env, args = original_make_env(args, force_reload_agent)
        env.speed_list = env.speed_list[:64]
        env.acc_list = env.acc_list[:64]
        args.episode_steps = 64
        return env, args
    monkeypatch.setattr(env_ldri, "make_env_ldri", short_env)
    original_eval = runner_ldri.RunnerLDRI._evaluate_policy_sac
    def eval_with_failed_drive(self):
        m = original_eval(self)
        if self.current_episode == incomplete_episode:
            m.update(ep_len=40, tracking_success=False, failure_reason="soc_floor",
                     paper_fuel=dict(m["paper_fuel"], equivalent_g_per_km=float("nan")))
        return m
    monkeypatch.setattr(runner_ldri.RunnerLDRI, "_evaluate_policy_sac", eval_with_failed_drive)
    args.cuda = False
    args.seed = 61
    args.buffer_size = 1024
    args.chunk_episodes = 10
    args.reward_file = main._resolve_input_path(args.reward_file)
    result = vw.TrialEvaluator(args, tmp_path, main, {"test": "incomplete_eval"})(baseline, 10, 61)
    assert result["status"] == expected, result
    assert result["trained_episodes"] == 10
    rows = [json.loads(line) for line in Path(result["evaluation_evidence"]).read_text().splitlines()]
    assert [r["episode"] for r in rows] == list(range(10))
    assert rows[incomplete_episode]["incomplete_drive"] and rows[incomplete_episode]["fuel_gkm"] is None
    if expected == "complete":
        assert result["metrics"]["tail_episodes"] == [9]
