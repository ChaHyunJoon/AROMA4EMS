"""Equivalent fuel matching the evaluation notebooks' paper_rows calculation.

Reference: visualization/eval_viz_{LA92_US06,WVUCITY_UDDS,WVUSUB_HWFET}.ipynb.
The denominator is actual distance. The printed electric-distance assumption
does not alter mileage in those notebooks.
"""
import numpy as np

PAPER_BATTERY_CAPACITY_KWH = 1.56
PAPER_H2_LHV_KWH_PER_KG = 33.33
PAPER_FC_EFFICIENCY = 0.50
PAPER_ELECTRIC_MOVING_DISTANCE_KM_PER_KWH = 5.0
FC_EFF_MODE = "energy"
PAPER_FUEL_BASIS = "deterministic_paper_energy_tail10_v2"


def _to_1d_float(values):
    if values is None:
        return np.zeros(0, dtype=np.float64)
    arr = np.asarray(values, dtype=np.float64).reshape(-1)
    return np.where(np.isfinite(arr), arr, 0.0)


def fc_operating_efficiency(data, mode=FC_EFF_MODE, default=PAPER_FC_EFFICIENCY):
    """Net-power weighted harmonic efficiency, with notebook fallback semantics."""
    power = data.get("P_fce")
    if power is None:
        power = data.get("P_fc")
    eff = data.get("fce_eff")
    if power is None or eff is None:
        return float(default)
    power = np.asarray(power, dtype=np.float64).reshape(-1)
    eff = np.asarray(eff, dtype=np.float64).reshape(-1)
    n = min(power.size, eff.size)
    power, eff = power[:n], eff[:n]
    valid = np.isfinite(power) & np.isfinite(eff) & (power > 0.0)
    power, eff = power[valid], eff[valid]
    if not power.size:
        return float(default)
    if mode == "energy":
        positive = eff > 0.0
        value = (np.sum(power[positive]) / np.sum(power[positive] / eff[positive])
                 if np.any(positive) else np.nan)
    elif mode == "power_weighted":
        value = np.sum(power * eff) / np.sum(power)
    elif mode == "time":
        value = np.mean(eff)
    else:
        value = np.nan
    return float(value) if np.isfinite(value) and value > 0 else float(default)


def compute_paper_style_fuel_economy(
    travel_m_series, h2_fcs_gps, soc_series, dt_s=1.0,
    battery_capacity_kwh=PAPER_BATTERY_CAPACITY_KWH,
    h2_lhv_kwh_per_kg=PAPER_H2_LHV_KWH_PER_KG,
    fc_efficiency=PAPER_FC_EFFICIENCY,
    electric_distance_km_per_kwh=PAPER_ELECTRIC_MOVING_DISTANCE_KM_PER_KWH,
):
    travel = _to_1d_float(travel_m_series)
    h2 = _to_1d_float(h2_fcs_gps)
    result = dict.fromkeys(("equivalent_g_per_km", "equivalent_fuel_g", "equivalent_mileage_km",
                           "drive_mileage_km", "soc_i", "soc_f", "batt_eq_h2_g",
                           "mileage_correction_km"), np.nan)
    result["fc_efficiency"] = fc_efficiency
    if not travel.size or not h2.size:
        return result
    distance = float(travel[-1]) / 1000.0
    fuel = float(np.sum(h2) * float(dt_s))
    soc = _to_1d_float(soc_series)
    soc_i, soc_f = (float(soc[0]), float(soc[-1])) if soc.size else (np.nan, np.nan)
    battery_h2 = np.nan
    if (np.isfinite(soc_i) and np.isfinite(soc_f)
            and np.isfinite(battery_capacity_kwh) and battery_capacity_kwh > 0
            and np.isfinite(h2_lhv_kwh_per_kg) and h2_lhv_kwh_per_kg > 0
            and np.isfinite(fc_efficiency) and fc_efficiency > 0):
        battery_h2 = ((soc_i - soc_f) * battery_capacity_kwh
                      / (h2_lhv_kwh_per_kg * fc_efficiency) * 1000.0)
    equivalent = fuel + battery_h2 if np.isfinite(battery_h2) else np.nan
    result.update(
        equivalent_g_per_km=(equivalent / distance
                             if np.isfinite(equivalent) and distance > 1e-12 else np.nan),
        equivalent_fuel_g=equivalent, equivalent_mileage_km=distance,
        drive_mileage_km=distance, soc_i=soc_i, soc_f=soc_f,
        batt_eq_h2_g=battery_h2, mileage_correction_km=0.0)
    return result


def paper_fuel_economy(data, dt_s=1.0):
    """Compute the notebook row directly from a rollout or loaded MAT dictionary."""
    row = compute_paper_style_fuel_economy(
        data.get("travel"), data.get("h2_fcs"), data.get("SOC"), dt_s=dt_s,
        fc_efficiency=fc_operating_efficiency(data))
    row.update(fuel_metric_basis=PAPER_FUEL_BASIS, fc_eff_mode=FC_EFF_MODE,
               battery_capacity_kwh=PAPER_BATTERY_CAPACITY_KWH,
               h2_lhv_kwh_per_kg=PAPER_H2_LHV_KWH_PER_KG,
               electric_distance_km_per_kwh=PAPER_ELECTRIC_MOVING_DISTANCE_KM_PER_KWH,
               dt_s=float(dt_s))
    return row
