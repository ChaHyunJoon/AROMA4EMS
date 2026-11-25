# Iteration 5

Decision: **retain_champion**

```json
{
  "iteration": 5,
  "control": {
    "candidate_id": "9a1a00b2da2f4836b7563a0ad13593c767d8ae9618ae004902187c2068ca2d83",
    "seed": 1,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.592957563806065,
      "fc_loss": 0.00014194499997055576,
      "batt_loss": 0.0004656390750389372,
      "soc_in_bounds": 100.0,
      "soc_min": 0.564684939325233,
      "soc_max": 0.6680178496457082
    },
    "operating_cost": {
      "h2_usd": 7.415070294664246,
      "fc_usd": 17.89460408478419,
      "batt_usd": 3.6599799446490873,
      "degradation_usd": 21.55458402943328,
      "total_usd": 28.969654324097526,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.550211884342488,
      "soc_correction_gkm": 0.042745679463576804,
      "soc_final": 0.5776486440139301,
      "soc_final_minus_initial": -0.022351355986069854,
      "unaccepted_fc_kwh": 0.0,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.522227783061224,
      "fc_loss": 0.0001434360749754615,
      "batt_loss": 0.00046901508513810255
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.5776486440139301,
      "soc_final_minus_initial": -0.022351355986069854,
      "soc_swing": 0.1033329103204752,
      "soc_mean": 0.608591370877483,
      "fc_power_kw_mean": 9.855238376195702,
      "fc_abs_ramp_kw_s_mean": 1.2217917655698105,
      "fc_on_pct": 74.16448706771287,
      "fc_start_stop_count": 7,
      "fc_start_stop_soh_loss": 0.0001372,
      "fc_low_power_count": 678,
      "fc_low_power_soh_loss": 2.3729999999999996e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 4,
      "fc_load_change_soh_loss": 2.3720000000000003e-06,
      "battery_throughput_kwh": 4.26299916139816,
      "battery_ohmic_loss_kw_integral_kwh": 0.2055063882301972,
      "fc_low_output_pct": 39.37808776518454,
      "fc_regeneration_energy_kwh": 0.6178704224733306,
      "fc_energy_efficiency": 0.507457121033949
    },
    "regimes": {
      "available": true,
      "groups": {
        "stopped": {
          "steps": 408,
          "available": true,
          "duration_s": 408.0,
          "hydrogen_g": 6.098756949610739,
          "fc_energy_kwh": 0.06888597520778209,
          "fc_energy_efficiency": 0.3388864242177843,
          "fc_low_output_pct": 20.588235294117645,
          "battery_throughput_kwh": 0.050882331185136555,
          "battery_ohmic_loss_kwh": 0.0005593326544359664,
          "soc_mean": 0.6370984588706933,
          "soc_delta": 0.03092862274807029
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 84.11022668311922,
          "fc_energy_kwh": 1.377717709890936,
          "fc_energy_efficiency": 0.4914463614388332,
          "fc_low_output_pct": 45.637119113573405,
          "battery_throughput_kwh": 0.8092733187436295,
          "battery_ohmic_loss_kwh": 0.017677134552075893,
          "soc_mean": 0.6182397956574345,
          "soc_delta": -0.12922202103733726
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 207.16541990768883,
          "fc_energy_kwh": 3.5361014721674118,
          "fc_energy_efficiency": 0.512120476369318,
          "fc_low_output_pct": 25.213270142180093,
          "battery_throughput_kwh": 1.8244561330050382,
          "battery_ohmic_loss_kwh": 0.09733479042926174,
          "soc_mean": 0.6077439865919851,
          "soc_delta": -1.1179537579548193
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 44.13869509781211,
          "fc_energy_kwh": 0.6178704224733306,
          "fc_energy_efficiency": 0.41999353242696796,
          "fc_low_output_pct": 76.36632200886262,
          "battery_throughput_kwh": 1.6286160509635785,
          "battery_ohmic_loss_kwh": 0.09510421128027824,
          "soc_mean": 0.6170530965803704,
          "soc_delta": 0.9527934349185635
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 295.21986880536116,
          "fc_energy_kwh": 5.094065697497729,
          "fc_energy_efficiency": 0.517706532656048,
          "fc_low_output_pct": 14.425162689804772,
          "battery_throughput_kwh": 0.7487375747775823,
          "battery_ohmic_loss_kwh": 0.019361372103325346,
          "soc_mean": 0.5879087000228408,
          "soc_delta": 0.059503462502564
        }
      },
      "missing_sensors": [],
      "basis": "overlapping_input_regimes_diagnostic_only",
      "thresholds": {
        "stopped_m_s": 0.1,
        "low_load_kw": 10.0,
        "acceleration_m_s2": 0.1,
        "high_speed_m_s": 22.2222222222
      },
      "note": "Groups overlap; raw H2 alone is not charge-sustaining fuel economy."
    },
    "development": null
  },
  "decision": "retain_champion",
  "experiment_plan": {
    "name": "archive",
    "iteration": 5
  },
  "edit_base": {
    "mode": "champion_improve",
    "parent_reward_id": "9a1a00b2da2f4836b7563a0ad13593c767d8ae9618ae004902187c2068ca2d83",
    "selection_reason": "champion_improve: rank 1 of 1"
  },
  "candidate": {
    "candidate_id": "187b8f1ea4ae4ba8b0855af8f8741a1c4860a183c03e810145cc6243e5570d4e",
    "seed": 1,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.556665388962326,
      "fc_loss": 0.0002264129999761666,
      "batt_loss": 0.00042894649844260613,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5633687875388056,
      "soc_max": 0.6413181083241309
    },
    "operating_cost": {
      "h2_usd": 7.389665772273628,
      "fc_usd": 28.543245588518,
      "batt_usd": 3.3715718155657575,
      "degradation_usd": 31.91481740408376,
      "total_usd": 39.30448317635739,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.621449345836748,
      "soc_correction_gkm": -0.06478395687442112,
      "soc_final": 0.6348431033679202,
      "soc_final_minus_initial": 0.03484310336792018,
      "unaccepted_fc_kwh": 0.0027975643530234783,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.524402182881689,
      "fc_loss": 0.000262286412479712,
      "batt_loss": 0.0004383661714070702
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.6348431033679202,
      "soc_final_minus_initial": 0.03484310336792018,
      "soc_swing": 0.07794932078532535,
      "soc_mean": 0.6006792156275059,
      "fc_power_kw_mean": 9.983984565805397,
      "fc_abs_ramp_kw_s_mean": 1.554989291953871,
      "fc_on_pct": 77.85527462946817,
      "fc_start_stop_count": 11,
      "fc_start_stop_soh_loss": 0.00021560000000000004,
      "fc_low_power_count": 548,
      "fc_low_power_soh_loss": 1.918e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 15,
      "fc_load_change_soh_loss": 8.895e-06,
      "battery_throughput_kwh": 3.8463822045383096,
      "battery_ohmic_loss_kw_integral_kwh": 0.1974577113604633,
      "fc_low_output_pct": 45.306596919500144,
      "fc_regeneration_energy_kwh": 0.6941485052086683,
      "fc_energy_efficiency": 0.5109235176735343
    },
    "regimes": {
      "available": true,
      "groups": {
        "stopped": {
          "steps": 408,
          "available": true,
          "duration_s": 408.0,
          "hydrogen_g": 1.4590768434829395,
          "fc_energy_kwh": 0.026784729811116216,
          "fc_energy_efficiency": 0.5507744572525928,
          "fc_low_output_pct": 2.696078431372549,
          "battery_throughput_kwh": 0.022453951630198487,
          "battery_ohmic_loss_kwh": 0.000663890578990924,
          "soc_mean": 0.6337454088656523,
          "soc_delta": 0.013309114058396299
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 85.03333668163921,
          "fc_energy_kwh": 1.3939261099331761,
          "fc_energy_efficiency": 0.49183022949133703,
          "fc_low_output_pct": 55.33240997229917,
          "battery_throughput_kwh": 0.6455956065247891,
          "battery_ohmic_loss_kwh": 0.012019030595299489,
          "soc_mean": 0.6132401531298927,
          "soc_delta": -0.12459486957450405
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 224.32344470408756,
          "fc_energy_kwh": 3.8263903183473045,
          "fc_energy_efficiency": 0.5117752628168079,
          "fc_low_output_pct": 39.905213270142184,
          "battery_throughput_kwh": 1.5657642426934657,
          "battery_ohmic_loss_kwh": 0.08782127020191614,
          "soc_mean": 0.601204243112973,
          "soc_delta": -0.962422536504528
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 46.20217623173089,
          "fc_energy_kwh": 0.6941485052086683,
          "fc_energy_efficiency": 0.450769628373863,
          "fc_low_output_pct": 78.13884785819793,
          "battery_throughput_kwh": 1.6920039204829436,
          "battery_ohmic_loss_kwh": 0.10177376475845587,
          "soc_mean": 0.6117612918549937,
          "soc_delta": 0.9893130521181129
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 288.4166449749638,
          "fc_energy_kwh": 4.994829722730937,
          "fc_energy_efficiency": 0.5195951075663604,
          "fc_low_output_pct": 13.99132321041215,
          "battery_throughput_kwh": 0.5101716309362413,
          "battery_ohmic_loss_kwh": 0.010924125321984274,
          "soc_mean": 0.5722962278730762,
          "soc_delta": 0.013023151303743097
        }
      },
      "missing_sensors": [],
      "basis": "overlapping_input_regimes_diagnostic_only",
      "thresholds": {
        "stopped_m_s": 0.1,
        "low_load_kw": 10.0,
        "acceleration_m_s2": 0.1,
        "high_speed_m_s": 22.2222222222
      },
      "note": "Groups overlap; raw H2 alone is not charge-sustaining fuel economy."
    },
    "development": null
  },
  "verdict": {
    "status": "fail",
    "checks": {
      "total_cost_strictly_improved": false,
      "charge_sustaining": true,
      "fuel_within_guard": true,
      "battery_within_guard": true
    },
    "checkpoint_episode": 399,
    "cost_unit": "USD per 100 km",
    "total_cost_delta_usd": 10.33482885225986,
    "cost_delta_usd": {
      "h2_usd": -0.025404522390617856,
      "fc_usd": 10.64864150373381,
      "batt_usd": -0.2884081290833298
    },
    "soc_drift": 0.03484310336792018,
    "fuel_delta_gkm": -0.03629217484373903,
    "fc_loss_delta": 8.446800000561083e-05,
    "batt_loss_delta": -3.669257659633107e-05,
    "guards": {
      "reference": "baseline",
      "max_fuel_increase_fraction": 0.05,
      "max_batt_increase_fraction": 0.1,
      "fuel_gkm_max": 11.18909967951321,
      "batt_loss_max": 0.0005969470490372886,
      "soc_drift_abs_max": 0.05
    },
    "guard_reference": "baseline",
    "comparison_basis": "matched_fresh_training",
    "total_cost_delta_usd_vs_baseline": -1.108054336349774,
    "fuel_delta_gkm_vs_baseline": -0.09962002009787341,
    "fc_loss_delta_vs_baseline": -1.145166667271269e-06,
    "batt_loss_delta_vs_baseline": -0.00011373263704583803
  },
  "observed_relation": {
    "vs_champion": "objective_tradeoff",
    "vs_baseline": "strict_pareto"
  },
  "reward_verdict": "inconclusive_single_run",
  "tail": {
    "basis": "single_run_tail_diagnostic_not_a_gate",
    "window": [
      360,
      399
    ],
    "available": true,
    "trial_tail_status": "all_rows_valid",
    "rows": 40,
    "coverage": 1.0,
    "failed_rows": 0,
    "failed_episodes": [],
    "metrics": {
      "fuel_gkm": {
        "n": 40,
        "mean": 10.524402182881689,
        "std": 0.029267578169278007,
        "slope_per_10_episodes": 0.012903932276825498,
        "ep399_better_than_fraction": 0.125
      },
      "fc_loss": {
        "n": 40,
        "mean": 0.000262286412479712,
        "std": 2.2624385955187313e-05,
        "slope_per_10_episodes": -3.097037056084456e-06,
        "ep399_better_than_fraction": 0.875
      },
      "batt_loss": {
        "n": 40,
        "mean": 0.0004383661714070702,
        "std": 7.6158367165473635e-06,
        "slope_per_10_episodes": -4.86060891654577e-06,
        "ep399_better_than_fraction": 0.9
      }
    },
    "lucky_checkpoint": false
  },
  "reward_diff": "--- parent:9a1a00b2da2f\n+++ candidate\n@@ -11,7 +11,16 @@\n     term_soc_anchor = w_soc_eff * soc_err\n     self.info[\"term_soc_anchor\"] = float(term_soc_anchor)\n \n-    soc_cost = float(term_soc_anchor)\n+    # Catalog term: drift_barrier (ADDED per orchestrator; symmetric quadratic barrier around SOC_init)\n+    soc_init = float(self.SOC_init)\n+    d0 = 0.03  # deadband (< soc_drift_abs_max=0.05), keeps small drift cheap but prices guard-violating drift\n+    p = 2.0\n+    drift_excess = float(np.maximum(0.0, np.abs(soc - soc_init) - d0))\n+    c_drift = 20000.0  # sized to be several units/step when |drift| approaches the guard\n+    term_drift_barrier = c_drift * (drift_excess ** p)\n+    self.info[\"term_drift_barrier\"] = float(term_drift_barrier)\n+\n+    soc_cost = float(term_soc_anchor + term_drift_barrier)\n \n     # ---------- Core operating-cost proxy terms (existing) ----------\n     h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal\n@@ -19,21 +28,20 @@\n     fcs_soh_cost = float(self.w_fc) * float(self.dSOH_FCS)\n     batt_soh_cost = float(self.w_batt) * float(self.dSOH_batt)\n \n-    # ---------- Extra catalog price terms (ADDED): fc_efficiency_gap, batt_ohmic ----------\n+    # ---------- Extra catalog price terms (existing in edit_base): fc_efficiency_gap, batt_ohmic ----------\n     # Catalog term: fc_efficiency_gap\n-    # eta = P_FCS / (120 * h2_fcs) for 1-s step, with 120 kJ/g LHV\n     P_fcs_kw = float(self.P_FCS)\n     h2_fcs_g = float(h2_fcs)\n     eta_ref = 0.602  # peak measured band (10-15 kW) from EFFICIENCY FACTS\n     eta = float(P_fcs_kw / (120.0 * h2_fcs_g)) if h2_fcs_g > 0.0 else 0.0\n     eta_gap_frac = float(np.maximum(0.0, eta_ref - eta) / eta_ref) if h2_fcs_g > 0.0 else 0.0\n-    c_eff_gap = 5.0  # reward units per gram-scaled gap; moderate to satisfy deviation check\n+    c_eff_gap = 5.0\n     term_fc_efficiency_gap = c_eff_gap * h2_fcs_g * eta_gap_frac\n     self.info[\"term_fc_efficiency_gap\"] = float(term_fc_efficiency_gap)\n \n     # Catalog term: batt_ohmic\n     P_batt_loss_kw = float(self.P_batt_loss_kw)\n-    c_batt_ohmic = 2.0  # reward units per kW-step; sized to be comparable to baseline mean soc_cost scale\n+    c_batt_ohmic = 2.0\n     term_batt_ohmic = c_batt_ohmic * float(np.maximum(0.0, P_batt_loss_kw))\n     self.info[\"term_batt_ohmic\"] = float(term_batt_ohmic)\n \n"
}
```

[Training log](results/aroma_runs/seed1_obscur_20261018_061824_704722118/search/20261018_061824_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed1_obscur_seq_v3_catalog_iter6/trials/61e368bf76f11a40e702c34d/iter_001/train_log.log)
[Evaluation records](results/aroma_runs/seed1_obscur_20261018_061824_704722118/search/20261018_061824_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed1_obscur_seq_v3_catalog_iter6/trials/61e368bf76f11a40e702c34d/deterministic_evaluations.jsonl)
