"""The adoption cost must stay identical to the paper's economic translation (paper_figs_multi_seed.ipynb)."""
import ast
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import operating_cost as oc

NOTEBOOK = Path(__file__).resolve().parents[3] / "visualization" / "paper_figs_multi_seed.ipynb"
CONSTANTS = ("FC_EOL_LOSS", "FC_NET_KW", "FC_COST_PER_KW", "BATT_EOL_LOSS", "BATT_KWH", "BATT_COST_PER_KWH",
             "H2_PRICE")


def _notebook_code():
    cells = json.loads(NOTEBOOK.read_text(encoding="utf-8"))["cells"]
    return ["".join(c["source"]) for c in cells if c["cell_type"] == "code"]


def _notebook_constants():
    values = {}
    for code in _notebook_code():
        for node in ast.parse(code).body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                    and node.targets[0].id in CONSTANTS:
                values[node.targets[0].id] = ast.literal_eval(node.value)
    return values


def _notebook_economics(constants):
    for code in _notebook_code():
        for node in ast.parse(code).body:
            if isinstance(node, ast.FunctionDef) and node.name == "economics":
                namespace = {**constants, "FC_COST": constants["FC_NET_KW"] * constants["FC_COST_PER_KW"],
                             "BATT_COST": constants["BATT_KWH"] * constants["BATT_COST_PER_KWH"],
                             # life in hours/years only; they do not enter the cost
                             "HOURS_PER_KM": 1.0, "ANNUAL_KM": 1.0}
                exec(compile(ast.Module([node], []), str(NOTEBOOK), "exec"), namespace)
                return namespace["economics"]
    raise AssertionError("economics() not found in the notebook")


@pytest.mark.skipif(not NOTEBOOK.is_file(), reason="paper notebook not in this checkout")
def test_prices_match_the_notebook():
    constants = _notebook_constants()
    assert set(constants) == set(CONSTANTS)
    assert {k: getattr(oc, k) for k in CONSTANTS} == constants


@pytest.mark.skipif(not NOTEBOOK.is_file(), reason="paper notebook not in this checkout")
@pytest.mark.parametrize("fuel,fc,batt,km", [(10.37, 4.93e-4, 4.78e-4, 48.23), (1.2, 8e-6, 5e-4, 12.0)])
def test_cost_matches_the_notebook_economics(fuel, fc, batt, km):
    pd = pytest.importorskip("pandas")
    economics = _notebook_economics(_notebook_constants())
    row = economics(pd.DataFrame({"eq": [fuel], "fc_km": [fc / km], "bt_km": [batt / km]})).iloc[0]
    ours = oc.operating_cost(fuel, fc, batt, km)
    for theirs, mine in (("h2_cost", "h2_usd"), ("fc_cost", "fc_usd"), ("bt_cost", "batt_usd"),
                         ("deg_cost", "degradation_usd"), ("total_cost", "total_usd")):
        assert ours[mine] == pytest.approx(row[theirs], rel=1e-12)


@pytest.mark.parametrize("bad", [dict(fuel_gkm=None), dict(fc_loss=float("nan")), dict(distance_km=0.),
                                 dict(batt_loss=True)])
def test_missing_inputs_give_no_cost(bad):
    inputs = {"fuel_gkm": 10., "fc_loss": 1e-4, "batt_loss": 2e-4, "distance_km": 50., **bad}
    assert oc.operating_cost(**inputs) is None


def test_price_alignment_expresses_both_in_grams_h2():
    align = oc.price_alignment(10., 4.275e6, 1.116e6)
    assert align["reward_fc_g_h2_per_unit_loss"] == pytest.approx(4.275e5)
    assert align["selection_fc_g_h2_per_unit_loss"] == pytest.approx(6080 / .1 / .007)
    assert align["selection_over_reward_fc"] == pytest.approx(6080 / .1 / .007 / 4.275e5)
    assert oc.price_alignment(0., 1., 1.) == {"available": False}
