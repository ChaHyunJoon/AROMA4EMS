# Iteration 4

Decision: **retain_champion**

```json
{
  "iteration": 4,
  "control": {
    "candidate_id": "17afbf80420cb9f947efdaac72a30bf9687444a44fa8df43fcfaa7ace533d083",
    "seed": 41,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 11.267763405434842,
      "fc_loss": 0.000321448999946794,
      "batt_loss": 0.0005755324677042539,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5427557043950955,
      "soc_max": 0.7848309797753499
    },
    "operating_cost": {
      "h2_usd": 7.88743438380439,
      "fc_usd": 40.52416491381096,
      "batt_usd": 4.52375541961513,
      "degradation_usd": 45.047920333426084,
      "total_usd": 52.935354717230474,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 11.631791603870743,
      "soc_correction_gkm": -0.36402819843590245,
      "soc_final": 0.7848309797753499,
      "soc_final_minus_initial": 0.1848309797753499,
      "unaccepted_fc_kwh": 0.0008152458432027427,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 11.170457610474221,
      "fc_loss": 0.00031377086245310546,
      "batt_loss": 0.0006188561520595687
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.7848309797753499,
      "soc_final_minus_initial": 0.1848309797753499,
      "soc_swing": 0.24207527538025442,
      "soc_mean": 0.617364544552925,
      "fc_power_kw_mean": 10.483248046730951,
      "fc_abs_ramp_kw_s_mean": 1.777515488526801,
      "fc_on_pct": 99.3897122929381,
      "fc_start_stop_count": 16,
      "fc_start_stop_soh_loss": 0.00031360000000000003,
      "fc_low_power_count": 1226,
      "fc_low_power_soh_loss": 4.291e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 6,
      "fc_load_change_soh_loss": 3.5580000000000005e-06,
      "battery_throughput_kwh": 5.184095681160171,
      "battery_ohmic_loss_kw_integral_kwh": 0.27789422272453795,
      "fc_low_output_pct": 66.95727986050566,
      "fc_regeneration_energy_kwh": 0.8552505442453315,
      "fc_energy_efficiency": 0.4916866101093882
    },
    "regimes": {
      "available": true,
      "groups": {
        "stopped": {
          "steps": 408,
          "available": true,
          "duration_s": 408.0,
          "hydrogen_g": 30.517653796098003,
          "fc_energy_kwh": 0.33074161666203544,
          "fc_energy_efficiency": 0.3251639490455275,
          "fc_low_output_pct": 95.83333333333334,
          "battery_throughput_kwh": 0.24331280242778283,
          "battery_ohmic_loss_kwh": 0.004137849732290317,
          "soc_mean": 0.6738289018583526,
          "soc_delta": 0.14695804186610606
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 139.08327013501957,
          "fc_energy_kwh": 2.113033407752638,
          "fc_energy_efficiency": 0.45582291748842835,
          "fc_low_output_pct": 90.65096952908587,
          "battery_throughput_kwh": 1.096613176921308,
          "battery_ohmic_loss_kwh": 0.02261888693029128,
          "soc_mean": 0.6403404885273243,
          "soc_delta": 0.22003515943660346
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 212.09616976406218,
          "fc_energy_kwh": 3.530129589097236,
          "fc_energy_efficiency": 0.4993700699010711,
          "fc_low_output_pct": 64.739336492891,
          "battery_throughput_kwh": 2.1191501050811756,
          "battery_ohmic_loss_kwh": 0.1489556543019183,
          "soc_mean": 0.6187549593580652,
          "soc_delta": -1.181980489272552
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 59.87113768520258,
          "fc_energy_kwh": 0.8552505442453315,
          "fc_energy_efficiency": 0.428588520741197,
          "fc_low_output_pct": 90.10339734121122,
          "battery_throughput_kwh": 1.823549474145427,
          "battery_ohmic_loss_kwh": 0.10262315112999973,
          "soc_mean": 0.6292175099750802,
          "soc_delta": 1.0685839504939247
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 293.4874612994399,
          "fc_energy_kwh": 5.053548931294675,
          "fc_energy_efficiency": 0.5166204696804872,
          "fc_low_output_pct": 13.774403470715836,
          "battery_throughput_kwh": 0.8647975501555727,
          "battery_ohmic_loss_kwh": 0.02709760646439159,
          "soc_mean": 0.570431589661366,
          "soc_delta": 0.03267610939938215
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
    "iteration": 4
  },
  "edit_base": {
    "mode": "guard_repair",
    "parent_reward_id": "fd453666c82582ad9c860a7d45df21f0efbe27b757448de0bce5c2349df38b3a",
    "selection_reason": "guard_repair: rank 1 of 1"
  },
  "candidate": {
    "candidate_id": "433d2659d7a7b27a2cf16dd99928418c11528eec719aa62ad52c50e020bc78c8",
    "seed": 41,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.538606940147615,
      "fc_loss": 0.001128436499971297,
      "batt_loss": 0.00037557828829659634,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5416933707734448,
      "soc_max": 0.6277339542521964
    },
    "operating_cost": {
      "h2_usd": 7.37702485810333,
      "fc_usd": 142.25879323677935,
      "batt_usd": 2.9520911721084184,
      "degradation_usd": 145.21088440888778,
      "total_usd": 152.58790926699112,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.50410690811229,
      "soc_correction_gkm": 0.03450003203532478,
      "soc_final": 0.5820765914764113,
      "soc_final_minus_initial": -0.017923408523588646,
      "unaccepted_fc_kwh": 0.0,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.470735326416653,
      "fc_loss": 0.000919491449974627,
      "batt_loss": 0.00038004705603603974
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.5820765914764113,
      "soc_final_minus_initial": -0.017923408523588646,
      "soc_swing": 0.08604058347875154,
      "soc_mean": 0.5715794667876896,
      "fc_power_kw_mean": 9.807432531760279,
      "fc_abs_ramp_kw_s_mean": 1.4989404175035888,
      "fc_on_pct": 69.68904388259227,
      "fc_start_stop_count": 57,
      "fc_start_stop_soh_loss": 0.0011172,
      "fc_low_power_count": 669,
      "fc_low_power_soh_loss": 2.3415e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 15,
      "fc_load_change_soh_loss": 8.895e-06,
      "battery_throughput_kwh": 3.410137490827067,
      "battery_ohmic_loss_kw_integral_kwh": 0.1447522056164369,
      "fc_low_output_pct": 35.62917756466143,
      "fc_regeneration_energy_kwh": 0.19291558395639047,
      "fc_energy_efficiency": 0.5041837055429202
    },
    "regimes": {
      "available": true,
      "groups": {
        "stopped": {
          "steps": 408,
          "available": true,
          "duration_s": 408.0,
          "hydrogen_g": 0.06039859689900664,
          "fc_energy_kwh": 0.00026552393845297585,
          "fc_energy_efficiency": 0.13189900451480202,
          "fc_low_output_pct": 0.24509803921568626,
          "battery_throughput_kwh": 0.00032726346432575,
          "battery_ohmic_loss_kwh": 3.111143823170732e-07,
          "soc_mean": 0.5909207505105349,
          "soc_delta": -4.477767653920939e-05
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 76.87104742730153,
          "fc_energy_kwh": 1.1712834850892169,
          "fc_energy_efficiency": 0.4571554561915715,
          "fc_low_output_pct": 52.42382271468144,
          "battery_throughput_kwh": 0.5784857037564054,
          "battery_ohmic_loss_kwh": 0.009752154490757062,
          "soc_mean": 0.5791406829833803,
          "soc_delta": -0.24252294918514827
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 243.34882601332336,
          "fc_energy_kwh": 4.157669067023598,
          "fc_energy_efficiency": 0.5126079640856982,
          "fc_low_output_pct": 38.48341232227488,
          "battery_throughput_kwh": 1.4620071335438147,
          "battery_ohmic_loss_kwh": 0.06469827559814137,
          "soc_mean": 0.5707102373805439,
          "soc_delta": -0.7700554458533838
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 18.81904149143917,
          "fc_energy_kwh": 0.19291558395639047,
          "fc_energy_efficiency": 0.3075632904022792,
          "fc_low_output_pct": 38.70014771048744,
          "battery_throughput_kwh": 1.2860499568687307,
          "battery_ohmic_loss_kwh": 0.069661287578292,
          "soc_mean": 0.5769624481924391,
          "soc_delta": 0.7599588730489981
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 296.6246787806976,
          "fc_energy_kwh": 5.069823046824364,
          "fc_energy_efficiency": 0.5128025861510642,
          "fc_low_output_pct": 17.35357917570499,
          "battery_throughput_kwh": 0.6661920577724729,
          "battery_ohmic_loss_kwh": 0.017044037581312822,
          "soc_mean": 0.5602622489764033,
          "soc_delta": 0.04968637127047548
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
    "total_cost_delta_usd": 99.65255454976065,
    "cost_delta_usd": {
      "h2_usd": -0.5104095257010597,
      "fc_usd": 101.7346283229684,
      "batt_usd": -1.5716642475067113
    },
    "soc_drift": -0.017923408523588646,
    "fuel_delta_gkm": -0.7291564652872271,
    "fc_loss_delta": 0.000806987500024503,
    "batt_loss_delta": -0.00019995417940765758,
    "guards": {
      "reference": "baseline",
      "max_fuel_increase_fraction": 0.05,
      "max_batt_increase_fraction": 0.1,
      "fuel_gkm_max": 11.831151575706585,
      "batt_loss_max": 0.0006330857144746793,
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
        "mean": 10.470735326416653,
        "std": 0.06920875871421209,
        "slope_per_10_episodes": 0.05447371625676252,
        "ep399_better_than_fraction": 0.125
      },
      "fc_loss": {
        "n": 40,
        "mean": 0.000919491449974627,
        "std": 9.786967129985749e-05,
        "slope_per_10_episodes": 7.075443151645662e-05,
        "ep399_better_than_fraction": 0.025
      },
      "batt_loss": {
        "n": 40,
        "mean": 0.00038004705603603974,
        "std": 5.374209481312856e-06,
        "slope_per_10_episodes": -3.3403194496898534e-06,
        "ep399_better_than_fraction": 0.825
      }
    },
    "lucky_checkpoint": false
  },
  "reward_diff": "--- parent:fd453666c825\n+++ candidate\n@@ -5,21 +5,34 @@\n     # -----------------------\n     # Charge-sustaining terms (must sum into soc_cost)\n     # -----------------------\n-    # term_soc_anchor (catalog: soc_anchor) — baseline symmetric quadratic anchor to SOC_target,\n-    # with 10x penalty only when outside SOC operating bounds.\n+\n+    # term_soc_anchor (catalog: soc_anchor)\n     soc_err = float(np.abs(soc - float(self.SOC_target))) ** 2\n     w_soc_eff = float(np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10.0, self.w_soc))\n     term_soc_anchor = w_soc_eff * soc_err\n \n-    # term_drift_barrier (catalog: drift_barrier) — quadratic barrier beyond a deadband around SOC_init.\n-    # Sized to materially penalize the measured persistent drift (+0.185) per-step (terminal-only is too discounted).\n-    d0 = 0.025  # deadband half-width (must be < soc_drift_abs_max=0.05)\n+    # term_drift_barrier (catalog: drift_barrier)\n+    d0 = 0.025  # deadband half-width (< soc_drift_abs_max = 0.05)\n     p = 2.0\n-    c_drift = 1100.0  # reward-units per (SOC^2)-step beyond deadband (sized to land ~6.8k–8k total on the baseline drifted rollout)\n+    c_drift = 1100.0\n     drift_excess = max(0.0, abs(soc - float(self.SOC_init)) - d0)\n     term_drift_barrier = c_drift * (drift_excess ** p)\n \n-    soc_cost = term_soc_anchor + term_drift_barrier\n+    # term_fc_surplus_charge (catalog: fc_surplus_charge)\n+    # Price FC power pushed into the battery while SOC is already high (measured drift mechanism).\n+    P_batt_w = float(self.P_batt)   # W, + = discharge, so charging => -P_batt_w > 0\n+    P_mot_w = float(self.P_mot)     # W, motor electrical power\n+    P_fc_to_batt_w = max(0.0, min(-P_batt_w, P_mot_w - P_batt_w))\n+    P_fc_to_batt_kw = P_fc_to_batt_w / 1000.0\n+\n+    # SOC gate g(SOC): 0 at/below SOC_target - m, ramps to 1 at SOC_target, nondecreasing above.\n+    m = 0.05\n+    soc_gate = max(0.0, (soc - (float(self.SOC_target) - m)) / m)\n+\n+    c_surplus = 4.0  # reward-units per (kW-step) of FC->battery charging when SOC is high\n+    term_fc_surplus_charge = c_surplus * soc_gate * P_fc_to_batt_kw\n+\n+    soc_cost = term_soc_anchor + term_drift_barrier + term_fc_surplus_charge\n \n     # -----------------------\n     # Price-aligned operating-cost proxy terms (unchanged structure)\n@@ -47,6 +60,7 @@\n         # catalog terms\n         'term_soc_anchor': float(term_soc_anchor),\n         'term_drift_barrier': float(term_drift_barrier),\n+        'term_fc_surplus_charge': float(term_fc_surplus_charge),\n \n         # aggregated costs\n         'soc_cost': float(soc_cost),\n"
}
```

[Training log](results/aroma_runs/seed41_obscur_20261016_033309_216122644/search/20261016_033309_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed41_obscur_seq_v3_catalog_iter6/trials/7cf8636d3ca53118bfbdd0c4/iter_001/train_log.log)
[Evaluation records](results/aroma_runs/seed41_obscur_20261016_033309_216122644/search/20261016_033309_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed41_obscur_seq_v3_catalog_iter6/trials/7cf8636d3ca53118bfbdd0c4/deterministic_evaluations.jsonl)
