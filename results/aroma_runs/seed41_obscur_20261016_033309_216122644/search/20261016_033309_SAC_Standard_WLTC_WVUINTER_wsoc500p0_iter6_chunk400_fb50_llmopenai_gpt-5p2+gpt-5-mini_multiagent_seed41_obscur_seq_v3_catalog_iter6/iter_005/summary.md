# Iteration 5

Decision: **replace_champion**

```json
{
  "iteration": 5,
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
  "decision": "replace_champion",
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
    "candidate_id": "59716618abe00b79a7d6c2b4128d01833745357099ab208a400a9c9d1edbcd57",
    "seed": 41,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.837797361445341,
      "fc_loss": 0.00024280549995714384,
      "batt_loss": 0.00048721737274892707,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5476980802053689,
      "soc_max": 0.6493744396752982
    },
    "operating_cost": {
      "h2_usd": 7.58645815301174,
      "fc_usd": 30.60980162909899,
      "batt_usd": 3.829587997520566,
      "degradation_usd": 34.43938962661956,
      "total_usd": 42.02584777963129,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.91887871612674,
      "soc_correction_gkm": -0.08108135468139797,
      "soc_final": 0.6418230322902729,
      "soc_final_minus_initial": 0.041823032290272955,
      "unaccepted_fc_kwh": 0.0,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.818152987600552,
      "fc_loss": 0.00027410996245862964,
      "batt_loss": 0.0004741305584225225
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.6418230322902729,
      "soc_final_minus_initial": 0.041823032290272955,
      "soc_swing": 0.10167635946992926,
      "soc_mean": 0.6080463047547254,
      "fc_power_kw_mean": 10.05108164454542,
      "fc_abs_ramp_kw_s_mean": 1.8285076843239336,
      "fc_on_pct": 82.44696309212438,
      "fc_start_stop_count": 12,
      "fc_start_stop_soh_loss": 0.0002352,
      "fc_low_power_count": 987,
      "fc_low_power_soh_loss": 3.4544999999999997e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 7,
      "fc_load_change_soh_loss": 4.151e-06,
      "battery_throughput_kwh": 4.470172730611841,
      "battery_ohmic_loss_kw_integral_kwh": 0.2263781330059456,
      "fc_low_output_pct": 48.41615809357745,
      "fc_regeneration_energy_kwh": 0.652391434500671,
      "fc_energy_efficiency": 0.5005900598038818
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
          "battery_ohmic_loss_kwh": 3.9780363185302575e-08,
          "soc_mean": 0.6379038605342554,
          "soc_delta": -0.00012361143169081767
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 96.65461975920721,
          "fc_energy_kwh": 1.5331694666407005,
          "fc_energy_efficiency": 0.47591811009360374,
          "fc_low_output_pct": 53.18559556786704,
          "battery_throughput_kwh": 0.6993655111971177,
          "battery_ohmic_loss_kwh": 0.014794028587244002,
          "soc_mean": 0.6202515816109084,
          "soc_delta": -0.05082009225901429
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 217.64247170644896,
          "fc_energy_kwh": 3.7021955137783435,
          "fc_energy_efficiency": 0.5103644166497032,
          "fc_low_output_pct": 46.161137440758296,
          "battery_throughput_kwh": 1.7952258894559534,
          "battery_ohmic_loss_kwh": 0.10717263201165901,
          "soc_mean": 0.6065019478513133,
          "soc_delta": -1.052317282379726
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 49.449233874204204,
          "fc_energy_kwh": 0.652391434500671,
          "fc_energy_efficiency": 0.39583425002811823,
          "fc_low_output_pct": 89.36484490398819,
          "battery_throughput_kwh": 1.6492933280917972,
          "battery_ohmic_loss_kwh": 0.09617276203144476,
          "soc_mean": 0.616807425717925,
          "soc_delta": 0.9656361499998372
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 296.8675724602689,
          "fc_energy_kwh": 5.1066881899445935,
          "fc_energy_efficiency": 0.5161088024040513,
          "fc_low_output_pct": 15.075921908893708,
          "battery_throughput_kwh": 1.0759291523020413,
          "battery_ohmic_loss_kwh": 0.03523600633013308,
          "soc_mean": 0.584077352538944,
          "soc_delta": 0.05673430948255598
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
    "total_cost_delta_usd": -10.909506937599183,
    "cost_delta_usd": {
      "h2_usd": -0.30097623079265023,
      "fc_usd": -9.914363284711968,
      "batt_usd": -0.694167422094564
    },
    "soc_drift": 0.041823032290272955,
    "fuel_delta_gkm": -0.42996604398950033,
    "fc_loss_delta": -7.864349998965015e-05,
    "batt_loss_delta": -8.831509495532686e-05,
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
        "mean": 10.818152987600552,
        "std": 0.02402578036420742,
        "slope_per_10_episodes": 0.012865998521584376,
        "ep399_better_than_fraction": 0.15
      },
      "fc_loss": {
        "n": 40,
        "mean": 0.00027410996245862964,
        "std": 2.1127958826694e-05,
        "slope_per_10_episodes": -7.852392197968608e-08,
        "ep399_better_than_fraction": 0.875
      },
      "batt_loss": {
        "n": 40,
        "mean": 0.0004741305584225225,
        "std": 1.1952140383868274e-05,
        "slope_per_10_episodes": 6.660034431980315e-06,
        "ep399_better_than_fraction": 0.15
      }
    },
    "lucky_checkpoint": false
  },
  "reward_diff": "--- parent:17afbf80420c\n+++ candidate\n@@ -1,30 +1,70 @@\n def get_reward(self):\n     soc = float(self.SOC)\n     soc_low, soc_high = self.soc_bounds\n-    # SOC deviation from target\n-    soc_err = (np.abs(soc - self.SOC_target)) ** 2\n-    w_soc = np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10, self.w_soc)\n-    soc_cost = w_soc * soc_err\n \n+    # -----------------------\n+    # Charge-sustaining terms (must sum exactly into soc_cost)\n+    # -----------------------\n+\n+    # term_soc_anchor (catalog: soc_anchor) — baseline symmetric quadratic anchor to SOC_target,\n+    # with 10x penalty only when outside SOC operating bounds.\n+    soc_err = float(np.abs(soc - float(self.SOC_target))) ** 2\n+    w_soc_eff = float(np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10.0, self.w_soc))\n+    term_soc_anchor = w_soc_eff * soc_err\n+\n+    # term_drift_barrier (catalog: drift_barrier) — quadratic barrier beyond a deadband around SOC_init.\n+    # Asymmetric: penalize over-charge drift (SOC above SOC_init) more than depletion drift, matching the\n+    # measured failure mode (+SOC drift).\n+    d0 = 0.02  # deadband half-width (< soc_drift_abs_max = 0.05)\n+    p = 2.0\n+\n+    soc_init = float(self.SOC_init)\n+    drift_up_excess = max(0.0, (soc - soc_init) - d0)\n+    drift_down_excess = max(0.0, (soc_init - soc) - d0)\n+\n+    c_up = 1600.0   # reward-units per (SOC^2)-step beyond deadband (overcharge side)\n+    c_down = 900.0  # reward-units per (SOC^2)-step beyond deadband (depletion side)\n+    term_drift_barrier = c_up * (drift_up_excess ** p) + c_down * (drift_down_excess ** p)\n+\n+    soc_cost = term_soc_anchor + term_drift_barrier\n+\n+    # -----------------------\n+    # Price-aligned operating-cost proxy terms (unchanged structure/weights)\n+    # -----------------------\n     h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal\n-    h2_cost = self.w_h2 * h2_fcs\n+    h2_cost = float(self.w_h2) * float(h2_fcs)\n+\n     # Cost of fuel cell degradation (scaled)\n-    fcs_soh_cost = self.w_fc * float(self.dSOH_FCS)\n+    fcs_soh_cost = float(self.w_fc) * float(self.dSOH_FCS)\n+\n     # Cost of battery degradation (scaled)\n-    batt_soh_cost = self.w_batt * float(self.dSOH_batt)\n+    batt_soh_cost = float(self.w_batt) * float(self.dSOH_batt)\n \n     in_bounds = (soc_low < soc < soc_high)\n+\n     objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost\n     reward = float(-objective_cost)\n \n-    self.info.update({'EMS_reward': reward,\n-                      'h2_fcs': float(h2_fcs),\n-                      'h2_batt': float(h2_batt),\n-                      'h2_equal': float(h2_equal),\n-                      'soc_cost': float(soc_cost),\n-                      'h2_cost': float(h2_cost),\n-                      'fcs_soh_cost': float(fcs_soh_cost),\n-                      'batt_soh_cost': float(batt_soh_cost),\n-                      'objective_cost': float(objective_cost),\n-                      'soc_in_bounds': int(in_bounds)})\n+    # -----------------------\n+    # Required logging (log every catalog term as term_<id>)\n+    # -----------------------\n+    self.info.update({\n+        'EMS_reward': reward,\n+        'h2_fcs': float(h2_fcs),\n+        'h2_batt': float(h2_batt),\n+        'h2_equal': float(h2_equal),\n+\n+        # catalog terms\n+        'term_soc_anchor': float(term_soc_anchor),\n+        'term_drift_barrier': float(term_drift_barrier),\n+\n+        # aggregated costs\n+        'soc_cost': float(soc_cost),\n+        'h2_cost': float(h2_cost),\n+        'fcs_soh_cost': float(fcs_soh_cost),\n+        'batt_soh_cost': float(batt_soh_cost),\n+        'objective_cost': float(objective_cost),\n+\n+        'soc_in_bounds': int(in_bounds),\n+    })\n     return reward\n"
}
```

[Training log](results/aroma_runs/seed41_obscur_20261016_033309_216122644/search/20261016_033309_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed41_obscur_seq_v3_catalog_iter6/trials/357a0010ebb1cb54c7173bfe/iter_001/train_log.log)
[Evaluation records](results/aroma_runs/seed41_obscur_20261016_033309_216122644/search/20261016_033309_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed41_obscur_seq_v3_catalog_iter6/trials/357a0010ebb1cb54c7173bfe/deterministic_evaluations.jsonl)
