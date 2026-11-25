"""Free proposals, total-cost adoption with guard bands, and compact real trial artifacts."""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import main_ldri_refine as main
import sequential_workflow as sw
from arguments_ldri import get_ldri_args
from candidate_validation import candidate_id, verify_candidate
from prompt_builder import extract_method_source
from reward_patcher import ensure_logging_contract
from validated_workflow import TrialEvaluator


@pytest.fixture
def args(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["test"])
    args = get_ldri_args()
    args.seed, args.skip_patch = 41, True
    args.reward_term_catalog = False  # free-form fake proposals; the catalog is covered by test_reward_terms.py
    return args


@pytest.fixture
def source():
    return ensure_logging_contract(extract_method_source(main._resolve_input_path("agentEMS_val_base.py"),
                                                         "EMS", "get_reward"), sw.REQUIRED_KEYS)


def trial(fuel=10., fc=.0001, batt=.0002, **overrides):
    return {"status": "complete", "episodes": 400, "seed": 41, "conditions_id": "same",
            "candidate_id": str(fuel), "metrics": {"fuel_gkm": fuel, "fc_loss": fc, "batt_loss": batt},
            "final_metrics": {"episode": 399, "fuel_metric_basis": sw.DETERMINISTIC_FUEL_BASIS,
                              "fuel_gkm": fuel, "fc_loss": fc, "batt_loss": batt,
                              "soc_in_bounds": 100., "soc_min": .5, "soc_max": .7,
                              "power_violations": {"trace_available": True, "steps_by_reason": {}},
                              "paper_fuel": {"drive_mileage_km": 50.},
                              "physical_evidence": {"scalars": {"soc_final_minus_initial": 0.}},
                              **overrides}}


@pytest.mark.parametrize("fuel,fc,batt,accepted", [
    (9.999999999, .0001, .0002, True),     # cheaper by a hair
    (10., .0001, .0002, False),            # tie in total cost
    (10.15, .00005, .0002, True),          # more hydrogen, much less FC wear: lower total cost
    (10.45, .00005, .0002, True),          # more hydrogen, inside the 5% guard
    (10.55, .00005, .0002, False),         # cheaper, but fuel past the 5% guard
    (10., .00005, .000219, True),          # battery inside the 10% guard
    (10., .00005, .000221, False),         # battery past the guard
    (9., .00011, .0002, False),            # less fuel, but the extra FC wear costs more
    (11., .00001, .00002, False)])         # far cheaper, fuel past the guard
def test_total_cost_is_mandatory_and_guards_bound_fuel_and_battery(args, fuel, fc, batt, accepted):
    assert (sw.compare_policies(trial(fuel, fc, batt), trial(), args)["status"] == "pass") == accepted


def test_final_policy_not_tail_mean_decides_adoption(args):
    candidate = trial(10.1)
    candidate["metrics"]["fuel_gkm"] = 8.
    assert sw.compare_policies(candidate, trial(), args)["status"] == "fail"
    candidate = trial(9.99)
    candidate["metrics"]["fuel_gkm"] = 11.
    assert sw.compare_policies(candidate, trial(), args)["status"] == "pass"


@pytest.mark.parametrize("change", [{"episode": 398}, {"soc_in_bounds": 97.9},
                                     {"fuel_gkm": float("nan")}, {"incomplete_drive": True},
                                     {"fc_loss": -1.}, {"soc_max": 1.1}])
def test_invalid_evidence_cannot_win(args, change):
    assert sw.compare_policies(trial(9., **change) if "fuel_gkm" not in change else trial(**change),
                               trial(), args)["status"] == "fail"


def test_unpaired_seed_and_missing_final_evidence_cannot_win(args):
    candidate = trial(9.)
    candidate["seed"] = 42
    assert sw.compare_policies(candidate, trial(), args)["reason"] == "unpaired_conditions"
    candidate.pop("final_metrics")
    assert not sw.policy_valid(candidate, args)


def joint_change(source, scale="1.1"):
    return source.replace("h2_cost = self.w_h2", f"h2_cost = {scale} * self.w_h2").replace(
        "batt_soh_cost = self.w_batt", "batt_soh_cost = 1.2 * self.w_batt")


def test_free_joint_proposal_six_calls_and_resume_without_repeating_reviews(args, source, tmp_path):
    changed = joint_change(source)
    assert verify_candidate(changed, args)["status"] == "pass"
    champion = {**trial(), "reward_source": source}
    summary = {"baseline": champion, "iterations": []}
    calls = []
    class Client:
        provider, model = "anthropic", "test"
        def complete(self, **kw):
            calls.append(kw)
            if "Generate ONE" in kw["prompt"]:
                return f"```python\n{changed}\n```"
            if "Mediate" in kw["prompt"]:
                return 'Scale h2 and battery.\n```json\n{"term_ratio": {"h2_cost": 1.1, "batt_soh_cost": 1.2}}\n```'
            return "One bounded hypothesis."
    client = Client()
    result = sw.propose_reward(args=args, client=client, champion=champion, summary=summary, iter_dir=tmp_path)
    assert result == changed
    assert len(calls) == 6
    assert max(c["max_tokens"] for c in calls[:4]) == 700
    assert "jointly change ANY" in calls[-1]["prompt"]
    assert not list(tmp_path.glob("candidate_review*"))
    assert not list(tmp_path.glob("*prompt*.md"))
    assert sw.propose_reward(args=args, client=client, champion=champion, summary=summary, iter_dir=tmp_path) == changed
    assert len(calls) == 6
    assert len(json.loads((tmp_path / "llm_usage.json").read_text())["records"]) == 6


def test_repair_budget_only_one_trained_proposal_and_no_duplicate_retry_loop(args, source, tmp_path):
    args.multi_agent_review = False
    champion = {**trial(), "reward_source": source}
    calls = []
    class Client:
        provider, model = "anthropic", "test"
        def complete(self, **kw):
            calls.append(kw)
            return f"```python\n{source}\n```"
    result = sw.propose_reward(args=args, client=Client(), champion=champion,
                              summary={"baseline": champion, "iterations": []}, iter_dir=tmp_path)
    assert result is None
    assert len(calls) == args.proposal_attempts
    assert not (tmp_path / "candidate.py").exists()


def test_malformed_output_is_repaired_without_repeating_specialists(args, source, tmp_path):
    champion = {**trial(), "reward_source": source}
    calls = []
    changed = joint_change(source)
    class Client:
        provider, model = "anthropic", "test"
        def complete(self, **kw):
            calls.append(kw)
            return f"```python\n{changed}\n```" if len(calls) == 8 else "No code here."
    result = sw.propose_reward(args=args, client=Client(), champion=champion,
                              summary={"baseline": champion, "iterations": []}, iter_dir=tmp_path)
    # 4 reviewers + orchestrator + its one CHANGE_SPEC repair (no JSON given) + 2 proposals
    assert result == changed and len(calls) == 8
    assert "orchestrator_spec" in json.loads((tmp_path / "review.json").read_text())["stages"]
    assert "could not find function" in calls[-1]["prompt"]


def test_two_rounds_rollback_use_champion_one_full_trial_each_and_resume(args, source, monkeypatch, tmp_path):
    proposals = [joint_change(source), joint_change(source, "1.3")]
    seen_champions, calls = [], []
    class Evaluator:
        def __init__(self, *a):
            pass
        def __call__(self, reward, episodes, seed):
            calls.append((reward, episodes, seed))
            fuel, fc = (9., .00011) if reward == proposals[0] else (9.9, .00009) if reward == proposals[1] else (10., .0001)
            result = {**trial(fuel, fc), "reward_source": reward, "candidate_id": candidate_id(reward),
                      "chunk": {"model_dir": str(tmp_path / candidate_id(reward)), "log_path": "train.log"}}
            model = Path(result["chunk"]["model_dir"])
            model.mkdir(exist_ok=True)
            (model / "actor_iter001_ep399.pkl").touch()
            return result
    def propose(**kw):
        seen_champions.append(kw["champion"]["reward_source"])
        return proposals[len(seen_champions) - 1]
    monkeypatch.setattr(main, "_init_llm_client", lambda a: object())
    result = sw.run_sequential_workflow(args, tmp_path, False, api=main, trial_factory=Evaluator, proposal_fn=propose)
    assert [r["decision"] for r in result["iterations"]] == ["baseline_trained", "retain_champion", "replace_champion"]
    assert seen_champions == [source, source]
    assert len(calls) == 3 and all(c[1:] == (400, 41) for c in calls)
    assert result["final_selection"]["improvement_confirmed"]
    assert (tmp_path / "final_reward.py").read_text() == proposals[1]
    assert args.pilot_episodes == 0 and args.validation_max_degradation_ratio == 1.
    assert not list(tmp_path.glob("**/pilot_results.json"))
    sw.run_sequential_workflow(args, tmp_path, True, api=main, trial_factory=Evaluator, proposal_fn=propose)
    assert len(calls) == 3
    args.w_soc += 1
    with pytest.raises(RuntimeError, match="conditions/code changed"):
        sw.run_sequential_workflow(args, tmp_path, True, api=main, trial_factory=Evaluator, proposal_fn=propose)


def test_default_options_and_saved_protocol_restore(args):
    assert args.refinement_protocol == "sequential" and args.chunk_episodes == 400
    main._apply_resume_run_config(args, {"refinement_protocol": "validated"})
    assert args.refinement_protocol == "validated"
    args.chunk_episodes = 500
    with pytest.raises(ValueError, match="400"):
        sw._configure(args)


def test_compact_real_cpu_trial_keeps_metrics_but_only_final_raw_artifacts(args, source, tmp_path, monkeypatch):
    import env_ldri
    original = env_ldri.make_env_ldri
    def short_env(args, force_reload_agent=True):
        env, args = original(args, force_reload_agent)
        env.speed_list, env.acc_list = env.speed_list[:16], env.acc_list[:16]
        args.episode_steps = 16
        return env, args
    monkeypatch.setattr(env_ldri, "make_env_ldri", short_env)
    args.cuda, args.buffer_size, args.chunk_episodes = False, 128, 3
    args.reward_file = main._resolve_input_path(args.reward_file)
    evaluator = TrialEvaluator(args, tmp_path, main, {"test": "compact"})
    result = evaluator(source, 3, 41)
    assert result["status"] == "complete", result
    rows = [json.loads(s) for s in Path(result["evaluation_evidence"]).read_text().splitlines()]
    assert len(rows) == 3 and result["trained_episodes"] == 3
    assert result["final_metrics"]["episode"] == 2
    assert [r["checkpoint_path"] is not None for r in rows] == [False, False, True]
    assert [r["trajectory_path"] is not None for r in rows] == [False, False, True]
    assert len(list(Path(result["trajectory_dir"]).glob("*.npz"))) == 1
    assert len(list(Path(result["chunk"]["episode_data_dir"]).glob("*.mat"))) == 1
    assert len(list(Path(result["chunk"]["model_dir"]).glob("actor_iter001_ep*.pkl"))) == 1
    assert evaluator(source, 3, 41) == result
