"""Sequential v3: total-cost deployment gate, search archive/edit_base, provenance, L6 rollback, L4 confirmation.

Fixture costs at 50 km (USD per 100 km): H2 0.7 * fuel, FC 121600 * fc_loss, battery 7581.6 * batt_loss;
the default trial (10 g/km, 1e-4, 2e-4) costs 7.00 + 12.16 + 1.52 = 20.68.
"""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import main_ldri_refine as main
import sequential_workflow as sw
from arguments_ldri import get_ldri_args
from candidate_validation import candidate_id
from prompt_builder import extract_method_source
from reward_patcher import ensure_logging_contract


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


def trial(fuel=10., fc=1e-4, batt=2e-4, seed=41, rid=None, src="src", **overrides):
    return {"status": "complete", "episodes": 400, "seed": seed, "conditions_id": "same",
            "candidate_id": rid or f"{fuel}-{fc}-{batt}", "reward_source": src,
            "metrics": {"fuel_gkm": fuel, "fc_loss": fc, "batt_loss": batt},
            "final_metrics": {"episode": 399, "fuel_metric_basis": sw.DETERMINISTIC_FUEL_BASIS,
                              "fuel_gkm": fuel, "fc_loss": fc, "batt_loss": batt,
                              "soc_in_bounds": 100., "soc_min": .5, "soc_max": .7,
                              "power_violations": {"trace_available": True, "steps_by_reason": {}},
                              "paper_fuel": {"drive_mileage_km": 50.},
                              "physical_evidence": {"scalars": {"soc_final_minus_initial": 0.}},
                              **overrides}}


def variant(source, scale):
    return source.replace("h2_cost = self.w_h2", f"h2_cost = {scale} * self.w_h2")


# ---- observed relation -------------------------------------------------------------------------

@pytest.mark.parametrize("c,relation", [
    ((9., 9e-5, 1.9e-4), "strict_pareto"),
    ((9., 1e-4, 1.9e-4), "cost_improved_noninferior"),
    ((10.2, .8e-4, 2e-4), "cost_tradeoff"),           # more fuel, cheaper through FC wear
    ((10., 9e-5, 2.1e-4), "cost_tradeoff"),           # more battery wear, cheaper through FC wear
    ((9., 1.1e-4, 1.9e-4), "objective_tradeoff"),     # less fuel, but the FC wear costs more
    ((10., 1e-4, 2e-4), "worse_or_equal"),
    ((11., 1.1e-4, 2e-4), "worse_or_equal"),
])
def test_observed_relation_classes(args, c, relation):
    assert sw.observed_relation(trial(*c), trial(), args) == relation


def test_observed_relation_invalid(args):
    assert sw.observed_relation(trial(9., soc_in_bounds=50.), trial(), args) == "invalid"


def drift(value):
    return {"physical_evidence": {"scalars": {"soc_final_minus_initial": value}}}


def test_deployment_gate_rejects_cost_ties_and_guard_excess(args):
    assert args.cost_max_fuel_increase == .05 and args.cost_max_batt_increase == .10
    assert args.cost_max_soc_drift == .05
    assert sw.compare_policies(trial(rid="same"), trial(), args)["status"] == "fail"  # tie in total cost
    # cheaper through FC wear, but fuel or battery loss just past its guard band: never deployed
    for candidate in (trial(10.51, .5e-4), trial(10., .5e-4, 2.21e-4)):
        assert sw.observed_relation(candidate, trial(), args) == "cost_tradeoff"
        assert sw.compare_policies(candidate, trial(), args)["status"] == "fail"
    assert sw.compare_policies(trial(10.49, .5e-4, 2.19e-4), trial(), args)["status"] == "pass"


@pytest.mark.parametrize("value,sustaining", [(.05, True), (-.05, True), (.051, False), (-.051, False),
                                               (None, False)])
def test_charge_sustaining_guard_is_absolute_and_fails_closed(args, value, sustaining):
    """Cheaper in every objective, but an FC idling into the battery is not charge sustaining."""
    candidate = trial(9., .5e-4, 1.9e-4, **drift(value))
    verdict = sw.compare_policies(candidate, trial(**drift(.185)), args)  # a drifting baseline does not loosen it
    assert verdict["checks"]["charge_sustaining"] is sustaining
    assert verdict["checks"]["total_cost_strictly_improved"] and verdict["checks"]["fuel_within_guard"]
    assert (verdict["status"] == "pass") is sustaining
    assert verdict["guards"]["soc_drift_abs_max"] == .05


def test_missing_drive_distance_fails_closed(args):
    candidate = trial(9., .5e-4, paper_fuel={})
    assert "missing_drive_distance_for_operating_cost" in sw.validity_failures(candidate, args)
    assert sw.compare_policies(candidate, trial(), args)["status"] == "fail"


# ---- L2 tail diagnostics -----------------------------------------------------------------------

def _write_tail(path, fuels, fc=1e-4, batt=2e-4):
    rows = [{"episode": 360 + i, "fuel_gkm": f, "fc_loss": fc, "batt_loss": batt} for i, f in enumerate(fuels)]
    rows.insert(0, {"episode": 10, "fuel_gkm": 99., "fc_loss": 1., "batt_loss": 1.})  # outside tail
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")


def test_tail_diagnostics_flags_lucky_final_checkpoint(tmp_path):
    path = tmp_path / "ev.jsonl"
    _write_tail(path, [10.0 + 0.01 * (i % 5) for i in range(39)] + [9.5])
    diag = sw.tail_diagnostics({"episodes": 400, "evaluation_evidence": str(path)})
    assert diag["available"] and diag["basis"] == "single_run_tail_diagnostic_not_a_gate"
    assert diag["metrics"]["fuel_gkm"]["n"] == 40
    assert diag["metrics"]["fuel_gkm"]["ep399_better_than_fraction"] == pytest.approx(39 / 40)
    assert diag["lucky_checkpoint"] is True


def test_tail_diagnostics_missing_evidence_is_explicit():
    assert sw.tail_diagnostics({"episodes": 400})["available"] is False


# ---- L3 archive / edit base --------------------------------------------------------------------

def _summary(args, entries, champion_id, baseline_id="base"):
    return {"archive": entries, "champion_id": champion_id, "baseline_id": baseline_id}


def _entry(rid, fuel, fc, batt, stale=0, parent=None, feasible=True):
    return {"reward_id": rid, "parent_id": parent, "iteration": 1, "reward_source": rid,
            "final_ep399": {"fuel_gkm": fuel, "fc_loss": fc, "batt_loss": batt},
            "operating_cost": sw.operating_cost(fuel, fc, batt, 50.),
            "guard_checks": {"charge_sustaining": feasible, "fuel_within_guard": True,
                             "battery_within_guard": True},
            "physics": {}, "tail": {"available": False}, "stale": stale, "children": 0}


def test_archive_members_are_cost_fuel_front_plus_baseline_and_champion(args):
    # costs at 50 km: base 20.68, A 20.56 (least fuel), B 20.11 (cheapest feasible), dominated 21.29
    entries = [_entry("base", 10., 1e-4, 2e-4), _entry("A", 9.7, 1.01e-4, 1.96e-4),
               _entry("B", 9.9, 0.96e-4, 1.99e-4), _entry("dominated", 9.95, 1.05e-4, 2.05e-4),
               _entry("drift", 9., .5e-4, 2e-4, feasible=False)]  # dominates all, but fails a guard
    summary = _summary(args, entries, "base")
    assert {e["reward_id"] for e in sw.archive_members(summary)} == {"base", "A", "B"}
    assert [e["reward_id"] for e in sw.repair_targets(summary)] == ["drift"]
    # a guard-failed reward dearer than the champion is no repair target
    assert sw.repair_targets(_summary(args, entries, "drift")) == []


def test_edit_base_rotates_modes_and_can_move_to_tradeoff(args):
    entries = [_entry("base", 10., 1e-4, 2e-4), _entry("A", 9.7, 1.01e-4, 1.96e-4),
               _entry("B", 9.9, 0.96e-4, 1.99e-4)]
    s = _summary(args, entries, "base")
    picks = [sw.select_edit_base(s, k, args) for k in (2, 3, 4, 5)]
    assert [(m, e["reward_id"]) for m, e, _ in picks] == [
        ("champion_improve", "base"), ("fuel_leader", "A"), ("champion_improve", "base"), ("champion_improve", "base")]
    assert "no fresh guard_repair target" in picks[2][2]
    s["archive"].append(_entry("R", 10.6, .3e-4, 2e-4, feasible=False))
    mode, base, _ = sw.select_edit_base(s, 4, args)
    assert (mode, base["reward_id"]) == ("guard_repair", "R")


def test_stale_bases_are_skipped_then_fallback(args):
    args.edit_base_max_stale = 2
    entries = [_entry("base", 10., 1e-4, 2e-4), _entry("A", 9.7, 1.01e-4, 1.96e-4, stale=2),
               _entry("B", 9.9, 0.96e-4, 1.99e-4)]
    mode, base, _ = sw.select_edit_base(_summary(args, entries, "base"), 3, args)
    assert (mode, base["reward_id"]) == ("fuel_leader", "B")
    for e in entries:
        e["stale"] = 2
    entries[2]["stale"] = 3
    mode, base, reason = sw.select_edit_base(_summary(args, entries, "base"), 2, args)
    assert mode == "fallback_least_stale" and base["reward_id"] == "A" and "stale" in reason


# ---- provenance in the proposer context --------------------------------------------------------

def test_context_separates_edit_base_champion_baseline_provenance(args, source, tmp_path):
    base_src = variant(source, "1.2")
    champion = trial(9.8, rid="champ", src=source)
    baseline = trial(10., rid="base", src=source)
    edit_base = {**_entry("tradeoffX", 9.5, 1.2e-4, 1.9e-4, parent="base"), "reward_source": base_src}
    summary = {"baseline": baseline, "iterations": []}
    captured = []

    class Client:
        provider, model = "anthropic", "test"
        def complete(self, **kw):
            captured.append(kw["prompt"])
            return f"```python\n{variant(source, '1.3')}\n```" if "Generate ONE" in kw["prompt"] else "hyp"

    result = sw.propose_reward(args=args, client=Client(), champion=champion, summary=summary,
                               iter_dir=tmp_path, edit_base=edit_base, edit_mode="fuel_leader")
    assert result == variant(source, "1.3")
    ctx = json.loads((tmp_path / "review.json").read_text())["context"]
    assert ctx["edit_base"]["reward_id"] == "tradeoffX" and ctx["edit_base"]["parent_id"] == "base"
    assert ctx["edit_base"]["reward_source"] == base_src
    assert ctx["champion"]["reward_id"] == "champ" and "reward_source" not in ctx["champion"]
    assert ctx["baseline"]["reward_id"] == "base"
    assert ctx["edit_base_vs_champion"]["reference_reward_id"] == "champ"
    assert ctx["edit_base_vs_champion"]["fuel_gkm"] == pytest.approx(9.5 - 9.8)
    assert ctx["evaluation_conditions"]["seed"] == 41 and ctx["evaluation_conditions"]["checkpoint_episode"] == 399
    assert ctx["edit_mode"] == "fuel_leader" and "champion" in ctx["edit_goal"]
    assert "judged ONLY against the champion" in captured[-1]


def test_edit_base_source_counts_as_trained_duplicate(args, source, tmp_path):
    args.multi_agent_review = False
    base_src = variant(source, "1.2")
    edit_base = {**_entry("X", 9.5, 1e-4, 2e-4), "reward_source": base_src}

    class Client:
        provider, model = "anthropic", "test"
        def complete(self, **kw):
            return f"```python\n{base_src}\n```"

    assert sw.propose_reward(args=args, client=Client(), champion=trial(src=source, rid="c"),
                             summary={"baseline": trial(src=source, rid="b"), "iterations": []},
                             iter_dir=tmp_path, edit_base=edit_base, edit_mode="fuel_leader") is None


# ---- end-to-end with a fake evaluator ----------------------------------------------------------

def _evaluator_factory(tmp_path, table, calls):
    class Evaluator:
        def __init__(self, *a):
            pass

        def __call__(self, reward, episodes, seed):
            calls.append((reward, episodes, seed))
            fuel, fc, batt, *soc = table(reward, seed)  # optional 4th value: SOC_final - SOC_initial
            rid = candidate_id(reward)
            result = {**trial(fuel, fc, batt, seed=seed, rid=rid, src=reward, **(drift(soc[0]) if soc else {})),
                      "chunk": {"model_dir": str(tmp_path / f"{rid[:12]}_{seed}"), "log_path": "train.log"}}
            model = Path(result["chunk"]["model_dir"])
            model.mkdir(exist_ok=True)
            (model / "actor_iter001_ep399.pkl").touch()
            return result
    return Evaluator


def test_full_run_moves_edit_base_to_tradeoff_and_confirms_on_unused_seeds(args, source, monkeypatch, tmp_path):
    args.ldri_iterations = 4
    p_trade, p_win, p_last = variant(source, "1.1"), variant(source, "1.3"), variant(source, "1.5")
    search = {source: (10., 1e-4, 2e-4), p_trade: (9.0, 1.1e-4, 1.9e-4),     # less fuel, costlier FC wear
              p_win: (9.5, 0.9e-4, 1.9e-4), p_last: (10.6, 0.5e-4, 1.8e-4)}  # win, then cheaper past fuel guard
    confirm = {101: (9.4, 0.9e-4, 1.9e-4), 102: (9.4, 1.1e-4, 1.9e-4), 103: (10.6, 0.9e-4, 1.9e-4)}

    def table(reward, seed):
        if seed == 41 or reward == source:
            return search[reward] if seed == 41 else (10., 1e-4, 2e-4)
        return confirm[seed]

    calls, seen = [], []

    def propose(**kw):
        seen.append({"mode": kw["edit_mode"], "base": kw["edit_base"]["reward_id"],
                     "champion": kw["champion"]["candidate_id"], "keys": set(kw["summary"])})
        return [p_trade, p_win, p_last][len(seen) - 1]

    monkeypatch.setattr(main, "_init_llm_client", lambda a: object())
    result = sw.run_sequential_workflow(args, tmp_path, False, api=main,
                                        trial_factory=_evaluator_factory(tmp_path, table, calls), proposal_fn=propose)
    rows = result["iterations"]
    assert [r["decision"] for r in rows] == ["baseline_trained", "retain_champion", "replace_champion", "retain_champion"]
    # iteration 3 = fuel_leader: edit base moved to the tradeoff candidate, adoption still vs champion (baseline)
    assert seen[1]["mode"] == "fuel_leader" and seen[1]["base"] == candidate_id(p_trade)
    assert seen[1]["champion"] == candidate_id(source)
    assert rows[1]["observed_relation"] == {"vs_champion": "objective_tradeoff", "vs_baseline": "objective_tradeoff"}
    assert rows[3]["observed_relation"]["vs_champion"] == "cost_tradeoff"
    assert rows[3]["verdict"]["checks"] == {"total_cost_strictly_improved": True, "charge_sustaining": True,
                                            "fuel_within_guard": False, "battery_within_guard": True}
    assert rows[2]["edit_base"]["parent_reward_id"] == candidate_id(p_trade)
    assert "parent:" in rows[2]["reward_diff"]
    assert all(r.get("reward_verdict") in (None, "inconclusive_single_run") for r in rows)
    # confirmation never reached the proposer
    assert all("confirmation" not in s["keys"] for s in seen)
    # deployment: L1 champion on seed 41
    final = result["final_selection"]
    assert final["candidate"]["candidate_id"] == candidate_id(p_win)
    assert final["improvement_confirmed"] and not final["rolled_back_to_baseline"]
    assert final["final_actor"].endswith(f"{candidate_id(p_win)[:12]}_41/actor_iter001_ep399.pkl")
    # the search alone never trains on other seeds; L4 is a separate explicit step
    assert all(c[2] == 41 for c in calls) and len(calls) == 4
    assert result["confirmation"]["status"] == "not_run" and "--run_confirmation" in result["confirmation"]["reason"]
    # L4 decided later: seeds registered right before confirmation
    args.run_confirmation, args.confirmation_seed_list = True, [101, 102, 103]
    result = sw.run_sequential_workflow(args, tmp_path, True, api=main,
                                        trial_factory=_evaluator_factory(tmp_path, table, calls), proposal_fn=propose)
    assert result["confirmation_registration"] == {"seeds": [101, 102, 103], "registered_at": "before_confirmation"}
    final = result["final_selection"]
    assert len(seen) == 3
    # L4: 6 fresh paired trials on the pre-specified seeds, after the search
    conf_calls = [c for c in calls if c[2] != 41]
    assert sorted((c[2], c[0] == source) for c in conf_calls) == sorted(
        [(s, b) for s in (101, 102, 103) for b in (True, False)])
    conf = result["confirmation"]
    assert conf["status"] == "complete"
    assert conf["counts"] == {"n_seeds": 3, "cost_improved": 2, "charge_sustaining": 3, "fuel_within_guard": 2,
                              "battery_within_guard": 3, "all_checks": 1}
    assert conf["reward_verdict"] == "observed_on_some_prespecified_seeds"
    assert final["reward_verdict"] == "observed_on_some_prespecified_seeds"
    assert (tmp_path / "confirmation.json").exists()
    overview = (tmp_path / "summary.md").read_text()
    assert "all_checks: 1/3" in overview and "Total cost" in overview
    # re-running confirmation reuses it; seeds cannot change; extending the search is refused
    n = len(calls)
    sw.run_sequential_workflow(args, tmp_path, True, api=main,
                               trial_factory=_evaluator_factory(tmp_path, table, calls), proposal_fn=propose)
    assert len(seen) == 3 and len(calls) == n
    args.confirmation_seed_list = [201, 202, 203]
    with pytest.raises(RuntimeError, match="already registered"):
        sw.run_sequential_workflow(args, tmp_path, True, api=main,
                                   trial_factory=_evaluator_factory(tmp_path, table, calls), proposal_fn=propose)
    args.confirmation_seed_list, args.run_confirmation = [], False
    args.resume_additional_iterations = 1
    with pytest.raises(RuntimeError, match="[Cc]onfirmation"):
        sw.run_sequential_workflow(args, tmp_path, True, api=main,
                                   trial_factory=_evaluator_factory(tmp_path, table, calls), proposal_fn=propose)
    assert len(calls) >= n


def test_no_champion_change_skips_confirmation_and_search_may_still_extend(args, source, monkeypatch, tmp_path):
    args.ldri_iterations = 2
    args.confirmation_seed_list = [101, 102, 103]
    worse = variant(source, "1.1")
    calls = []
    table = lambda reward, seed: (10., 1e-4, 2e-4) if reward == source else (10.5, 1e-4, 2e-4)
    monkeypatch.setattr(main, "_init_llm_client", lambda a: object())
    make = lambda: _evaluator_factory(tmp_path, table, calls)
    sw.run_sequential_workflow(args, tmp_path, False, api=main, trial_factory=make(), proposal_fn=lambda **kw: worse)
    args.run_confirmation = True
    result = sw.run_sequential_workflow(args, tmp_path, True, api=main, trial_factory=make(),
                                        proposal_fn=lambda **kw: worse)
    assert result["confirmation"] == {"status": "skipped", "reason": "no_champion_change", "iterations_at_skip": 2}
    assert result["confirmation_registration"]["registered_at"] == "run_start"
    assert all(c[2] == 41 for c in calls) and len(calls) == 2
    assert not result["final_selection"]["improvement_confirmed"]
    # a skip trained no confirmation seed: extension is allowed and the skip stays on record
    args.run_confirmation, args.resume_additional_iterations = False, 1
    result = sw.run_sequential_workflow(args, tmp_path, True, api=main, trial_factory=make(),
                                        proposal_fn=lambda **kw: variant(source, "1.2"))
    assert len(result["iterations"]) == 3 and result["confirmation"]["status"] == "not_run"
    assert result["confirmation_history"] == [{"status": "skipped", "reason": "no_champion_change",
                                               "iterations_at_skip": 2}]


def test_final_selection_rolls_back_when_champion_fails_vs_baseline(args, tmp_path):
    for name in ("b", "c"):
        (tmp_path / name).mkdir()
        (tmp_path / name / "actor_iter001_ep399.pkl").touch()
    baseline = {**trial(10., rid="b"), "chunk": {"model_dir": str(tmp_path / "b")}}
    champion = {**trial(9., 1.2e-4, rid="c"), "chunk": {"model_dir": str(tmp_path / "c")}}
    selection = sw.final_selection({"baseline": baseline, "champion": champion}, args, tmp_path)
    assert selection["rolled_back_to_baseline"] and not selection["improvement_confirmed"]
    assert selection["candidate"]["candidate_id"] == "b"
    assert selection["final_actor"].startswith(str(tmp_path / "b"))


# ---- configuration -----------------------------------------------------------------------------

def test_confirmation_seeds_must_be_unused_and_unique(args):
    args.confirmation_seed_list = [41, 42, 43]
    with pytest.raises(ValueError, match="search seed"):
        sw._configure(args)
    args.confirmation_seed_list = [42, 42, 43]
    with pytest.raises(ValueError, match="unique"):
        sw._configure(args)
    args.confirmation_seed_list, args.edit_base_max_stale = [42, 43, 44], 0
    with pytest.raises(ValueError, match="stale"):
        sw._configure(args)


def test_new_cli_options_parse_and_are_restored_on_resume(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["x", "--confirmation_seed_list", "101", "102", "103",
                                      "--edit_base_max_stale", "3"])
    parsed = get_ldri_args()
    assert parsed.confirmation_seed_list == [101, 102, 103] and parsed.edit_base_max_stale == 3
    assert {"confirmation_seed_list", "edit_base_max_stale"} <= set(main.RESUME_RESTORE_KEYS)
    assert "run_confirmation" not in main.RESUME_RESTORE_KEYS


def test_seeds_registered_at_start_are_restored_and_search_can_still_be_extended(args, source, monkeypatch, tmp_path):
    args.ldri_iterations = 2
    args.confirmation_seed_list = [101, 102, 103]
    calls, proposals = [], [variant(source, "1.1"), variant(source, "1.2")]
    table = lambda reward, seed: (10., 1e-4, 2e-4) if reward == source else (9., 9e-5, 1.9e-4)
    monkeypatch.setattr(main, "_init_llm_client", lambda a: object())
    make = lambda: _evaluator_factory(tmp_path, table, calls)
    propose = lambda **kw: proposals[len([c for c in calls if c[2] == 41]) - 1]
    sw.run_sequential_workflow(args, tmp_path, False, api=main, trial_factory=make(), proposal_fn=propose)
    assert all(c[2] == 41 for c in calls)
    # extension is allowed because L4 has not started
    args.resume_additional_iterations = 1
    table2 = lambda reward, seed: (10., 1e-4, 2e-4) if reward == source else (
        (9., 9e-5, 1.9e-4) if reward == proposals[0] else (8.9, 9e-5, 1.9e-4))
    result = sw.run_sequential_workflow(args, tmp_path, True, api=main,
                                        trial_factory=_evaluator_factory(tmp_path, table2, calls), proposal_fn=propose)
    assert len(result["iterations"]) == 3 and result["target_iterations"] == 3
    # confirmation without re-typing the seeds uses the ones registered at run start
    args.resume_additional_iterations, args.confirmation_seed_list, args.run_confirmation = 0, [], True
    result = sw.run_sequential_workflow(args, tmp_path, True, api=main,
                                        trial_factory=_evaluator_factory(tmp_path, table2, calls), proposal_fn=propose)
    assert result["confirmation"]["seeds"] == [101, 102, 103]
    assert sorted({c[2] for c in calls}) == [41, 101, 102, 103]


def test_interrupted_run_resumes_to_its_own_target_not_cli_default(args, source, monkeypatch, tmp_path):
    args.ldri_iterations, args.skip_llm = 4, True
    calls = []
    table = lambda reward, seed: (10., 1e-4, 2e-4)
    monkeypatch.setattr(main, "_init_llm_client", lambda a: object())
    result = sw.run_sequential_workflow(args, tmp_path, False, api=main,
                                        trial_factory=_evaluator_factory(tmp_path, table, calls),
                                        proposal_fn=lambda **kw: None)
    assert result["workflow_status"] == "paused_skip_llm"
    args.ldri_iterations, args.skip_llm = 3, False   # resume CLI does not restore ldri_iterations
    result = sw.run_sequential_workflow(args, tmp_path, True, api=main,
                                        trial_factory=_evaluator_factory(tmp_path, table, calls),
                                        proposal_fn=lambda **kw: None)
    assert len(result["iterations"]) == 4 and result["workflow_status"] == "completed"


def test_run_confirmation_needs_completed_search_and_seeds(args, source, monkeypatch, tmp_path):
    args.ldri_iterations, args.run_confirmation = 2, True
    calls, proposals = [], []
    table = lambda reward, seed: (10., 1e-4, 2e-4) if reward == source else (9., 9e-5, 1.9e-4)
    monkeypatch.setattr(main, "_init_llm_client", lambda a: object())
    make = lambda: _evaluator_factory(tmp_path, table, calls)
    p = variant(source, "1.1")

    def propose(**kw):
        proposals.append(kw["iter_dir"])
        return p
    with pytest.raises(RuntimeError, match="separate step"):
        sw.run_sequential_workflow(args, tmp_path, False, api=main, trial_factory=make(), proposal_fn=propose)
    assert not calls
    # an interrupted search: the confirmation command must not finish it (no LLM call, no training)
    args.run_confirmation, args.skip_llm = False, True
    sw.run_sequential_workflow(args, tmp_path, False, api=main, trial_factory=make(), proposal_fn=propose)
    n = len(calls)
    args.run_confirmation, args.skip_llm, args.confirmation_seed_list = True, False, [101, 102, 103]
    monkeypatch.setattr(main, "_init_llm_client", lambda a: pytest.fail("LLM initialised"))
    with pytest.raises(RuntimeError, match="completed search"):
        sw.run_sequential_workflow(args, tmp_path, True, api=main, trial_factory=make(), proposal_fn=propose)
    assert not proposals and len(calls) == n
    assert "confirmation_registration" not in json.loads((tmp_path / "run_summary.json").read_text())
    args.resume_additional_iterations = 1
    with pytest.raises(RuntimeError, match="cannot be combined"):
        sw.run_sequential_workflow(args, tmp_path, True, api=main, trial_factory=make(), proposal_fn=propose)
    # finish the search, then confirmation still needs seeds
    monkeypatch.setattr(main, "_init_llm_client", lambda a: object())
    args.run_confirmation, args.resume_additional_iterations, args.confirmation_seed_list = False, 0, []
    sw.run_sequential_workflow(args, tmp_path, True, api=main, trial_factory=make(), proposal_fn=propose)
    args.run_confirmation = True
    with pytest.raises(ValueError, match="confirmation_seed_list"):
        sw.run_sequential_workflow(args, tmp_path, True, api=main, trial_factory=make(), proposal_fn=propose)


# ---- whole-drive physical validity (review 2026-09-24) -----------------------------------------

def test_mid_drive_power_shortfall_invalidates_ep399(args):
    shortfall = {"trace_available": True, "unserved_kwh": .01, "unserved_peak_kw": 40.,
                 "steps_by_reason": {"unserved_power": 1}}
    bad = trial(9., 9e-5, 1.9e-4, power_violations=shortfall)
    assert not sw.policy_valid(bad, args)
    assert sw.validity_failures(bad, args)[0].startswith("requested_power_not_delivered: steps {'unserved_power': 1}")
    verdict = sw.compare_policies(bad, trial(), args)
    assert verdict["status"] == "fail" and verdict["invalid_reasons"]["candidate"]
    # missing whole-drive evidence fails closed
    assert not sw.policy_valid(trial(power_violations=None), args)
    # the reason reaches the proposer through the iteration brief
    brief = sw._brief(bad, args)
    assert brief["invalid_reasons"] and brief["power_violations"]["unserved_peak_kw"] == 40.
    assert "invalid_reasons" not in sw._brief(trial(), args)


def test_fuel_breakdown_reports_raw_h2_and_soc_correction(args):
    t = trial(paper_fuel={"equivalent_fuel_g": 500., "batt_eq_h2_g": -20., "drive_mileage_km": 50., "soc_f": .61},
              physical_evidence={"scalars": {"soc_final_minus_initial": .01}})
    f = sw.fuel_breakdown(t)
    assert f["raw_h2_gkm"] == pytest.approx(10.4) and f["soc_correction_gkm"] == pytest.approx(-.4)
    assert f["soc_final_minus_initial"] == .01
    assert sw.fuel_breakdown(trial()) == {}


def test_tail_diagnostics_counts_failed_rows(tmp_path):
    path = tmp_path / "ev.jsonl"
    rows = [{"episode": 360 + i, "fuel_gkm": 10. + .01 * i, "fc_loss": 1e-4, "batt_loss": 2e-4} for i in range(40)]
    rows[0] = {"episode": 360, "fuel_gkm": None, "fc_loss": None, "batt_loss": None, "incomplete_drive": True}
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    diag = sw.tail_diagnostics({"episodes": 400, "evaluation_evidence": str(path),
                                "metrics": {"tail_status": "contains_invalid_rows"}})
    assert diag["available"] and diag["failed_rows"] == 1 and diag["failed_episodes"] == [360]
    assert diag["coverage"] == 1.0 and diag["metrics"]["fuel_gkm"]["n"] == 39
    assert diag["trial_tail_status"] == "contains_invalid_rows"


def _row(episode, fuel=10.):
    return {"episode": episode, "fuel_gkm": fuel, "soc_in_bounds": 100., "soc_min": .5, "soc_max": .7,
            "fc_loss": 1e-4, "batt_loss": 2e-4}


def test_invalid_tail_row_does_not_invalidate_sequential_ep399(args):
    from validated_workflow import TrialEvaluator
    records = [_row(e) for e in range(360, 400)]
    records[0] = {**_row(360, float("nan")), "incomplete_drive": True}
    args.refinement_protocol = "sequential"
    metrics = TrialEvaluator(args, ".", None, {})._tail_metrics(records, 400)
    assert metrics["tail_status"] == "contains_invalid_rows" and metrics["tail_failed_episodes"] == [360]
    # the validated protocol keeps requiring a fully valid tail
    args.refinement_protocol = "validated"
    with pytest.raises(ValueError, match="Incomplete/non-finite"):
        TrialEvaluator(args, ".", None, {})._tail_metrics(records, 400)


def test_runner_judges_the_whole_drive_not_the_last_step(args, monkeypatch, tmp_path):
    """Mid-drive 80 kW request with a 40 kW battery and FC off, then feasible steps (review repro)."""
    import numpy as np
    import torch
    from env_ldri import make_env_ldri
    from runner_ldri import RunnerLDRI
    torch.set_num_threads(1)
    args.cuda, args.ramp_limit_kw, args.save_dir = False, 19., str(tmp_path / "models")
    env, args = make_env_ldri(args)
    args.episode_steps = 3
    env.speed_list, env.acc_list = np.array([20., 20., 20.]), np.zeros(3)
    requests = iter([80000., 10000., 10000.])
    env.agent.FCHEV.T_W_axle = lambda v, acc: (100., 3000., 30000.)
    env.agent.FCHEV.run_motor = lambda t, w, p: (t, w, .9, next(requests))
    runner = RunnerLDRI(args, env, tmp_path)
    runner.SAC_agent.select_action = lambda state, evaluate=False: np.array([0.])
    runner.validation_eval_hook = lambda *a: None
    m = runner._evaluate_policy_sac()
    assert m["physical_evidence"]["scalars"]["power_constraint_failed_steps"] == 1
    power = m["power_violations"]
    assert power["steps_by_reason"]["unserved_power"] == 1 and power["unserved_peak_kw"] > 0
    assert m["tracking_success"] is False and m["failure_reason"] == "unserved_power"
    assert np.isnan(m["paper_fuel"]["equivalent_g_per_km"])


def test_power_violation_summary_splits_fc_surplus_from_regen():
    from power_constraints import FAILURE_CODES, shortfall_steps, summarize_power_violations
    code = FAILURE_CODES["unaccepted_fc_power"]
    trace = {"power_failure_code": [0, code, code], "unserved_power_kw": [0., 0., 0.],
             "unaccepted_power_kw": [0., 5., 8.], "fc_applied_kw": [10., 3., 0.]}
    out = summarize_power_violations(trace, dt_s=3600.)
    assert out["steps_by_reason"]["unaccepted_fc_power"] == 2 and shortfall_steps(out) == {}
    assert out["unaccepted_fc_kwh"] == pytest.approx(3.) and out["unaccepted_regen_kwh"] == pytest.approx(10.)
    assert summarize_power_violations({}, dt_s=1.)["trace_available"] is False


def test_guards_are_fixed_by_baseline_not_by_the_champion(args):
    """A champion A that used less fuel and battery must not shrink the guard bands for B."""
    base, a = trial(10., 1e-4, 2e-4, rid="base"), trial(9.5, 1e-4, 1.5e-4, rid="A")
    b = trial(10.15, .6e-4, 1.9e-4, rid="B")   # more fuel and battery wear than A, much less FC wear
    verdict = sw.compare_policies(b, a, args, degradation_cap=base)
    assert verdict["status"] == "pass" and verdict["guard_reference"] == "baseline"
    assert verdict["fuel_delta_gkm"] > 0 and verdict["batt_loss_delta"] > 0 and verdict["total_cost_delta_usd"] < 0
    assert verdict["guards"]["fuel_gkm_max"] == pytest.approx(10.5)
    assert verdict["guards"]["batt_loss_max"] == pytest.approx(2.2e-4)
    assert verdict["cost_delta_usd"]["fc_usd"] < 0
    # past a baseline guard, or not cheaper than the champion: rejected
    assert sw.compare_policies(trial(10.6, .4e-4, 1e-4), a, args, degradation_cap=base)["status"] == "fail"
    assert sw.compare_policies(trial(9.4, .8e-4, 2.3e-4), a, args, degradation_cap=base)["status"] == "fail"
    assert sw.compare_policies(trial(9.95, 1e-4, 1.5e-4), a, args, degradation_cap=base)["status"] == "fail"


def test_cheaper_drifting_reward_is_repaired_not_adopted(args, source, monkeypatch, tmp_path):
    """FC idling into the battery: cheapest, but not charge sustaining -> kept as the guard_repair edit base."""
    args.ldri_iterations = 4
    p_drift, p_fuel, p_fixed = variant(source, "1.1"), variant(source, "1.2"), variant(source, "1.3")
    table = {source: (10., 1e-4, 2e-4, 0.), p_drift: (10.3, .2e-4, 2e-4, .11),
             p_fuel: (9.8, 1.05e-4, 2e-4, .01), p_fixed: (10.4, .3e-4, 2e-4, .03)}
    calls, seen, props = [], [], iter([p_drift, p_fuel, p_fixed])

    def propose(**kw):
        seen.append((kw["edit_mode"], kw["edit_base"]["reward_id"]))
        return next(props)

    monkeypatch.setattr(main, "_init_llm_client", lambda a: object())
    result = sw.run_sequential_workflow(args, tmp_path, False, api=main,
                                        trial_factory=_evaluator_factory(tmp_path, lambda r, s: table[r], calls),
                                        proposal_fn=propose)
    rows = result["iterations"]
    # p_fuel: less fuel, but dearer (21.14 > 20.68): a front member, not a champion
    assert [r["decision"] for r in rows] == ["baseline_trained", "retain_champion", "retain_champion",
                                             "replace_champion"]
    assert seen[1] == ("fuel_leader", candidate_id(source))  # p_drift is off the front (guard failed)
    assert rows[1]["verdict"]["checks"]["charge_sustaining"] is False
    assert rows[1]["verdict"]["checks"]["total_cost_strictly_improved"]
    assert seen[2] == ("guard_repair", candidate_id(p_drift))
    assert result["final_selection"]["candidate"]["candidate_id"] == candidate_id(p_fixed)


def test_run_selects_lowest_cost_guard_feasible_actor(args, source, monkeypatch, tmp_path):
    args.ldri_iterations = 3
    p_a, p_b = variant(source, "1.1"), variant(source, "1.2")
    # p_b burns more hydrogen than the champion p_a but wears the FC much less: adopted
    table = {source: (10., 1e-4, 2e-4), p_a: (9.9, .5e-4, 1e-4), p_b: (10.15, .3e-4, 1.6e-4)}
    calls, props = [], iter([p_a, p_b])
    monkeypatch.setattr(main, "_init_llm_client", lambda a: object())
    result = sw.run_sequential_workflow(args, tmp_path, False, api=main,
                                        trial_factory=_evaluator_factory(tmp_path, lambda r, s: table[r], calls),
                                        proposal_fn=lambda **kw: next(props))
    assert [r["decision"] for r in result["iterations"]][1:] == ["replace_champion", "replace_champion"]
    final = result["final_selection"]
    assert final["candidate"]["candidate_id"] == candidate_id(p_b) and final["improvement_confirmed"]
    assert final["candidate"]["operating_cost"]["total_usd"] == pytest.approx(0.7 * 10.15 + 121600 * .3e-4
                                                                              + 7581.6 * 1.6e-4)


def test_configure_rejects_negative_guard(args):
    args.cost_max_fuel_increase = -.01
    with pytest.raises(ValueError, match="cost_max_fuel_increase"):
        sw._configure(args)


def test_context_carries_cost_model_guards_and_price_alignment(args, source, tmp_path):
    args.multi_agent_review = False
    baseline = trial(10., rid="base", src=source)
    captured = []

    class Client:
        provider, model = "anthropic", "test"
        def complete(self, **kw):
            captured.append(kw["prompt"])
            return f"```python\n{variant(source, '1.3')}\n```"

    sw.propose_reward(args=args, client=Client(), champion=baseline, summary={"baseline": baseline, "iterations": []},
                      iter_dir=tmp_path)
    ctx = json.loads((tmp_path / "review.json").read_text())["context"]
    model = ctx["cost_model"]
    assert model["guards"]["fuel_gkm_max"] == pytest.approx(10.5)
    assert model["guards"]["batt_loss_max"] == pytest.approx(2.2e-4)
    assert model["guards"]["soc_drift_abs_max"] == .05
    assert ctx["champion"]["guard_checks"] == {"charge_sustaining": True, "fuel_within_guard": True,
                                               "battery_within_guard": True}
    align = model["reward_weight_alignment"]
    assert align["reward_fc_g_h2_per_unit_loss"] == pytest.approx(args.w_fc / args.w_h2)
    assert align["selection_fc_g_h2_per_unit_loss"] == pytest.approx(80 * 76 / .1 / .007)
    assert ctx["champion"]["operating_cost"]["fc_usd"] == pytest.approx(12.16)
    assert "total operating cost" in ctx["objective"] and "core levers" in ctx["objective"]
    assert "operating_cost.total_usd" in captured[-1]


def test_every_stage_is_told_to_protect_the_battery(args, source, tmp_path):
    """Cutting FC wear must not silently move it onto the battery: reviewers, orchestrator and proposer all see it."""
    args.multi_agent_review, args.proposal_attempts = True, 1
    baseline = trial(10., rid="base", src=source)
    prompts = []

    class Client:
        provider, model = "anthropic", "test"
        def complete(self, **kw):
            prompts.append(kw["prompt"])
            if "Mediate" in kw["prompt"]:
                return '```json\n{"term_ratio": {"h2_cost": 1.3}}\n```'
            return f"```python\n{variant(source, '1.3')}\n```" if "Generate ONE" in kw["prompt"] else "hyp"

    sw.propose_reward(args=args, client=Client(), champion=baseline, summary={"baseline": baseline, "iterations": []},
                      iter_dir=tmp_path)
    assert len(prompts) == 6 and all("BATTERY PROTECTION" in p and "CHARGE SUSTAINING" in p for p in prompts)
    assert "keeps battery degradation inside its guard" in prompts[4]
    assert "keeps the terminal SOC drift inside its guard" in prompts[4]
    assert "cost-fuel front" in prompts[4]
    assert "expected effect on terminal SOC drift" in prompts[5]
    assert "battery throughput and batt_loss" in prompts[5]
