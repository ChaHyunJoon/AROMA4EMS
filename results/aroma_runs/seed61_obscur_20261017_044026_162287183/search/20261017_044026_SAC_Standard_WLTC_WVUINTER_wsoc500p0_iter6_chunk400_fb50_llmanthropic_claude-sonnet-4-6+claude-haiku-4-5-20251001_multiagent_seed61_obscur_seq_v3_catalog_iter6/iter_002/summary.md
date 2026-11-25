# Iteration 2

Decision: **retain_champion**

```json
{
  "iteration": 2,
  "control": {
    "candidate_id": "17afbf80420cb9f947efdaac72a30bf9687444a44fa8df43fcfaa7ace533d083",
    "seed": 61,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.368679466188617,
      "fc_loss": 0.0004929689999854103,
      "batt_loss": 0.00047805274582957136,
      "soc_in_bounds": 100.0,
      "soc_min": 0.551525929333007,
      "soc_max": 0.6709449717569985
    },
    "operating_cost": {
      "h2_usd": 7.258075626332032,
      "fc_usd": 62.14720548551044,
      "batt_usd": 3.757552911714616,
      "degradation_usd": 65.90475839722505,
      "total_usd": 73.16283402355708,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.350719647201126,
      "soc_correction_gkm": 0.017959818987490474,
      "soc_final": 0.5903945215871,
      "soc_final_minus_initial": -0.009605478412899937,
      "unaccepted_fc_kwh": 0.0,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.385722875245106,
      "fc_loss": 0.0004935898645695685,
      "batt_loss": 0.0004940034588567816
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.5903945215871,
      "soc_final_minus_initial": -0.009605478412899937,
      "soc_swing": 0.11941904242399148,
      "soc_mean": 0.6026898638086382,
      "fc_power_kw_mean": 9.888809495318126,
      "fc_abs_ramp_kw_s_mean": 1.1199841441874725,
      "fc_on_pct": 68.87532693984308,
      "fc_start_stop_count": 25,
      "fc_start_stop_soh_loss": 0.00049,
      "fc_low_power_count": 340,
      "fc_low_power_soh_loss": 1.1899999999999998e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 3,
      "fc_load_change_soh_loss": 1.7790000000000002e-06,
      "battery_throughput_kwh": 4.3136880128134525,
      "battery_ohmic_loss_kw_integral_kwh": 0.22859309942537506,
      "fc_low_output_pct": 30.89218250508573,
      "fc_regeneration_energy_kwh": 0.5847137644898311,
      "fc_energy_efficiency": 0.5190446818575747
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
          "battery_ohmic_loss_kwh": 3.9558190348588274e-08,
          "soc_mean": 0.6230461588153884,
          "soc_delta": -0.00012331245936003654
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 86.41195239256726,
          "fc_energy_kwh": 1.5346450854168339,
          "fc_energy_efficiency": 0.5328424562035624,
          "fc_low_output_pct": 28.047091412742382,
          "battery_throughput_kwh": 0.8280082789362685,
          "battery_ohmic_loss_kwh": 0.018143855937291297,
          "soc_mean": 0.6125472393123876,
          "soc_delta": -0.030744283213567036
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 201.02522857567476,
          "fc_energy_kwh": 3.4685378038693084,
          "fc_energy_efficiency": 0.5176790072942563,
          "fc_low_output_pct": 29.383886255924168,
          "battery_throughput_kwh": 1.8848963778536032,
          "battery_ohmic_loss_kwh": 0.114899328385615,
          "soc_mean": 0.603556185960894,
          "soc_delta": -1.174601064287614
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 38.78951470705711,
          "fc_energy_kwh": 0.5847137644898311,
          "fc_energy_efficiency": 0.452265705923575,
          "fc_low_output_pct": 63.22008862629247,
          "battery_throughput_kwh": 1.6106837852815263,
          "battery_ohmic_loss_kwh": 0.09897901759612003,
          "soc_mean": 0.6150636118458233,
          "soc_delta": 0.939504627646831
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 291.99481103490604,
          "fc_energy_kwh": 5.058912532533184,
          "fc_energy_efficiency": 0.5198125052067246,
          "fc_low_output_pct": 11.171366594360087,
          "battery_throughput_kwh": 0.9138540746389853,
          "battery_ohmic_loss_kwh": 0.029133453822460582,
          "soc_mean": 0.5752691057956685,
          "soc_delta": 0.031606799212833825
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
    "iteration": 2
  },
  "edit_base": {
    "mode": "champion_improve",
    "parent_reward_id": "17afbf80420cb9f947efdaac72a30bf9687444a44fa8df43fcfaa7ace533d083",
    "selection_reason": "champion_improve: rank 1 of 1"
  },
  "candidate": {
    "candidate_id": "dd6bf7ad68dc759a0e8eab604662bfed0645f2ec9702f9318d56618f3cb10089",
    "seed": 61,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.416938091960285,
      "fc_loss": 0.00038760849998786817,
      "batt_loss": 0.0005433898415627691,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5485774680730577,
      "soc_max": 0.6444187504156749
    },
    "operating_cost": {
      "h2_usd": 7.2918566643722,
      "fc_usd": 48.86470568613733,
      "batt_usd": 4.271110456268034,
      "degradation_usd": 53.13581614240536,
      "total_usd": 60.42767280677756,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.457949191628417,
      "soc_correction_gkm": -0.041011099668132295,
      "soc_final": 0.6222541677164349,
      "soc_final_minus_initial": 0.02225416771643496,
      "unaccepted_fc_kwh": 0.0036320980564814717,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.436401381244469,
      "fc_loss": 0.0003894832499874268,
      "batt_loss": 0.0005383635017377292
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.6222541677164349,
      "soc_final_minus_initial": 0.02225416771643496,
      "soc_swing": 0.09584128234261713,
      "soc_mean": 0.6017664372041579,
      "fc_power_kw_mean": 10.001546851803115,
      "fc_abs_ramp_kw_s_mean": 1.7335466220713234,
      "fc_on_pct": 63.06306306306306,
      "fc_start_stop_count": 19,
      "fc_start_stop_soh_loss": 0.0003724,
      "fc_low_power_count": 279,
      "fc_low_power_soh_loss": 9.765e-07,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 24,
      "fc_load_change_soh_loss": 1.4232000000000002e-05,
      "battery_throughput_kwh": 4.955473425310211,
      "battery_ohmic_loss_kw_integral_kwh": 0.2795385780767453,
      "fc_low_output_pct": 24.673060156931125,
      "fc_regeneration_energy_kwh": 0.6300442228299055,
      "fc_energy_efficiency": 0.5185319012266847
    },
    "regimes": {
      "available": true,
      "groups": {
        "stopped": {
          "steps": 408,
          "available": true,
          "duration_s": 408.0,
          "hydrogen_g": 7.2744081338845,
          "fc_energy_kwh": 0.13025143759164245,
          "fc_energy_efficiency": 0.5372167534755257,
          "fc_low_output_pct": 1.715686274509804,
          "battery_throughput_kwh": 0.11145788807359765,
          "battery_ohmic_loss_kwh": 0.005497281814317556,
          "soc_mean": 0.623996312768747,
          "soc_delta": 0.0656411293246778
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 87.27711039014953,
          "fc_energy_kwh": 1.5292477173744017,
          "fc_energy_efficiency": 0.5257050733932505,
          "fc_low_output_pct": 27.70083102493075,
          "battery_throughput_kwh": 1.0760028911337107,
          "battery_ohmic_loss_kwh": 0.03134688605466637,
          "soc_mean": 0.610034486588434,
          "soc_delta": -0.04141282384106948
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 194.9763258420028,
          "fc_energy_kwh": 3.334906701015499,
          "fc_energy_efficiency": 0.5131761834112132,
          "fc_low_output_pct": 16.303317535545023,
          "battery_throughput_kwh": 2.160023305111355,
          "battery_ohmic_loss_kwh": 0.14523036576028567,
          "soc_mean": 0.5974969605228285,
          "soc_delta": -1.2546458520143755
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 38.42214982453879,
          "fc_energy_kwh": 0.6300442228299055,
          "fc_energy_efficiency": 0.49198748880326953,
          "fc_low_output_pct": 44.903988183161005,
          "battery_throughput_kwh": 1.6577707010963918,
          "battery_ohmic_loss_kwh": 0.10561860885842585,
          "soc_mean": 0.6079488342497706,
          "soc_delta": 0.9661243664741656
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 296.6208296147712,
          "fc_energy_kwh": 5.098157448300886,
          "fc_energy_efficiency": 0.5156752465753152,
          "fc_low_output_pct": 15.509761388286334,
          "battery_throughput_kwh": 1.044487895818366,
          "battery_ohmic_loss_kwh": 0.03635824407939233,
          "soc_mean": 0.58905715234104,
          "soc_delta": 0.05027444068978981
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
      "total_cost_strictly_improved": true,
      "charge_sustaining": true,
      "fuel_within_guard": true,
      "battery_within_guard": false
    },
    "checkpoint_episode": 399,
    "cost_unit": "USD per 100 km",
    "total_cost_delta_usd": -12.735161216779524,
    "cost_delta_usd": {
      "h2_usd": 0.033781038040167743,
      "fc_usd": -13.282499799373113,
      "batt_usd": 0.5135575445534184
    },
    "soc_drift": 0.02225416771643496,
    "fuel_delta_gkm": 0.04825862577166795,
    "fc_loss_delta": -0.00010536049999754216,
    "batt_loss_delta": 6.533709573319779e-05,
    "guards": {
      "reference": "baseline",
      "max_fuel_increase_fraction": 0.05,
      "max_batt_increase_fraction": 0.1,
      "fuel_gkm_max": 10.887113439498048,
      "batt_loss_max": 0.0005258580204125286,
      "soc_drift_abs_max": 0.05
    },
    "guard_reference": "same_as_cost_reference",
    "comparison_basis": "matched_fresh_training"
  },
  "observed_relation": {
    "vs_champion": "cost_tradeoff",
    "vs_baseline": "cost_tradeoff"
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
        "mean": 10.436401381244469,
        "std": 0.03942125126787779,
        "slope_per_10_episodes": -0.019548845420606205,
        "ep399_better_than_fraction": 0.65
      },
      "fc_loss": {
        "n": 40,
        "mean": 0.0003894832499874268,
        "std": 3.849388347056483e-05,
        "slope_per_10_episodes": 1.6052092870971575e-05,
        "ep399_better_than_fraction": 0.5
      },
      "batt_loss": {
        "n": 40,
        "mean": 0.0005383635017377292,
        "std": 9.263343914561942e-06,
        "slope_per_10_episodes": 4.2549938207001884e-07,
        "ep399_better_than_fraction": 0.325
      }
    },
    "lucky_checkpoint": false
  },
  "reward_diff": "--- parent:17afbf80420c\n+++ candidate\n@@ -1,30 +1,100 @@\n def get_reward(self):\n     soc = float(self.SOC)\n     soc_low, soc_high = self.soc_bounds\n-    # SOC deviation from target\n-    soc_err = (np.abs(soc - self.SOC_target)) ** 2\n-    w_soc = np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10, self.w_soc)\n-    soc_cost = w_soc * soc_err\n+    soc_init = float(self.SOC_init)\n+    soc_target = float(self.SOC_target)\n \n-    h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal\n-    h2_cost = self.w_h2 * h2_fcs\n-    # Cost of fuel cell degradation (scaled)\n+    # ------------------------------------------------------------------ #\n+    # CHARGE-SUSTAINING: soc_cost = soc_anchor + drift_barrier            #\n+    # ------------------------------------------------------------------ #\n+\n+    # --- term_soc_anchor (catalog: soc_anchor, symmetric, p=2) ----------\n+    # Raised w_soc from 500 to 700 to keep combined soc_cost above the\n+    # charge-sustaining sizing floor after adding drift_barrier.\n+    w_soc_eff = 700.0\n+    soc_err_sq = (soc - soc_target) ** 2\n+    # multiply by 10 outside soc_bounds (same shape as edit base)\n+    in_bounds = (soc_low < soc < soc_high)\n+    k_bounds = 10.0 if not in_bounds else 1.0\n+    term_soc_anchor = w_soc_eff * soc_err_sq * k_bounds\n+\n+    # --- term_drift_barrier (catalog: drift_barrier, new) ---------------\n+    # Flat for |SOC - SOC_init| <= d0 = 0.025, quadratic beyond.\n+    # Structural addition: the edit base has no drift_barrier.\n+    c_db = 800.0\n+    d0 = 0.025\n+    drift_excess = max(0.0, abs(soc - soc_init) - d0)\n+    term_drift_barrier = c_db * drift_excess ** 2\n+\n+    # soc_cost = sum of charge-sustaining terms\n+    soc_cost = term_soc_anchor + term_drift_barrier\n+\n+    # ------------------------------------------------------------------ #\n+    # HYDROGEN COST (reshaped: w_h2 raised from 10 to 12)                 #\n+    # CHANGE_SPEC: h2_cost \"changed\"                                       #\n+    # ------------------------------------------------------------------ #\n+    h2_fcs = float(self.h2_fcs)\n+    h2_batt = float(self.h2_batt)\n+    h2_equal = float(self.h2_equal)\n+\n+    w_h2_eff = 12.0\n+    h2_cost = w_h2_eff * h2_fcs\n+\n+    # ------------------------------------------------------------------ #\n+    # FC DEGRADATION COST (unchanged weight)                               #\n+    # ------------------------------------------------------------------ #\n     fcs_soh_cost = self.w_fc * float(self.dSOH_FCS)\n-    # Cost of battery degradation (scaled)\n+\n+    # ------------------------------------------------------------------ #\n+    # BATTERY DEGRADATION COST (unchanged weight)                          #\n+    # ------------------------------------------------------------------ #\n     batt_soh_cost = self.w_batt * float(self.dSOH_batt)\n \n-    in_bounds = (soc_low < soc < soc_high)\n-    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost\n+    # ------------------------------------------------------------------ #\n+    # EXTRA PRICE TERM: fc_efficiency_gap (catalog: fc_efficiency_gap)    #\n+    # New term: price H2 burned below peak efficiency eta_ref = 0.602.    #\n+    # eta = P_FCS / (120 * h2_fcs) when h2_fcs > 0, else 0.              #\n+    # CHANGE_SPEC: extra_terms \"added\"                                     #\n+    # ------------------------------------------------------------------ #\n+    eta_ref = 0.602\n+    p_fcs = float(self.P_FCS)   # kW\n+    if h2_fcs > 0.0:\n+        eta = p_fcs / (120.0 * h2_fcs)\n+        gap = max(0.0, eta_ref - eta) / eta_ref\n+        term_fc_efficiency_gap = 50.0 * h2_fcs * gap\n+    else:\n+        eta = 0.0\n+        gap = 0.0\n+        term_fc_efficiency_gap = 0.0\n+\n+    # ------------------------------------------------------------------ #\n+    # OBJECTIVE COST                                                        #\n+    # ------------------------------------------------------------------ #\n+    objective_cost = (so"
}
```

[Training log](results/aroma_runs/seed61_obscur_20261017_044026_162287183/search/20261017_044026_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed61_obscur_seq_v3_catalog_iter6/trials/87103ec00a5b3212322b0114/iter_001/train_log.log)
[Evaluation records](results/aroma_runs/seed61_obscur_20261017_044026_162287183/search/20261017_044026_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed61_obscur_seq_v3_catalog_iter6/trials/87103ec00a5b3212322b0114/deterministic_evaluations.jsonl)
