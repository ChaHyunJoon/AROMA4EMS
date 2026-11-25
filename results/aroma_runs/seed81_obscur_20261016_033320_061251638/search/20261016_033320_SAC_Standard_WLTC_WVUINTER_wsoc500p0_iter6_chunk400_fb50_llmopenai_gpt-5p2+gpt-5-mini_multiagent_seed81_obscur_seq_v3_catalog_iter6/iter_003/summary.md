# Iteration 3

Decision: **retain_champion**

```json
{
  "iteration": 3,
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
    "iteration": 3
  },
  "edit_base": {
    "mode": "fuel_leader",
    "parent_reward_id": "efd23e53013548d794da5445a233514afd31b1c9e93801303f12be34d3b7ac07",
    "selection_reason": "fuel_leader: rank 1 of 2"
  },
  "candidate": {
    "candidate_id": "12d8a917f37bc0baf8c6450aa882b073e9dcd8efbcf7d6d95a336f1f11b56dff",
    "seed": 81,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.21571403460258,
      "fc_loss": 0.0011823484999878842,
      "batt_loss": 0.0003211765847781489,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5518389836015112,
      "soc_max": 0.6317172068166218
    },
    "operating_cost": {
      "h2_usd": 7.150999824221807,
      "fc_usd": 149.0553263722602,
      "batt_usd": 2.5244871446422663,
      "degradation_usd": 151.57981351690248,
      "total_usd": 158.73081334112427,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.147743572632196,
      "soc_correction_gkm": 0.06797046197038417,
      "soc_final": 0.5639314747295907,
      "soc_final_minus_initial": -0.03606852527040927,
      "unaccepted_fc_kwh": 0.0,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.238946854949962,
      "fc_loss": 0.0012078579624873298,
      "batt_loss": 0.00033223345315560595
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.5639314747295907,
      "soc_final_minus_initial": -0.03606852527040927,
      "soc_swing": 0.07987822321511062,
      "soc_mean": 0.5856775596058036,
      "fc_power_kw_mean": 9.705040142870425,
      "fc_abs_ramp_kw_s_mean": 1.5678186760261272,
      "fc_on_pct": 60.33129904097646,
      "fc_start_stop_count": 60,
      "fc_start_stop_soh_loss": 0.001176,
      "fc_low_power_count": 289,
      "fc_low_power_soh_loss": 1.0115e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 9,
      "fc_load_change_soh_loss": 5.337e-06,
      "battery_throughput_kwh": 2.815098377078473,
      "battery_ohmic_loss_kw_integral_kwh": 0.11207550719383684,
      "fc_low_output_pct": 24.062772449869225,
      "fc_regeneration_energy_kwh": 0.08088163243352967,
      "fc_energy_efficiency": 0.5149865238210449
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
          "battery_ohmic_loss_kwh": 4.0061561203476406e-08,
          "soc_mean": 0.5997062635439385,
          "soc_delta": -0.00012406996660385694
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 67.18076756946994,
          "fc_energy_kwh": 1.104828549895767,
          "fc_energy_efficiency": 0.49341757341082365,
          "fc_low_output_pct": 40.23545706371191,
          "battery_throughput_kwh": 0.5930548136774135,
          "battery_ohmic_loss_kwh": 0.01013556504960775,
          "soc_mean": 0.5899606907615925,
          "soc_delta": -0.2668030485260018
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 251.98623155048148,
          "fc_energy_kwh": 4.321435473982559,
          "fc_energy_efficiency": 0.5145361674115297,
          "fc_low_output_pct": 24.834123222748815,
          "battery_throughput_kwh": 1.132155987320991,
          "battery_ohmic_loss_kwh": 0.04191171314611053,
          "soc_mean": 0.5860923833081094,
          "soc_delta": -0.6530522296925982
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 7.657483518343908,
          "fc_energy_kwh": 0.08088163243352967,
          "fc_energy_efficiency": 0.31690458573718616,
          "fc_low_output_pct": 15.5096011816839,
          "battery_throughput_kwh": 1.2057801136913897,
          "battery_ohmic_loss_kwh": 0.06507322732313858,
          "soc_mean": 0.5908851176486947,
          "soc_delta": 0.7112301617665366
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 290.01321646492386,
          "fc_energy_kwh": 4.991132711116303,
          "fc_energy_efficiency": 0.5163521788919012,
          "fc_low_output_pct": 13.449023861171366,
          "battery_throughput_kwh": 0.4481588395091987,
          "battery_ohmic_loss_kwh": 0.008783476772960234,
          "soc_mean": 0.5752672054920127,
          "soc_delta": 0.01183471939675751
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
    "total_cost_delta_usd": 122.81023219608679,
    "cost_delta_usd": {
      "h2_usd": -0.4356440266931827,
      "fc_usd": 125.5482750246566,
      "batt_usd": -2.3023988018766413
    },
    "soc_drift": -0.03606852527040927,
    "fuel_delta_gkm": -0.6223486095616906,
    "fc_loss_delta": 0.0009958840000171554,
    "batt_loss_delta": -0.00029292150904924874,
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
        "mean": 10.238946854949962,
        "std": 0.039346945801935325,
        "slope_per_10_episodes": -0.012172138348045758,
        "ep399_better_than_fraction": 0.8
      },
      "fc_loss": {
        "n": 40,
        "mean": 0.0012078579624873298,
        "std": 9.79819691603872e-05,
        "slope_per_10_episodes": 4.969975938067211e-05,
        "ep399_better_than_fraction": 0.575
      },
      "batt_loss": {
        "n": 40,
        "mean": 0.00033223345315560595,
        "std": 1.4252236190442557e-05,
        "slope_per_10_episodes": -9.952908404734537e-06,
        "ep399_better_than_fraction": 0.7
      }
    },
    "lucky_checkpoint": false
  },
  "reward_diff": "--- parent:efd23e530135\n+++ candidate\n@@ -8,22 +8,34 @@\n     w_soc_eff = float(np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10.0, self.w_soc))\n     term_soc_anchor = w_soc_eff * soc_err2\n \n-    # term_fc_surplus_charge (catalog: fc_surplus_charge)\n+    # term_fc_surplus_charge (catalog: fc_surplus_charge)  [UNCHANGED FORM]\n     # g(SOC)=max(0,(SOC - SOC_target + 0.10)/0.10), nondecreasing; zero at/below SOC_target-0.10\n     m = 0.10\n     g_soc = float(np.maximum(0.0, (soc - float(self.SOC_target) + m) / m))\n \n     # P_fc_to_batt_kw = max(0, min(-P_batt, P_mot - P_batt)) / 1000  (per catalog)\n-    # self.P_batt, self.P_mot are in W; self.P_batt > 0 means discharge, < 0 means charging\n-    P_batt_w = float(self.P_batt)\n+    P_batt_w = float(self.P_batt)  # + discharge, - charge\n     P_mot_w = float(self.P_mot)\n     fc_to_batt_w = float(np.maximum(0.0, np.minimum(-P_batt_w, P_mot_w - P_batt_w)))\n     P_fc_to_batt_kw = fc_to_batt_w / 1000.0\n \n-    c_fc_surplus = 1.5  # reward_units per (kW*step), sized per orchestrator (DRIFT FACTS range)\n+    c_fc_surplus = 1.5  # reward_units per (kW*step)  [UNCHANGED]\n     term_fc_surplus_charge = c_fc_surplus * g_soc * P_fc_to_batt_kw\n \n-    soc_cost = term_soc_anchor + term_fc_surplus_charge\n+    # term_drift_barrier (catalog: drift_barrier)  [ADDED PER CHANGE_SPEC]\n+    # Penalize sustained drift away from SOC_init beyond a small band (per-step, not terminal-only).\n+    # d0 must be < soc_drift_abs_max (=0.05); choose d0=0.02 to start pricing before the guard.\n+    d0 = 0.02\n+    drift_abs = float(np.abs(soc - float(self.SOC_init)))\n+    drift_excess = float(np.maximum(0.0, drift_abs - d0))\n+    # Coefficient sizing target (from DRIFT FACTS on edit_base rollout):\n+    # 1377 steps have |SOC-SOC_init|>0.025. We want total added cost ~ geometric mean 1.343e4,\n+    # i.e. ~9.75 reward-units/step over those steps. With typical drift_excess ~0.02-0.03,\n+    # drift_excess^2 ~4e-4..9e-4, so c ~ (9.75)/(4e-4..9e-4) ≈ 1.1e4..2.4e4. Pick 1.5e4.\n+    c_drift = 15000.0\n+    term_drift_barrier = c_drift * (drift_excess ** 2)\n+\n+    soc_cost = term_soc_anchor + term_fc_surplus_charge + term_drift_barrier\n \n     # ---------- Objective price terms (unchanged) ----------\n     h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal\n@@ -47,6 +59,7 @@\n         # Catalog-term logs (plain values, before summing)\n         'term_soc_anchor': float(term_soc_anchor),\n         'term_fc_surplus_charge': float(term_fc_surplus_charge),\n+        'term_drift_barrier': float(term_drift_barrier),\n \n         # Keep these four logs truthful for their own terms\n         'soc_cost': float(soc_cost),\n"
}
```

[Training log](results/aroma_runs/seed81_obscur_20261016_033320_061251638/search/20261016_033320_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed81_obscur_seq_v3_catalog_iter6/trials/15b878c94902d9d58c9e2723/iter_001/train_log.log)
[Evaluation records](results/aroma_runs/seed81_obscur_20261016_033320_061251638/search/20261016_033320_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed81_obscur_seq_v3_catalog_iter6/trials/15b878c94902d9d58c9e2723/deterministic_evaluations.jsonl)
