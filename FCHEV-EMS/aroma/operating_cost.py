"""Operating cost per 100 km, the selection objective of sequential AROMA.

Same prices and formula as the economic translation of visualization/paper_figs_multi_seed.ipynb
(configuration cell and `economics`): hydrogen bought, plus the share of the FC system and the
battery pack used up by the wear of the distance driven, wear extrapolated linearly to end of life.
tests/test_operating_cost.py executes the notebook's `economics` to keep the two identical.
"""
from __future__ import annotations

import math

FC_EOL_LOSS = 0.10         # FC end of life: 10% voltage loss (FCHEV_SOH.run_FC_SOH, DOE durability target)
FC_NET_KW = 80.0           # kW_net: FC_COST_PER_KW is per net system kW (plant P_fc_sys max 79.4 kW; stack 95 kW)
FC_COST_PER_KW = 76.0      # USD/kW_net, DOE Hydrogen Program Record 21001
BATT_EOL_LOSS = 0.20       # battery end of life: 20% capacity loss
BATT_KWH = 1.56            # pack energy of the plant (Battery.py: 6.5 Ah at 240 V)
BATT_COST_PER_KWH = 486.0  # USD/kWh, power-type HEV pack (Argonne BatPaC)
H2_PRICE = 7.0             # USD/kg, DOE light-duty dispensed cost target
FC_COST = FC_NET_KW * FC_COST_PER_KW
BATT_COST = BATT_KWH * BATT_COST_PER_KWH
UNIT = "USD per 100 km"

# Price of one unit (= 100%) of SOH loss and of one gram of H2, for comparing with reward weights.
USD_PER_FC_LOSS = FC_COST / FC_EOL_LOSS
USD_PER_BATT_LOSS = BATT_COST / BATT_EOL_LOSS
USD_PER_H2_G = H2_PRICE / 1000.0


def operating_cost(fuel_gkm, fc_loss, batt_loss, distance_km):
    """USD per 100 km of one drive: fuel_gkm is SOC-corrected equivalent H2, losses are 1 - SOH at the end.

    Returns None when an input is missing or not finite (fail closed: no cost, no comparison).
    """
    values = (fuel_gkm, fc_loss, batt_loss, distance_km)
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in values) \
            or distance_km <= 0:
        return None
    h2 = fuel_gkm * USD_PER_H2_G * 100.0
    fc = USD_PER_FC_LOSS * fc_loss / distance_km * 100.0
    batt = USD_PER_BATT_LOSS * batt_loss / distance_km * 100.0
    return {"h2_usd": h2, "fc_usd": fc, "batt_usd": batt, "degradation_usd": fc + batt,
            "total_usd": h2 + fc + batt, "unit": UNIT}


def price_model():
    """The fixed prices, as shown to the proposer."""
    return {"unit": UNIT,
            "formula": "total = H2 (fuel_gkm * H2_PRICE) + FC (FC system cost * fc_loss / FC_EOL_LOSS) "
                       "+ battery (pack cost * batt_loss / BATT_EOL_LOSS), all per 100 km of the drive",
            "h2_usd_per_kg": H2_PRICE, "fc_system_usd": FC_COST, "fc_eol_loss": FC_EOL_LOSS,
            "battery_pack_usd": BATT_COST, "battery_eol_loss": BATT_EOL_LOSS,
            "usd_per_unit_fc_loss": USD_PER_FC_LOSS, "usd_per_unit_batt_loss": USD_PER_BATT_LOSS,
            "usd_per_h2_g": USD_PER_H2_G}


def price_alignment(w_h2, w_fc, w_batt):
    """How the reward's weights rank one unit of FC/battery SOH loss against hydrogen, versus the selection.

    Both expressed as grams of H2 per unit (= 100%) SOH loss, so reward units cancel out.
    """
    if not all(isinstance(w, (int, float)) and w > 0 for w in (w_h2, w_fc, w_batt)):
        return {"available": False}
    sel_fc, sel_batt = USD_PER_FC_LOSS / USD_PER_H2_G, USD_PER_BATT_LOSS / USD_PER_H2_G
    rew_fc, rew_batt = w_fc / w_h2, w_batt / w_h2
    return {"available": True, "basis": "settings w_h2/w_fc/w_batt; grams H2 per unit (100%) SOH loss",
            "selection_fc_g_h2_per_unit_loss": sel_fc, "reward_fc_g_h2_per_unit_loss": rew_fc,
            "selection_over_reward_fc": sel_fc / rew_fc,
            "selection_batt_g_h2_per_unit_loss": sel_batt, "reward_batt_g_h2_per_unit_loss": rew_batt,
            "selection_over_reward_batt": sel_batt / rew_batt}
