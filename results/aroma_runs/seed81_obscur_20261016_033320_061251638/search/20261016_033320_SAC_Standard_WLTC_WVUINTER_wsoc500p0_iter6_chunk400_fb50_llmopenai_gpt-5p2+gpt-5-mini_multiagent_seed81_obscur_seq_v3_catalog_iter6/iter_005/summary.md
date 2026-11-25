# Iteration 5

Decision: **retain_champion**

```json
{
  "iteration": 5,
  "control": {
    "candidate_id": "17afbf80420cb9f947efdaac72a30bf9687444a44fa8df43fcfaa7ace533d083",
    "seed": 81,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.838062644164271,
      "fc_loss": 0.00018646449997072878,
      "batt_loss": 0.0006140980938273977,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5219102773508741,
      "soc_max": 0.7005968306189944
    },
    "operating_cost": {
      "h2_usd": 7.58664385091499,
      "fc_usd": 23.507051347603593,
      "batt_usd": 4.826885946518908,
      "degradation_usd": 28.3339372941225,
      "total_usd": 35.92058114503749,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 11.015494047079216,
      "soc_correction_gkm": -0.1774314029149446,
      "soc_final": 0.6933909074637872,
      "soc_final_minus_initial": 0.0933909074637872,
      "unaccepted_fc_kwh": 0.0029069897429724813,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.804265071761517,
      "fc_loss": 0.00023094022497543442,
      "batt_loss": 0.0006092576054848586
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.6933909074637872,
      "soc_final_minus_initial": 0.0933909074637872,
      "soc_swing": 0.17868655326812022,
      "soc_mean": 0.6141031181647345,
      "fc_power_kw_mean": 10.331529178127507,
      "fc_abs_ramp_kw_s_mean": 1.644182118823985,
      "fc_on_pct": 89.97384481255449,
      "fc_start_stop_count": 9,
      "fc_start_stop_soh_loss": 0.0001764,
      "fc_low_power_count": 673,
      "fc_low_power_soh_loss": 2.3554999999999997e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 13,
      "fc_load_change_soh_loss": 7.709000000000002e-06,
      "battery_throughput_kwh": 5.656315904706234,
      "battery_ohmic_loss_kw_integral_kwh": 0.3304574340924226,
      "fc_low_output_pct": 60.33129904097646,
      "fc_regeneration_energy_kwh": 1.149410317593584,
      "fc_energy_efficiency": 0.5108128448435574
    },
    "regimes": {
      "available": true,
      "groups": {
        "stopped": {
          "steps": 408,
          "available": true,
          "duration_s": 408.0,
          "hydrogen_g": 9.788494045905244,
          "fc_energy_kwh": 0.09399491909818601,
          "fc_energy_efficiency": 0.2881065843916917,
          "fc_low_output_pct": 34.55882352941176,
          "battery_throughput_kwh": 0.06651828580241553,
          "battery_ohmic_loss_kwh": 0.0007137165333119277,
          "soc_mean": 0.672912275543433,
          "soc_delta": 0.040520013822578194
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 123.53653394556694,
          "fc_energy_kwh": 2.0493771900734465,
          "fc_energy_efficiency": 0.4977269677627597,
          "fc_low_output_pct": 68.69806094182826,
          "battery_throughput_kwh": 0.9053698368957496,
          "battery_ohmic_loss_kwh": 0.019313540035792498,
          "soc_mean": 0.6393014847682068,
          "soc_delta": 0.21299188736798458
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 196.8043123343204,
          "fc_energy_kwh": 3.304912114645745,
          "fc_energy_efficiency": 0.5038369230387906,
          "fc_low_output_pct": 71.09004739336493,
          "battery_throughput_kwh": 2.361892024078149,
          "battery_ohmic_loss_kwh": 0.16692266367602734,
          "soc_mean": 0.6197806999084543,
          "soc_delta": -1.3162099965334892
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 69.1166456393207,
          "fc_energy_kwh": 1.149410317593584,
          "fc_energy_efficiency": 0.49895011230115044,
          "fc_low_output_pct": 81.0930576070901,
          "battery_throughput_kwh": 2.08403599630716,
          "battery_ohmic_loss_kwh": 0.13406456542167658,
          "soc_mean": 0.6334005963752112,
          "soc_delta": 1.2103126616978916
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 298.9610683091209,
          "fc_energy_kwh": 5.177544911456666,
          "fc_energy_efficiency": 0.5196057212748256,
          "fc_low_output_pct": 15.184381778741866,
          "battery_throughput_kwh": 1.1015617550527097,
          "battery_ohmic_loss_kwh": 0.042483578869247716,
          "soc_mean": 0.5516001004095981,
          "soc_delta": 0.09475896273611428
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
    "parent_reward_id": "17afbf80420cb9f947efdaac72a30bf9687444a44fa8df43fcfaa7ace533d083",
    "selection_reason": "champion_improve: rank 1 of 1"
  },
  "candidate": {
    "candidate_id": "4181ee36f97a184d3f6b238ba3a42eb6e19a9fb139e69b6195e3519178176ea5",
    "seed": 81,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.444853555713188,
      "fc_loss": 0.00023739599998018335,
      "batt_loss": 0.00048805745747959595,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5047486174317077,
      "soc_max": 0.64491237007285
    },
    "operating_cost": {
      "h2_usd": 7.311397488999232,
      "fc_usd": 29.92784128949959,
      "batt_usd": 3.8361911660063654,
      "degradation_usd": 33.764032455505955,
      "total_usd": 41.07542994450519,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.371475160991384,
      "soc_correction_gkm": 0.07337839472180473,
      "soc_final": 0.5611236818954893,
      "soc_final_minus_initial": -0.03887631810451064,
      "unaccepted_fc_kwh": 0.0,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.428200549235696,
      "fc_loss": 0.0002448686895642205,
      "batt_loss": 0.0004801253421190338
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.5611236818954893,
      "soc_final_minus_initial": -0.03887631810451064,
      "soc_swing": 0.14016375264114223,
      "soc_mean": 0.5919975049083677,
      "fc_power_kw_mean": 9.867100150709614,
      "fc_abs_ramp_kw_s_mean": 1.191547462356119,
      "fc_on_pct": 65.50421389131067,
      "fc_start_stop_count": 12,
      "fc_start_stop_soh_loss": 0.00023520000000000002,
      "fc_low_power_count": 458,
      "fc_low_power_soh_loss": 1.603e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 1,
      "fc_load_change_soh_loss": 5.930000000000001e-07,
      "battery_throughput_kwh": 4.499804020444302,
      "battery_ohmic_loss_kw_integral_kwh": 0.2369052738065236,
      "fc_low_output_pct": 27.521069456553327,
      "fc_regeneration_energy_kwh": 0.6152085680179041,
      "fc_energy_efficiency": 0.5141674989584539
    },
    "regimes": {
      "available": true,
      "groups": {
        "stopped": {
          "steps": 408,
          "available": true,
          "duration_s": 408.0,
          "hydrogen_g": 0.06114545231734987,
          "fc_energy_kwh": 0.00029561388700470847,
          "fc_energy_efficiency": 0.14505254609063808,
          "fc_low_output_pct": 0.24509803921568626,
          "battery_throughput_kwh": 0.00035055587962853625,
          "battery_ohmic_loss_kwh": 4.196857391846468e-07,
          "soc_mean": 0.6065599293966896,
          "soc_delta": -2.9924661674285424e-05
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 79.91418896580467,
          "fc_energy_kwh": 1.3427656580999674,
          "fc_energy_efficiency": 0.5041282275927513,
          "fc_low_output_pct": 28.462603878116344,
          "battery_throughput_kwh": 0.9585163705290104,
          "battery_ohmic_loss_kwh": 0.027423985775814903,
          "soc_mean": 0.5974306708166133,
          "soc_delta": -0.14005668671257265
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 195.54170790370796,
          "fc_energy_kwh": 3.375059483225619,
          "fc_energy_efficiency": 0.517853258895041,
          "fc_low_output_pct": 15.734597156398102,
          "battery_throughput_kwh": 1.9250971615691217,
          "battery_ohmic_loss_kwh": 0.1145167770223419,
          "soc_mean": 0.5873469755656524,
          "soc_delta": -1.2187388861686739
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 40.881029969190116,
          "fc_energy_kwh": 0.6152085680179041,
          "fc_energy_efficiency": 0.451507774259433,
          "fc_low_output_pct": 60.118168389955684,
          "battery_throughput_kwh": 1.6381763594892176,
          "battery_ohmic_loss_kwh": 0.10026571134058214,
          "soc_mean": 0.5986626221046786,
          "soc_delta": 0.9582110350684258
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 298.9571613579153,
          "fc_energy_kwh": 5.1623014803312435,
          "fc_energy_efficiency": 0.5180826984030461,
          "fc_low_output_pct": 12.906724511930587,
          "battery_throughput_kwh": 0.9113453107469532,
          "battery_ohmic_loss_kwh": 0.034322420840587786,
          "soc_mean": 0.5824378192978436,
          "soc_delta": 0.08537944914721118
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
    "total_cost_delta_usd": 5.1548487994677,
    "cost_delta_usd": {
      "h2_usd": -0.2752463619157579,
      "fc_usd": 6.420789941895997,
      "batt_usd": -0.9906947805125421
    },
    "soc_drift": -0.03887631810451064,
    "fuel_delta_gkm": -0.3932090884510835,
    "fc_loss_delta": 5.093150000945457e-05,
    "batt_loss_delta": -0.00012604063634780172,
    "guards": {
      "reference": "baseline",
      "max_fuel_increase_fraction": 0.05,
      "max_batt_increase_fraction": 0.1,
      "fuel_gkm_max": 11.379965776372485,
      "batt_loss_max": 0.0006755079032101375,
      "soc_drift_abs_max": 0.05
    },
    "guard_reference": "same_as_cost_reference",
    "comparison_basis": "matched_fresh_training"
  },
  "observed_relation": {
    "vs_champion": "objective_tradeoff",
    "vs_baseline": "objective_tradeoff"
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
        "mean": 10.428200549235696,
        "std": 0.04550801386498473,
        "slope_per_10_episodes": 0.018187448722165423,
        "ep399_better_than_fraction": 0.2
      },
      "fc_loss": {
        "n": 40,
        "mean": 0.0002448686895642205,
        "std": 4.85879965373653e-05,
        "slope_per_10_episodes": 5.396887193991924e-06,
        "ep399_better_than_fraction": 0.375
      },
      "batt_loss": {
        "n": 40,
        "mean": 0.0004801253421190338,
        "std": 8.743003884566279e-06,
        "slope_per_10_episodes": -3.212279745515846e-06,
        "ep399_better_than_fraction": 0.2
      }
    },
    "lucky_checkpoint": false
  },
  "reward_diff": "--- parent:17afbf80420c\n+++ candidate\n@@ -1,30 +1,56 @@\n def get_reward(self):\n     soc = float(self.SOC)\n     soc_low, soc_high = self.soc_bounds\n-    # SOC deviation from target\n-    soc_err = (np.abs(soc - self.SOC_target)) ** 2\n-    w_soc = np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10, self.w_soc)\n-    soc_cost = w_soc * soc_err\n \n-    h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal\n-    h2_cost = self.w_h2 * h2_fcs\n-    # Cost of fuel cell degradation (scaled)\n-    fcs_soh_cost = self.w_fc * float(self.dSOH_FCS)\n-    # Cost of battery degradation (scaled)\n-    batt_soh_cost = self.w_batt * float(self.dSOH_batt)\n+    # ---------- Charge-sustaining terms (must sum into soc_cost) ----------\n+    # term_soc_anchor (catalog: soc_anchor) [same as edit_base: symmetric quadratic, k=10 outside bounds]\n+    soc_err2 = float(np.abs(soc - float(self.SOC_target)) ** 2)\n+    w_soc_eff = float(np.where((soc >= soc_high) | (soc <= soc_low), float(self.w_soc) * 10.0, float(self.w_soc)))\n+    term_soc_anchor = w_soc_eff * soc_err2\n \n-    in_bounds = (soc_low < soc < soc_high)\n+    # term_drift_barrier (catalog: drift_barrier) [ADDED]\n+    # Deadband d0 must be < soc_drift_abs_max and checked to be zero for |SOC-SOC_init|<=0.01.\n+    d0 = 0.01\n+    drift_abs = float(np.abs(soc - float(self.SOC_init)))\n+    drift_excess = float(np.maximum(0.0, drift_abs - d0))\n+    # Coefficient sized to matter per-step (not terminal-only) while staying within DRIFT FACTS range on edit_base rollout.\n+    c_drift = 500.0\n+    term_drift_barrier = c_drift * (drift_excess ** 2)\n+\n+    soc_cost = term_soc_anchor + term_drift_barrier\n+\n+    # ---------- Objective price terms (unchanged) ----------\n+    h2_fcs = float(self.h2_fcs)\n+    h2_batt = float(self.h2_batt)\n+    h2_equal = float(self.h2_equal)\n+\n+    h2_cost = float(self.w_h2) * h2_fcs\n+    fcs_soh_cost = float(self.w_fc) * float(self.dSOH_FCS)\n+    batt_soh_cost = float(self.w_batt) * float(self.dSOH_batt)\n+\n     objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost\n     reward = float(-objective_cost)\n \n-    self.info.update({'EMS_reward': reward,\n-                      'h2_fcs': float(h2_fcs),\n-                      'h2_batt': float(h2_batt),\n-                      'h2_equal': float(h2_equal),\n-                      'soc_cost': float(soc_cost),\n-                      'h2_cost': float(h2_cost),\n-                      'fcs_soh_cost': float(fcs_soh_cost),\n-                      'batt_soh_cost': float(batt_soh_cost),\n-                      'objective_cost': float(objective_cost),\n-                      'soc_in_bounds': int(in_bounds)})\n+    in_bounds = (soc_low < soc < soc_high)\n+\n+    # ---------- Required logging ----------\n+    self.info.update({\n+        'EMS_reward': reward,\n+        'h2_fcs': float(h2_fcs),\n+        'h2_batt': float(h2_batt),\n+        'h2_equal': float(h2_equal),\n+\n+        # Catalog-term logs (plain values, before summing)\n+        'term_soc_anchor': float(term_soc_anchor),\n+        'term_drift_barrier': float(term_drift_barrier),\n+\n+        # Keep these four logs truthful for their own terms\n+        'soc_cost': float(soc_cost),\n+        'h2_cost': float(h2_cost),\n+        'fcs_soh_cost': float(fcs_soh_cost),\n+        'batt_soh_cost': float(batt_soh_cost),\n+\n+        'objective_cost': float(objective_cost),\n+        'soc_in_bounds': int(in_bounds),\n+    })\n     return reward\n"
}
```

[Training log](results/aroma_runs/seed81_obscur_20261016_033320_061251638/search/20261016_033320_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed81_obscur_seq_v3_catalog_iter6/trials/7a199b6d8f91ebcd1b77c3a1/iter_001/train_log.log)
[Evaluation records](results/aroma_runs/seed81_obscur_20261016_033320_061251638/search/20261016_033320_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed81_obscur_seq_v3_catalog_iter6/trials/7a199b6d8f91ebcd1b77c3a1/deterministic_evaluations.jsonl)
