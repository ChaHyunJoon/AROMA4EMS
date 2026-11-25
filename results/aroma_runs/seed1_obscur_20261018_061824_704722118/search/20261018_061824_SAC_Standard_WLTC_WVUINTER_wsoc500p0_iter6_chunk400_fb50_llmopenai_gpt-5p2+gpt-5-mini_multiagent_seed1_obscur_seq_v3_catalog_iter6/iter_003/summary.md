# Iteration 3

Decision: **replace_champion**

```json
{
  "iteration": 3,
  "control": {
    "candidate_id": "17afbf80420cb9f947efdaac72a30bf9687444a44fa8df43fcfaa7ace533d083",
    "seed": 1,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.6562854090602,
      "fc_loss": 0.00022755816664343786,
      "batt_loss": 0.0005426791354884442,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5436408567243644,
      "soc_max": 0.6739097201102481
    },
    "operating_cost": {
      "h2_usd": 7.45939978634214,
      "fc_usd": 28.687613506557817,
      "batt_usd": 4.2655242198072045,
      "degradation_usd": 32.95313772636502,
      "total_usd": 40.41253751270716,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.673761753276468,
      "soc_correction_gkm": -0.01747634421626657,
      "soc_final": 0.6092110798875628,
      "soc_final_minus_initial": 0.009211079887562867,
      "unaccepted_fc_kwh": 0.0013104144617879854,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.653879374321736,
      "fc_loss": 0.00024918413539261054,
      "batt_loss": 0.000545478315356987
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.6092110798875628,
      "soc_final_minus_initial": 0.009211079887562867,
      "soc_swing": 0.13026886338588373,
      "soc_mean": 0.6144319802401514,
      "fc_power_kw_mean": 10.031732207036825,
      "fc_abs_ramp_kw_s_mean": 1.6468069579348108,
      "fc_on_pct": 78.17494914269108,
      "fc_start_stop_count": 11,
      "fc_start_stop_soh_loss": 0.00021559999999999998,
      "fc_low_power_count": 534,
      "fc_low_power_soh_loss": 1.8689999999999998e-06,
      "fc_high_power_soh_loss": 8.166666666666667e-09,
      "fc_load_change_count": 17,
      "fc_load_change_soh_loss": 1.0081e-05,
      "battery_throughput_kwh": 4.966083766525999,
      "battery_ohmic_loss_kw_integral_kwh": 0.2798767034022185,
      "fc_low_output_pct": 42.28421970357454,
      "fc_regeneration_energy_kwh": 0.8388188480629577,
      "fc_energy_efficiency": 0.5115023807111742
    },
    "regimes": {
      "available": true,
      "groups": {
        "stopped": {
          "steps": 408,
          "available": true,
          "duration_s": 408.0,
          "hydrogen_g": 0.0,
          "fc_energy_kwh": 0.0,
          "fc_energy_efficiency": null,
          "fc_low_output_pct": 0.0,
          "battery_throughput_kwh": 0.0001999727845381161,
          "battery_ohmic_loss_kwh": 3.950502492830206e-08,
          "soc_mean": 0.6439403423091218,
          "soc_delta": -0.00012321992355279754
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 100.96585803455488,
          "fc_energy_kwh": 1.701678573259136,
          "fc_energy_efficiency": 0.5056705676346067,
          "fc_low_output_pct": 39.958448753462605,
          "battery_throughput_kwh": 0.8475848353926325,
          "battery_ohmic_loss_kwh": 0.01989636786945871,
          "soc_mean": 0.628104997332726,
          "soc_delta": 0.04702673189687556
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 192.26448409491476,
          "fc_energy_kwh": 3.226911590751169,
          "fc_energy_efficiency": 0.5035616946168914,
          "fc_low_output_pct": 48.530805687203795,
          "battery_throughput_kwh": 2.1738392680552603,
          "battery_ohmic_loss_kwh": 0.1441977979134814,
          "soc_mean": 0.6140984909097984,
          "soc_delta": -1.3347151370675276
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 53.47505966893712,
          "fc_energy_kwh": 0.8388188480629577,
          "fc_energy_efficiency": 0.47063214713387097,
          "fc_low_output_pct": 78.43426883308715,
          "battery_throughput_kwh": 1.8191868756018237,
          "battery_ohmic_loss_kwh": 0.11391632923905065,
          "soc_mean": 0.6283029742548273,
          "soc_delta": 1.0582728144367015
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 299.8736333139417,
          "fc_energy_kwh": 5.181548465675691,
          "fc_energy_efficiency": 0.518425039414961,
          "fc_low_output_pct": 11.930585683297181,
          "battery_throughput_kwh": 1.0729746277091563,
          "battery_ohmic_loss_kwh": 0.0396630429497996,
          "soc_mean": 0.5804159560739341,
          "soc_delta": 0.09481839406846948
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
  "decision": "replace_champion",
  "experiment_plan": {
    "name": "archive",
    "iteration": 3
  },
  "edit_base": {
    "mode": "fuel_leader",
    "parent_reward_id": "17afbf80420cb9f947efdaac72a30bf9687444a44fa8df43fcfaa7ace533d083",
    "selection_reason": "fuel_leader: rank 1 of 1"
  },
  "candidate": {
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
  "verdict": {
    "status": "pass",
    "checks": {
      "total_cost_strictly_improved": true,
      "charge_sustaining": true,
      "fuel_within_guard": true,
      "battery_within_guard": true
    },
    "checkpoint_episode": 399,
    "cost_unit": "USD per 100 km",
    "total_cost_delta_usd": -11.442883188609635,
    "cost_delta_usd": {
      "h2_usd": -0.04432949167789424,
      "fc_usd": -10.793009421773625,
      "batt_usd": -0.6055442751581173
    },
    "soc_drift": -0.022351355986069854,
    "fuel_delta_gkm": -0.06332784525413437,
    "fc_loss_delta": -8.56131666728821e-05,
    "batt_loss_delta": -7.704006044950695e-05,
    "guards": {
      "reference": "baseline",
      "max_fuel_increase_fraction": 0.05,
      "max_batt_increase_fraction": 0.1,
      "fuel_gkm_max": 11.18909967951321,
      "batt_loss_max": 0.0005969470490372886,
      "soc_drift_abs_max": 0.05
    },
    "guard_reference": "same_as_cost_reference",
    "comparison_basis": "matched_fresh_training"
  },
  "observed_relation": {
    "vs_champion": "strict_pareto",
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
        "mean": 10.522227783061224,
        "std": 0.06648171723499345,
        "slope_per_10_episodes": 0.03562099179816322,
        "ep399_better_than_fraction": 0.125
      },
      "fc_loss": {
        "n": 40,
        "mean": 0.0001434360749754615,
        "std": 1.531597195167729e-05,
        "slope_per_10_episodes": 5.909686676557379e-06,
        "ep399_better_than_fraction": 0.45
      },
      "batt_loss": {
        "n": 40,
        "mean": 0.00046901508513810255,
        "std": 1.113190368293735e-05,
        "slope_per_10_episodes": 5.499473318582425e-07,
        "ep399_better_than_fraction": 0.55
      }
    },
    "lucky_checkpoint": false
  },
  "reward_diff": "--- parent:17afbf80420c\n+++ candidate\n@@ -1,30 +1,66 @@\n def get_reward(self):\n     soc = float(self.SOC)\n     soc_low, soc_high = self.soc_bounds\n-    # SOC deviation from target\n-    soc_err = (np.abs(soc - self.SOC_target)) ** 2\n-    w_soc = np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10, self.w_soc)\n-    soc_cost = w_soc * soc_err\n \n+    # ---------- Charge-sustaining family (soc_cost = sum of catalog terms) ----------\n+    # Catalog term: soc_anchor (baseline symmetric quadratic anchor with bounds multiplier)\n+    soc_tgt = float(self.SOC_target)\n+    soc_err = float(np.abs(soc - soc_tgt)) ** 2\n+    out_of_bounds = (soc >= float(soc_high)) or (soc <= float(soc_low))\n+    w_soc_eff = float(self.w_soc) * (10.0 if out_of_bounds else 1.0)\n+    term_soc_anchor = w_soc_eff * soc_err\n+    self.info[\"term_soc_anchor\"] = float(term_soc_anchor)\n+\n+    soc_cost = float(term_soc_anchor)\n+\n+    # ---------- Core operating-cost proxy terms (existing) ----------\n     h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal\n-    h2_cost = self.w_h2 * h2_fcs\n-    # Cost of fuel cell degradation (scaled)\n-    fcs_soh_cost = self.w_fc * float(self.dSOH_FCS)\n-    # Cost of battery degradation (scaled)\n-    batt_soh_cost = self.w_batt * float(self.dSOH_batt)\n+    h2_cost = float(self.w_h2) * float(h2_fcs)\n+    fcs_soh_cost = float(self.w_fc) * float(self.dSOH_FCS)\n+    batt_soh_cost = float(self.w_batt) * float(self.dSOH_batt)\n \n-    in_bounds = (soc_low < soc < soc_high)\n-    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost\n+    # ---------- Extra catalog price terms (ADDED): fc_efficiency_gap, batt_ohmic ----------\n+    # Catalog term: fc_efficiency_gap\n+    # eta = P_FCS / (120 * h2_fcs) for 1-s step, with 120 kJ/g LHV\n+    P_fcs_kw = float(self.P_FCS)\n+    h2_fcs_g = float(h2_fcs)\n+    eta_ref = 0.602  # peak measured band (10-15 kW) from EFFICIENCY FACTS\n+    eta = float(P_fcs_kw / (120.0 * h2_fcs_g)) if h2_fcs_g > 0.0 else 0.0\n+    eta_gap_frac = float(np.maximum(0.0, eta_ref - eta) / eta_ref) if h2_fcs_g > 0.0 else 0.0\n+    c_eff_gap = 5.0  # reward units per gram-scaled gap; moderate to satisfy deviation check\n+    term_fc_efficiency_gap = c_eff_gap * h2_fcs_g * eta_gap_frac\n+    self.info[\"term_fc_efficiency_gap\"] = float(term_fc_efficiency_gap)\n+\n+    # Catalog term: batt_ohmic\n+    P_batt_loss_kw = float(self.P_batt_loss_kw)\n+    c_batt_ohmic = 2.0  # reward units per kW-step; sized to be comparable to baseline mean soc_cost scale\n+    term_batt_ohmic = c_batt_ohmic * float(np.maximum(0.0, P_batt_loss_kw))\n+    self.info[\"term_batt_ohmic\"] = float(term_batt_ohmic)\n+\n+    # Total objective\n+    objective_cost = (\n+        soc_cost\n+        + h2_cost\n+        + fcs_soh_cost\n+        + batt_soh_cost\n+        + term_fc_efficiency_gap\n+        + term_batt_ohmic\n+    )\n     reward = float(-objective_cost)\n \n-    self.info.update({'EMS_reward': reward,\n-                      'h2_fcs': float(h2_fcs),\n-                      'h2_batt': float(h2_batt),\n-                      'h2_equal': float(h2_equal),\n-                      'soc_cost': float(soc_cost),\n-                      'h2_cost': float(h2_cost),\n-                      'fcs_soh_cost': float(fcs_soh_cost),\n-                      'batt_soh_cost': float(batt_soh_cost),\n-                      'objective_cost': float(objective_cost),\n-                      'soc_in_bounds': int(in_bounds)})\n+    in_bounds = (float(soc_low) < soc < float(soc_high))\n+    self.info.update(\n+        {\n+            \"EMS_reward\": float(reward),\n+            \"h2_fcs\": float(h2_fcs),\n+            \"h2_batt\": float(h2_batt),\n+            \"h2_equal\": float(h2_equal),\n+            \"soc_cost\": float(soc_cost),\n+            \"h2_cost\": float(h2_cost),\n+            \"fcs_soh_cost\": float(fcs_soh_cost),\n+            \"batt_soh_cost\": float(batt_soh_cost),\n+            \"objective_cost\": float(objective_cost),\n+            \"soc_in_bounds\": int(in_bounds),\n+        }\n+    )\n     retur"
}
```

[Training log](results/aroma_runs/seed1_obscur_20261018_061824_704722118/search/20261018_061824_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed1_obscur_seq_v3_catalog_iter6/trials/f10ea050f7c8decfbe311dc2/iter_001/train_log.log)
[Evaluation records](results/aroma_runs/seed1_obscur_20261018_061824_704722118/search/20261018_061824_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed1_obscur_seq_v3_catalog_iter6/trials/f10ea050f7c8decfbe311dc2/deterministic_evaluations.jsonl)
