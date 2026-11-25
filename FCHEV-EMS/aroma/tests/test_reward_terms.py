"""Reward term catalog: shapes on probes, structural change, charge-sustaining requirement and sizing."""
import json
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import main_ldri_refine as main
import reward_terms as rt
import sequential_workflow as sw
from arguments_ldri import get_ldri_args
from prompt_builder import extract_method_source
from reward_patcher import ensure_logging_contract
from test_sequential_v2 import trial

ANCHOR = "    soc_cost = w_soc * soc_err\n"
GUARD = .05


@pytest.fixture
def args(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["test"])
    args = get_ldri_args()
    args.seed, args.skip_patch = 41, True
    return args


@pytest.fixture
def base():
    return ensure_logging_contract(extract_method_source(main._resolve_input_path("agentEMS_val_base.py"),
                                                         "EMS", "get_reward"), sw.REQUIRED_KEYS)


def with_terms(base, *lines, anchor=True):
    """Insert term lines after the baseline anchor; each line may add to soc_cost or objective (via extra)."""
    head = ANCHOR + ("    self.info['term_soc_anchor'] = float(soc_cost)\n" if anchor else "")
    return base.replace(ANCHOR, head + "".join(f"    {line}\n" for line in lines))


SURPLUS = ["fc_to_batt = max(0.0, min(-self.P_batt, self.P_mot - self.P_batt)) / 1000.0",
           "surplus = 2.0 * max(0.0, soc - self.SOC_target + 0.05) / 0.05 * fc_to_batt",
           "self.info['term_fc_surplus_charge'] = float(surplus)",
           "soc_cost = soc_cost + surplus"]
BARRIER = ["barrier = 2000.0 * max(0.0, abs(soc - self.SOC_init) - 0.03) ** 2",
           "self.info['term_drift_barrier'] = float(barrier)", "soc_cost = soc_cost + barrier"]
PEAK = ["peak = 0.5 * max(0.0, soc - self.SOC_target + 0.05) / 0.05 * max(0.0, self.P_FCS - 20.0)",
        "self.info['term_fc_peak_shave'] = float(peak)", "soc_cost = soc_cost + peak"]


def ohmic_reward(base, c=1.0):
    src = with_terms(base, f"ohmic = {c} * self.P_batt_loss_kw", "self.info['term_batt_ohmic'] = float(ohmic)")
    return src.replace("objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost",
                       "objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost + ohmic")


def gap_reward(base, sign=1):
    eta = "self.P_FCS / (120.0 * max(self.h2_fcs, 1e-9))"
    gap = (f"gap = 3.0 * self.h2_fcs * max(0.0, 0.6 - {eta}) / 0.6" if sign > 0
           else f"gap = 3.0 * self.h2_fcs * max(0.0, {eta} - 0.6)")  # wrong direction: prices efficiency
    src = with_terms(base, "eta = 0.0", gap, "self.info['term_fc_efficiency_gap'] = float(gap)")
    return src.replace("objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost",
                       "objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost + gap")


def check(src, parent, args, **kw):
    return rt.verify_catalog_terms(src, parent, args, guard=GUARD, **kw)


# ---- shapes -------------------------------------------------------------------------------------

@pytest.mark.parametrize("lines", [SURPLUS, BARRIER, PEAK])
def test_correct_charge_sustaining_terms_pass(args, base, lines):
    out = check(with_terms(base, *lines), base, args)
    assert out["status"] == "pass", out.get("reason")
    assert len(out["structural_changes"]) == 1


@pytest.mark.parametrize("build", [ohmic_reward, gap_reward])
def test_correct_price_terms_pass(args, base, build):
    out = check(build(base), base, args)
    assert out["status"] == "pass", out.get("reason")


@pytest.mark.parametrize("lines,message", [
    # prices regeneration too: FC surplus must be P_mot - P_batt limited
    (["surplus = max(0.0, soc - 0.55) * max(0.0, -self.P_batt) / 1000.0",
      "self.info['term_fc_surplus_charge'] = float(surplus)", "soc_cost = soc_cost + surplus"], "pure regeneration"),
    # barrier starts past the guard
    (["barrier = 2000.0 * max(0.0, abs(soc - self.SOC_init) - 0.06) ** 2",
      "self.info['term_drift_barrier'] = float(barrier)", "soc_cost = soc_cost + barrier"], "positive at"),
    # peak shave also taxes the efficient band
    (["peak = 0.5 * max(0.0, soc - self.SOC_target + 0.05) / 0.05 * self.P_FCS",
      "self.info['term_fc_peak_shave'] = float(peak)", "soc_cost = soc_cost + peak"], "P_FCS <= 8 kW"),
])
def test_wrong_shapes_are_named(args, base, lines, message):
    out = check(with_terms(base, *lines), base, args)
    assert out["status"] == "fail" and message in out["reason"]


def test_efficiency_gap_must_price_inefficiency_not_efficiency(args, base):
    out = check(gap_reward(base, sign=-1), base, args)
    assert out["status"] == "fail" and "nonincreasing in FC efficiency" in out["reason"]


def test_unknown_term_and_unlogged_soc_component_fail(args, base):
    assert "unknown catalog term" in check(with_terms(base, "self.info['term_magic'] = 1.0"), base, args)["reason"]
    hidden = with_terms(base, "soc_cost = soc_cost + 5.0 * max(0.0, soc - 0.7)")
    assert "soc_cost must equal the sum" in check(hidden, base, args)["reason"]


# ---- structural change -----------------------------------------------------------------------------

def test_weight_only_changes_are_not_structural(args, base):
    logged = with_terms(base)
    assert "no structural change" in check(logged, base, args)["reason"]  # logging alone
    doubled = logged.replace("soc_cost = w_soc * soc_err", "soc_cost = 2.0 * w_soc * soc_err")
    assert "no structural change" in check(doubled, base, args)["reason"]  # pure multiplier
    h2 = logged.replace("h2_cost = self.w_h2", "h2_cost = 1.3 * self.w_h2")
    assert "no structural change" in check(h2, base, args)["reason"]


def test_reshaped_anchor_is_structural(args, base):
    asym = with_terms(base, "soc_cost = soc_cost + 4.0 * w_soc * max(0.0, soc - self.SOC_target) ** 2",
                      "self.info['term_soc_anchor'] = float(soc_cost)")
    out = check(asym, base, args)
    assert out["status"] == "pass" and out["structural_changes"] == ["soc_anchor"]


def test_child_of_a_catalog_reward_must_change_shape_again(args, base):
    parent = with_terms(base, *SURPLUS)
    stronger = parent.replace("surplus = 2.0 *", "surplus = 3.0 *")
    assert "no structural change" in check(stronger, parent, args)["reason"]
    gated = parent.replace("+ 0.05) / 0.05", "+ 0.02) / 0.02")  # new SOC gate = new shape
    assert check(gated, parent, args)["status"] == "pass"


def test_failed_cs_guard_requires_a_charge_sustaining_term(args, base):
    out = check(ohmic_reward(base), base, args, require_cs=True)
    assert out["status"] == "fail" and "charge-sustaining term" in out["reason"]
    assert check(with_terms(base, *SURPLUS), base, args, require_cs=True)["status"] == "pass"


def test_orchestrator_declared_terms_must_be_the_ones_changed(args, base):
    out = check(with_terms(base, *SURPLUS), base, args, declared=["drift_barrier"])
    assert out["status"] == "fail" and "catalog_terms" in out["reason"]
    assert check(with_terms(base, *SURPLUS), base, args, declared=["fc_surplus_charge"])["status"] == "pass"


def test_change_spec_parses_catalog_ids():
    text = '```json\n{"term_ratio": {"soc_cost": "changed"}, "catalog_terms": ["fc_surplus_charge"]}\n```'
    assert sw.parse_change_spec(text)["catalog_terms"] == ["fc_surplus_charge"]
    bad = '```json\n{"term_ratio": {"soc_cost": "changed"}, "catalog_terms": ["magic"]}\n```'
    assert sw.parse_change_spec(bad) is None


# ---- sizing on a drifting rollout --------------------------------------------------------------------

def drifting_rollout(path, n=400):
    """FC on at 6 kW against a 2 kW motor: 4 kW into the battery, SOC climbing 0.60 -> 0.72."""
    soc = np.linspace(0.6, 0.72, n)
    fc_soh = 1 - np.cumsum(np.full(n, 2e-8))
    fc_soh[0] -= 1.96e-5  # one start
    np.savez_compressed(path, SOC=soc, SOH=np.ones(n), FCS_SOH=fc_soh, dsoh=np.full(n, 1e-8),
                        fc_applied_kw=np.full(n, 6.0), battery_delivered_kw=np.full(n, -4.0), I=np.full(n, -16.0),
                        P_batt_loss_kw=np.full(n, .05), P_mot=np.full(n, 2.0), h2_fcs=np.full(n, .1),
                        h2_batt=np.zeros(n), h2_equal=np.full(n, .1), speed_m_s=np.full(n, 5.0),
                        acceleration_m_s2=np.zeros(n), travel=np.linspace(5, 2000, n))
    return path


def test_drift_bite_needs_more_than_one_start_and_less_than_the_drive(args, base, tmp_path):
    roll = drifting_rollout(tmp_path / "episode_00399.npz")
    weak = with_terms(base, *SURPLUS).replace("surplus = 2.0 *", "surplus = 1e-4 *")
    out = check(weak, base, args, require_cs=True, edit_rollout=roll)
    assert out["status"] == "fail" and "below 1 FC starts" in out["reason"] and "minimum, not a target" in out["reason"]
    huge = with_terms(base, *SURPLUS).replace("surplus = 2.0 *", "surplus = 1e5 *")
    out = check(huge, base, args, require_cs=True, edit_rollout=roll)
    assert out["status"] == "fail" and "above the whole drive's operating cost" in out["reason"]
    sized = with_terms(base, *SURPLUS).replace("surplus = 2.0 *", "surplus = 0.1 *")  # ~310 in [84, 1117]
    out = check(sized, base, args, require_cs=True, edit_rollout=roll)
    assert out["status"] == "pass", out.get("reason")
    low, high = out["drift_bite"]["required_range"]
    assert low == pytest.approx(args.w_fc * 1.96e-5, rel=.05) and low <= out["drift_bite"]["added_cs_cost_on_drifted_steps"] <= high


def test_drift_and_efficiency_facts(args, tmp_path):
    roll = drifting_rollout(tmp_path / "episode_00399.npz")
    facts = rt.drift_facts(roll, args, GUARD)
    assert "final drift +0.120" in facts and "FC->battery energy 0.444 kWh" in facts and "Sizing range" in facts
    eff = rt.efficiency_facts(roll)
    assert "eta = P_FCS / (120 * h2_fcs)" in eff and "eta 0.500" in eff  # 6 kW / (120 * 0.1 g/s)


# ---- the proposer is held to the catalog ------------------------------------------------------------

def test_proposer_gets_the_catalog_and_repairs_a_weight_only_proposal(args, base, tmp_path):
    args.multi_agent_review, args.proposal_attempts = False, 2
    baseline = trial(10., rid="base", src=base)
    good = with_terms(base, *SURPLUS)
    replies = iter([f"```python\n{base.replace('h2_cost = self.w_h2', 'h2_cost = 1.3 * self.w_h2')}\n```",
                    f"```python\n{good}\n```"])
    prompts = []

    class Client:
        provider, model = "anthropic", "test"
        def complete(self, **kw):
            prompts.append(kw["prompt"])
            return next(replies)

    result = sw.propose_reward(args=args, client=Client(), champion=baseline,
                               summary={"baseline": baseline, "iterations": []}, iter_dir=tmp_path)
    assert result == good
    assert "REWARD TERM CATALOG" in prompts[0] and "OPERATING DIRECTION" in prompts[0]
    assert "fc_efficiency_gap" in prompts[0] and "P_mot (W" in prompts[0]
    review = json.loads((tmp_path / "review.json").read_text())
    assert "catalog_contract" in review["attempts"][0]["error"] and "no structural change" in review["attempts"][0]["error"]
    assert review["verification"]["catalog"]["structural_changes"] == ["fc_surplus_charge"]


def test_drifting_edit_base_makes_the_cs_family_mandatory(args, base, tmp_path):
    args.multi_agent_review, args.proposal_attempts = False, 1
    baseline = trial(10., rid="base", src=base)
    edit_base = {**sw._entry(trial(9., rid="drift", src=base, physical_evidence={
        "scalars": {"soc_final_minus_initial": .11}}), 2, "base", sw.guard_limits(baseline, args))}
    assert edit_base["guard_checks"]["charge_sustaining"] is False
    prompts = []

    class Client:
        provider, model = "anthropic", "test"
        def complete(self, **kw):
            prompts.append(kw["prompt"])
            return f"```python\n{ohmic_reward(base)}\n```"

    assert sw.propose_reward(args=args, client=Client(), champion=baseline, edit_mode="guard_repair",
                             summary={"baseline": baseline, "iterations": []}, iter_dir=tmp_path,
                             edit_base=edit_base) is None
    assert "EDIT BASE FAILS THE CHARGE-SUSTAINING GUARD" in prompts[0]
    error = json.loads((tmp_path / "review.json").read_text())["attempts"][0]["error"]
    assert "must add or reshape a charge-sustaining term" in error


def test_drift_bite_floor_counts_the_baselines_fc_off_intervals(args, base, tmp_path):
    """A drifting edit base never switches off; the floor prices the starts a load-following baseline needs."""
    roll = drifting_rollout(tmp_path / "episode_00399.npz")
    reference = tmp_path / "baseline.npz"
    data = dict(np.load(roll))
    h2 = data["h2_fcs"].copy()
    h2[[0, 50, 51, 120, 200, 201, 202, 399]] = 0.0  # reset start, 3 in-drive off intervals, off at the end
    np.savez_compressed(reference, **{**data, "h2_fcs": h2})
    assert rt.avoidable_starts(reference) == 3 and rt.avoidable_starts(roll) == 0
    sized = with_terms(base, *SURPLUS).replace("surplus = 2.0 *", "surplus = 0.05 *")  # ~155: 1 start ok, 3 (251) not
    out = rt.verify_catalog_terms(sized, base, args, guard=GUARD, rollout=reference, require_cs=True,
                                  edit_rollout=roll)
    assert out["status"] == "fail" and "below 3 FC starts" in out["reason"]
    assert out["drift_bite"]["starts_priced"] == 3
    assert out["drift_bite"]["required_range"][0] == pytest.approx(3 * out["drift_bite"]["one_fc_start_price"])
    facts = rt.drift_facts(roll, args, GUARD, reference_rollout=reference)
    assert "MINIMUM 3 FC starts" in facts and "floor, not a target" in facts and "geometric mean" in facts


@pytest.mark.parametrize("spec, conflict", [
    ({"term_ratio": {"soc_cost": "changed"}, "extra_terms": "unchanged", "catalog_terms": ["fc_surplus_charge"]}, None),
    ({"term_ratio": {"soc_cost": 1.0}, "extra_terms": "added", "catalog_terms": ["fc_surplus_charge"]}, "soc_cost"),
    ({"term_ratio": {}, "extra_terms": "unchanged", "catalog_terms": ["drift_barrier"]}, "soc_cost"),
    ({"term_ratio": {"h2_cost": "changed"}, "extra_terms": "unchanged", "catalog_terms": ["fc_efficiency_gap"]},
     "extra_terms"),
    ({"term_ratio": {"soc_cost": "changed"}, "extra_terms": "added",
      "catalog_terms": ["fc_surplus_charge", "batt_ohmic"]}, None),
])
def test_spec_family_conflict(spec, conflict):
    """2026-10-17 seed61: CS ids with soc_cost 1.0 / a price id with extra unchanged sent 10 proposals in circles."""
    out = rt.spec_family_conflict(spec)
    assert (out is None) if conflict is None else (conflict in out)


def test_contradictory_spec_is_restated_by_the_orchestrator(args, base, tmp_path):
    args.multi_agent_review, args.proposal_attempts = True, 1
    baseline = trial(10., rid="base", src=base)
    bad = {"term_ratio": {"soc_cost": 1.0}, "extra_terms": "added", "catalog_terms": ["fc_surplus_charge"]}
    fixed = {"term_ratio": {"soc_cost": "changed"}, "extra_terms": "unchanged", "catalog_terms": ["fc_surplus_charge"]}
    prompts = []

    class Client:
        provider, model = "anthropic", "test"
        def complete(self, **kw):
            prompts.append(kw["prompt"])
            if "Mediate" in kw["prompt"]:
                return "Add fc_surplus_charge.\n```json\n" + json.dumps(bad) + "\n```"
            if "Return ONLY the CHANGE_SPEC" in kw["prompt"]:
                return "```json\n" + json.dumps(fixed) + "\n```"
            if "Generate ONE" in kw["prompt"]:
                return f"```python\n{with_terms(base, *SURPLUS)}\n```"
            return "hyp"

    sw.propose_reward(args=args, client=Client(), champion=baseline,
                      summary={"baseline": baseline, "iterations": []}, iter_dir=tmp_path)
    review = json.loads((tmp_path / "review.json").read_text())
    assert any("Return ONLY the CHANGE_SPEC" in p and "contradicts the catalog" in p for p in prompts)
    assert review["change_spec_conflict"]["spec"] == bad and review["change_spec"] == fixed
