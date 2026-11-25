"""2026-10-15 seed41/61/81 v3 review: binding orchestrator CHANGE_SPEC, unit-consistent start economics,
and forking a measured baseline into a new run (proposal-side code changed, training identical)."""
import json
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import main_ldri_refine as main
import sequential_workflow as sw
from arguments_ldri import get_ldri_args
from candidate_validation import candidate_id
from prompt_builder import extract_method_source
from reward_patcher import ensure_logging_contract
from test_cost_scale_check import OBJECTIVE, _rollout


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


def degradation_scaled(source, k):
    return source.replace("fcs_soh_cost = self.w_fc", f"fcs_soh_cost = {k} * self.w_fc").replace(
        "batt_soh_cost = self.w_batt", f"batt_soh_cost = {k} * self.w_batt")


def with_ohmic(source):
    return source.replace(OBJECTIVE, f"{OBJECTIVE} + 1.0 * float(self.P_batt_loss_kw)")


SPEC_X5 = {"term_ratio": {"fcs_soh_cost": 5.0, "batt_soh_cost": 5.0}, "extra_terms": "unchanged"}


# ---- 2. orchestrator CHANGE_SPEC ---------------------------------------------------------------

def test_change_spec_parser_takes_the_last_valid_block_and_rejects_malformed_specs():
    text = ('draft ```json\n{"term_ratio": {"h2_cost": 2}}\n```\nfinal:\n```json\n'
            '{"term_ratio": {"fcs_soh_cost": 5, "soc_cost": "changed"}, "extra_terms": "added"}\n```')
    assert sw.parse_change_spec(text) == {"term_ratio": {"fcs_soh_cost": 5.0, "soc_cost": "changed"},
                                          "extra_terms": "added"}
    assert sw.parse_change_spec('```json\n{"term_ratio": {"fcs_soh_cost": 5}}\n```')["extra_terms"] == "unchanged"
    for bad in ("no json", '```json\n{"term_ratio": {"w_fc": 5}}\n```', '```json\n{"term_ratio": {"h2_cost": -1}}\n```',
                '```json\n{"term_ratio": {"h2_cost": 2}, "extra_terms": "some"}\n```'):
        assert sw.parse_change_spec(bad) is None


def test_seed81_case_proposal_that_ignores_the_orchestrator_is_rejected(args, source, tmp_path):
    """Orchestrator: w_fc and w_batt x5, no new terms. Trained: x2 plus an ohmic term."""
    path = _rollout(tmp_path / "r.npz", fc_start_steps=(0, 120))
    bad = sw.verify_change_spec(with_ohmic(degradation_scaled(source, 2.0)), source, SPEC_X5, path, args)
    assert bad["status"] == "fail"
    assert "fcs_soh_cost: spec 5.0, measured ratio 2.0" in bad["reason"]
    assert "batt_soh_cost: spec 5.0" in bad["reason"] and "extra_terms: spec unchanged" in bad["reason"]
    good = sw.verify_change_spec(degradation_scaled(source, 5.0), source, SPEC_X5, path, args)
    assert good["status"] == "pass" and good["measured"]["fcs_soh_cost"]["ratio"] == pytest.approx(5.0)


def test_unlisted_terms_must_stay_unchanged_and_changed_must_change(args, source, tmp_path):
    path = _rollout(tmp_path / "r.npz", fc_start_steps=(0, 120))
    touched_h2 = source.replace("h2_cost = self.w_h2", "h2_cost = 1.05 * self.w_h2")
    assert sw.verify_change_spec(degradation_scaled(touched_h2, 5.0), source, SPEC_X5, path, args)["status"] == "fail"
    spec = {"term_ratio": {"soc_cost": "changed"}, "extra_terms": "unchanged"}
    assert sw.verify_change_spec(source, source, spec, path, args)["status"] == "fail"
    added = {"term_ratio": {}, "extra_terms": "added"}
    assert sw.verify_change_spec(with_ohmic(source), source, added, path, args)["status"] == "pass"


def _baseline(tmp_path, source):
    traj = tmp_path / "trial" / "deterministic_rollouts"
    traj.mkdir(parents=True)
    _rollout(traj / "episode_00399.npz", fc_start_steps=(0, 120))
    return {"status": "complete", "episodes": 400, "seed": 41, "candidate_id": "b", "reward_source": source,
            "trajectory_dir": str(traj), "metrics": {}, "final_metrics": {}}


def test_proposer_must_implement_the_orchestrator_spec_and_repairs_on_mismatch(args, source, tmp_path):
    args.multi_agent_review = True
    baseline = _baseline(tmp_path, source)
    replies = [with_ohmic(degradation_scaled(source, 2.0)), degradation_scaled(source, 5.0)]
    prompts, proposals = [], []

    class Client:
        provider, model = "anthropic", "test"
        def complete(self, **kw):
            prompts.append(kw["prompt"])
            if "Mediate" in kw["prompt"]:
                return "Raise both degradation weights x5, no new terms.\n```json\n" + json.dumps(SPEC_X5) + "\n```"
            if "Generate ONE" in kw["prompt"]:
                proposals.append(kw["prompt"])
                return f"```python\n{replies[len(proposals) - 1]}\n```"
            return "hyp"

    iter_dir = tmp_path / "iter"
    iter_dir.mkdir()
    result = sw.propose_reward(args=args, client=Client(), champion=baseline,
                               summary={"baseline": baseline, "iterations": []}, iter_dir=iter_dir)
    assert result == degradation_scaled(source, 5.0)
    assert "Mediate" in prompts[4] and "CHANGE_SPEC" in prompts[4] and "SELECTION-PRICED" in prompts[4]
    assert "BINDING ORCHESTRATOR CHANGE_SPEC" in proposals[0] and json.dumps(SPEC_X5) in proposals[0]
    assert "orchestrator_conformance" in proposals[1]
    review = json.loads((iter_dir / "review.json").read_text())
    assert review["change_spec"] == SPEC_X5
    assert review["verification"]["orchestrator_conformance"]["status"] == "pass"


# ---- 3. start economics in consistent units ------------------------------------------------------

def _start_rollout(path):
    """100 s, 1 km: FC off at 0-1 (reset), on, off 40-42 and 70-71 (avoidable), off again 95-99 (drive end)."""
    on = np.ones(100, bool)
    on[[0, 1, 40, 41, 42, 70, 71, 95, 96, 97, 98, 99]] = False
    h2 = np.where(on, 0.06, 0.0)
    h2[50:60] = 0.2
    d_ss = np.zeros(100)
    d_ss[[2, 43, 72]] = 1.96
    np.savez_compressed(path, h2_fcs=h2, d_s_s=d_ss, travel=np.linspace(10., 1000., 100), dt_s=1.0)
    return path


def test_start_economics_separates_price_from_hydrogen_and_uses_guard_units(tmp_path):
    traj = tmp_path / "deterministic_rollouts"
    traj.mkdir()
    _start_rollout(traj / "episode_00399.npz")
    trial = {"candidate_id": "base", "episodes": 400, "trajectory_dir": str(traj),
             "final_metrics": {"fuel_gkm": 10.0}}
    note = sw._start_economics_note(trial, {"fuel_gkm_max": 10.2})
    assert "3 starts; 2 of them follow an FC-off interval inside the drive, totalling 5 s off" in note
    assert "1.19 USD per drive = 119 USD per 100 km" in note  # 1.96e-5 * 60800 over a 1 km drive
    assert "burns 0.06 g H2 per s" in note and "at most 0.3 g per drive = 0.3 g/km" in note
    assert "avoids up to 2 starts" in note
    assert "10.2 - 10 = 0.2 g/km = 0.2 g per drive" in note
    assert "PRICE comparison, never hydrogen that must be burned" in note


def test_start_economics_states_the_soc_cost_of_bridging(tmp_path):
    """Staying on through FC-off intervals charges the battery: the note sizes it against the drift guard."""
    traj = tmp_path / "deterministic_rollouts"
    traj.mkdir()
    _start_rollout(traj / "episode_00399.npz")
    trial = {"candidate_id": "base", "episodes": 400, "trajectory_dir": str(traj),
             "final_metrics": {"fuel_gkm": 10.0, "paper_fuel": {"fc_efficiency": 0.5}}}
    note = sw._start_economics_note(trial, {"fuel_gkm_max": 10.5, "soc_drift_abs_max": .05})
    # 0.3 g x 33.33 kWh/kg x 0.5 = 0.005 kWh into a 1.56 kWh pack
    assert "= 0.005 kWh" in note and "up to +0.0032 SOC" in note
    assert "|SOC_final - SOC_initial| <= 0.05" in note
    assert "Charge-sustaining side" not in sw._start_economics_note(trial, {"fuel_gkm_max": 10.5})


def test_every_review_stage_gets_the_start_economics(args, source, tmp_path):
    args.multi_agent_review, args.proposal_attempts = True, 1
    traj = tmp_path / "trial" / "deterministic_rollouts"
    traj.mkdir(parents=True)
    path = _rollout(traj / "episode_00399.npz", steps=100)  # every replay field, then the start pattern
    data = dict(np.load(path))
    start = np.load(_start_rollout(tmp_path / "s.npz"))
    data.update(h2_fcs=start["h2_fcs"], d_s_s=start["d_s_s"])
    np.savez_compressed(path, **data)
    baseline = {"status": "complete", "episodes": 400, "seed": 41, "candidate_id": "b", "reward_source": source,
                "trajectory_dir": str(traj), "metrics": {}, "final_metrics": {}}
    prompts = []

    class Client:
        provider, model = "anthropic", "test"
        def complete(self, **kw):
            prompts.append(kw["prompt"])
            return "hyp"

    sw.propose_reward(args=args, client=Client(), champion=baseline, summary={"baseline": baseline, "iterations": []},
                      iter_dir=tmp_path)
    assert prompts and all("FC START ECONOMICS" in p and "UNIT RULES" in p for p in prompts
                           if "Return ONLY the CHANGE_SPEC" not in p)


# ---- fork: reuse a measured baseline in a new run ------------------------------------------------

def _factory(root_for_trials, calls):
    class Evaluator:
        def __init__(self, args, root, api, manifest):
            self.root, self.conditions_id = Path(root), sw._digest(manifest)

        def __call__(self, reward, episodes, seed):
            calls.append(candidate_id(reward))
            rid = candidate_id(reward)
            trial_dir = self.root / "trials" / rid[:12]
            model = trial_dir / "models"
            model.mkdir(parents=True, exist_ok=True)
            (model / "actor_iter001_ep399.pkl").touch()
            (trial_dir / "deterministic_evaluations.jsonl").write_text("")
            fuel = 10. if "1.3" not in reward else 9.8
            return {"status": "complete", "episodes": 400, "seed": seed, "conditions_id": self.conditions_id,
                    "identity": {"conditions_id": self.conditions_id}, "candidate_id": rid, "reward_source": reward,
                    "evaluation_evidence": str(trial_dir / "deterministic_evaluations.jsonl"),
                    "chunk": {"model_dir": str(model), "log_path": str(trial_dir / "train.log")},
                    "metrics": {"fuel_gkm": fuel, "fc_loss": 1e-4, "batt_loss": 2e-4},
                    "final_metrics": {"episode": 399, "fuel_metric_basis": sw.DETERMINISTIC_FUEL_BASIS,
                                      "fuel_gkm": fuel, "fc_loss": 1e-4, "batt_loss": 2e-4, "soc_in_bounds": 100.,
                                      "soc_min": .5, "soc_max": .7, "paper_fuel": {"drive_mileage_km": 50.},
                                      "physical_evidence": {"scalars": {"soc_final_minus_initial": 0.}},
                                      "power_violations": {"trace_available": True, "steps_by_reason": {}}}}
    return Evaluator


def _source_run(args, monkeypatch, root):
    args.ldri_iterations = 1
    calls = []
    sw.run_sequential_workflow(args, root, False, api=main, trial_factory=_factory(root, calls))
    assert len(calls) == 1
    return calls


def test_fork_reuses_the_baseline_and_pairs_new_candidates_with_it(args, source, monkeypatch, tmp_path):
    old_root, new_root = tmp_path / "old", tmp_path / "new"
    _source_run(args, monkeypatch, old_root)
    # The source run was written by older proposal-side code: only those differences are tolerated.
    manifest_path = old_root / "validation_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    for path in manifest["source_hashes"]:
        if Path(path).name in sw.FORK_PROPOSAL_SIDE_FILES:
            manifest["source_hashes"][path] = "older"
    manifest["conditions"].pop("cost_scale_max_ratio")
    manifest["selection_policy"] = "older adoption rule text"  # judged actors differently, trained them alike
    manifest["conditions"]["extra_cost_max_h2_ratio"] = 1.0
    manifest["conditions"]["cost_max_fuel_increase"] = .02  # a stricter guard judged the source run
    manifest["conditions"].pop("cost_max_soc_drift")         # written before the drift guard existed
    manifest_path.write_text(json.dumps(manifest))
    old_conditions = json.loads((old_root / "run_summary.json").read_text())["baseline"]["conditions_id"]

    monkeypatch.setattr(main, "_init_llm_client", lambda a: object())
    args.ldri_iterations, args.fork_from_run_root = 2, str(old_root)
    calls, better = [], source.replace("h2_cost = self.w_h2", "h2_cost = 1.3 * self.w_h2")
    result = sw.run_sequential_workflow(args, new_root, False, api=main, trial_factory=_factory(new_root, calls),
                                        proposal_fn=lambda **kw: better)
    assert calls == [candidate_id(better)]  # the baseline was not trained again
    rows = result["iterations"]
    assert rows[0]["decision"] == "baseline_trained" and rows[0]["forked_from"]["run_root"] == str(old_root.resolve())
    assert rows[1]["decision"] == "replace_champion" and rows[1]["verdict"]["status"] == "pass"
    forked = result["forked_from"]
    assert forked["source_conditions_id"] == old_conditions
    assert forked["differing_proposal_side_sources"] == sorted(sw.FORK_PROPOSAL_SIDE_FILES)
    assert forked["selection_policy_changed"] is True
    assert forked["differing_proposal_side_args"] == {"extra_cost_max_h2_ratio": [1.0, None],
                                                      "cost_scale_max_ratio": [None, 1.0],
                                                      "cost_max_fuel_increase": [.02, .05],
                                                      "cost_max_soc_drift": [None, .05]}
    baseline = result["baseline"]
    assert baseline["conditions_id"] == result["champion"]["conditions_id"]
    assert baseline["forked_conditions_id"] == old_conditions
    assert str(old_root) not in json.dumps(baseline)
    assert Path(baseline["evaluation_evidence"]).is_file()
    assert "fork_from_run_root" not in json.loads((new_root / "validation_manifest.json").read_text())["conditions"]


@pytest.mark.parametrize("change", ["w_soc", "training_code"])
def test_fork_refuses_different_training_conditions_or_code(args, source, monkeypatch, tmp_path, change):
    old_root = tmp_path / "old"
    _source_run(args, monkeypatch, old_root)
    if change == "w_soc":
        args.w_soc = args.w_soc + 1
    else:
        manifest_path = old_root / "validation_manifest.json"
        manifest = json.loads(manifest_path.read_text())
        sac = next(p for p in manifest["source_hashes"] if Path(p).name == "sac.py")
        manifest["source_hashes"][sac] = "older"
        manifest_path.write_text(json.dumps(manifest))
    args.ldri_iterations, args.fork_from_run_root = 2, str(old_root)
    with pytest.raises(RuntimeError, match="sac.py" if change == "training_code" else "w_soc"):
        sw.run_sequential_workflow(args, tmp_path / "new", False, api=main, trial_factory=_factory(tmp_path, []),
                                   proposal_fn=lambda **kw: source)


def test_fork_cannot_be_combined_with_resume(args, monkeypatch, tmp_path):
    _source_run(args, monkeypatch, tmp_path / "old")
    args.fork_from_run_root = str(tmp_path / "old")
    with pytest.raises(RuntimeError, match="cannot be combined"):
        sw.run_sequential_workflow(args, tmp_path / "old", True, api=main, trial_factory=_factory(tmp_path, []))


def test_fork_tolerates_the_development_module_only_without_development_cycles():
    manifest = {"conditions": {}, "selection_policy": "rule text",
                "source_hashes": {"/x/development_validation.py": "h", "/x/runner_ldri.py": "r"},
                "development_validation": {"cycles": []}}
    assert sw._fork_comparable(manifest)["source_hashes"] == {"/x/runner_ldri.py": "r"}
    assert "selection_policy" not in sw._fork_comparable(manifest)
    manifest["development_validation"]["cycles"] = ["Standard_WLTC"]
    assert "/x/development_validation.py" in sw._fork_comparable(manifest)["source_hashes"]
