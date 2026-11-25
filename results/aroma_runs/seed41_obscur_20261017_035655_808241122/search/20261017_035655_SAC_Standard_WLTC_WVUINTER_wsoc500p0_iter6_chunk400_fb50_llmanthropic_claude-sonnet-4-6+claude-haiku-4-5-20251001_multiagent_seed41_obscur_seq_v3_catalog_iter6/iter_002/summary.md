# Iteration 2

Decision: **replace_champion**

```json
{
  "iteration": 2,
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
    "iteration": 2
  },
  "edit_base": {
    "mode": "champion_improve",
    "parent_reward_id": "17afbf80420cb9f947efdaac72a30bf9687444a44fa8df43fcfaa7ace533d083",
    "selection_reason": "champion_improve: rank 1 of 1"
  },
  "candidate": {
    "candidate_id": "2227859ceab7dbd6470e274243887e8a5291d335e82f6d2a08d7617571558bcc",
    "seed": 41,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.773400960778153,
      "fc_loss": 0.00029100899995571083,
      "batt_loss": 0.00042869396245737157,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5604581866597159,
      "soc_max": 0.651545266891305
    },
    "operating_cost": {
      "h2_usd": 7.541380672544706,
      "fc_usd": 36.686680336726454,
      "batt_usd": 3.369586851908695,
      "degradation_usd": 40.05626718863515,
      "total_usd": 47.59764786117985,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.828017827923501,
      "soc_correction_gkm": -0.054616867145349586,
      "soc_final": 0.6281844517815487,
      "soc_final_minus_initial": 0.028184451781548714,
      "unaccepted_fc_kwh": 0.0,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.75324355403996,
      "fc_loss": 0.0003182189624583359,
      "batt_loss": 0.000437731559489693
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.6281844517815487,
      "soc_final_minus_initial": 0.028184451781548714,
      "soc_swing": 0.09108708023158907,
      "soc_mean": 0.6015273129161173,
      "fc_power_kw_mean": 9.976702165223287,
      "fc_abs_ramp_kw_s_mean": 1.7269604550052222,
      "fc_on_pct": 81.89479802383029,
      "fc_start_stop_count": 14,
      "fc_start_stop_soh_loss": 0.0002744,
      "fc_low_power_count": 1018,
      "fc_low_power_soh_loss": 3.562999999999999e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 22,
      "fc_load_change_soh_loss": 1.3046e-05,
      "battery_throughput_kwh": 3.940469096570876,
      "battery_ohmic_loss_kw_integral_kwh": 0.18808637811856926,
      "fc_low_output_pct": 47.108398721301945,
      "fc_regeneration_energy_kwh": 0.6077935329211606,
      "fc_energy_efficiency": 0.500807134374192
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
          "battery_ohmic_loss_kwh": 3.9771916332599524e-08,
          "soc_mean": 0.6298657198945017,
          "soc_delta": -0.00012361261240445565
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 95.06433395419275,
          "fc_energy_kwh": 1.4848158423134261,
          "fc_energy_efficiency": 0.4686187585754839,
          "fc_low_output_pct": 54.22437673130194,
          "battery_throughput_kwh": 0.6936949152437774,
          "battery_ohmic_loss_kwh": 0.013443415744968823,
          "soc_mean": 0.6125272182660784,
          "soc_delta": -0.0787171723396971
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 221.95262126443623,
          "fc_energy_kwh": 3.7047827450880213,
          "fc_energy_efficiency": 0.5008032668377066,
          "fc_low_output_pct": 49.95260663507109,
          "battery_throughput_kwh": 1.6864483497795977,
          "battery_ohmic_loss_kwh": 0.08413232400054195,
          "soc_mean": 0.6004545168085997,
          "soc_delta": -1.0379759693582655
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 45.50496997969865,
          "fc_energy_kwh": 0.6077935329211606,
          "fc_energy_efficiency": 0.4007392941633721,
          "fc_low_output_pct": 83.01329394387001,
          "battery_throughput_kwh": 1.6152160706208478,
          "battery_ohmic_loss_kwh": 0.09307058015419266,
          "soc_mean": 0.6106155207771972,
          "soc_delta": 0.9472072978981625
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 294.0461484334894,
          "fc_energy_kwh": 5.066147744229367,
          "fc_energy_efficiency": 0.5169244116948228,
          "fc_low_output_pct": 14.316702819956618,
          "battery_throughput_kwh": 0.5836054094768971,
          "battery_ohmic_loss_kwh": 0.016074656213339037,
          "soc_mean": 0.5797762321798149,
          "soc_delta": 0.04645564261021873
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
    "total_cost_delta_usd": -5.337706856050623,
    "cost_delta_usd": {
      "h2_usd": -0.34605371125968354,
      "fc_usd": -3.8374845770845027,
      "batt_usd": -1.1541685677064346
    },
    "soc_drift": 0.028184451781548714,
    "fuel_delta_gkm": -0.494362444656689,
    "fc_loss_delta": -3.0439999991083155e-05,
    "batt_loss_delta": -0.00014683850524688236,
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
        "mean": 10.75324355403996,
        "std": 0.032615479368502745,
        "slope_per_10_episodes": 0.018043031841374603,
        "ep399_better_than_fraction": 0.275
      },
      "fc_loss": {
        "n": 40,
        "mean": 0.0003182189624583359,
        "std": 3.601551778811657e-05,
        "slope_per_10_episodes": -2.52485220461707e-05,
        "ep399_better_than_fraction": 0.675
      },
      "batt_loss": {
        "n": 40,
        "mean": 0.000437731559489693,
        "std": 8.710219624406004e-06,
        "slope_per_10_episodes": 3.2975914852222618e-06,
        "ep399_better_than_fraction": 0.825
      }
    },
    "lucky_checkpoint": false
  },
  "reward_diff": "--- parent:17afbf80420c\n+++ candidate\n@@ -1,30 +1,78 @@\n def get_reward(self):\n     soc = float(self.SOC)\n+    soc_init = float(self.SOC_init)\n+    soc_target = float(self.SOC_target)\n     soc_low, soc_high = self.soc_bounds\n-    # SOC deviation from target\n-    soc_err = (np.abs(soc - self.SOC_target)) ** 2\n-    w_soc = np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10, self.w_soc)\n-    soc_cost = w_soc * soc_err\n \n-    h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal\n+    # --- Catalog term: soc_anchor (charge_sustaining, reshaped from edit_base) ---\n+    # Symmetric quadratic anchor: c_up = c_down = w_soc, p = 2, x10 outside bounds\n+    soc_err_sq = (soc - soc_target) ** 2\n+    w_soc_eff = np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10.0, self.w_soc)\n+    term_soc_anchor = float(w_soc_eff * soc_err_sq)\n+\n+    # --- Catalog term: drift_barrier (charge_sustaining, ADDED) ---\n+    # c * max(0, |SOC - SOC_init| - d0)^2, d0=0.025, c=2000\n+    # Flat inside +-0.025 of SOC_init, steep beyond; symmetric\n+    d0 = 0.025\n+    c_db = 2000.0\n+    soc_abs_drift = float(np.abs(soc - soc_init))\n+    drift_excess = float(np.maximum(0.0, soc_abs_drift - d0))\n+    term_drift_barrier = c_db * drift_excess ** 2\n+\n+    # --- Catalog term: fc_surplus_charge (charge_sustaining, ADDED) ---\n+    # c * g(SOC) * P_fc_to_batt_kw\n+    # g(SOC) = max(0, SOC - SOC_target + m) / m, m=0.05\n+    # P_fc_to_batt_kw = max(0, min(-P_batt, P_mot - P_batt)) / 1000\n+    # Zero while discharging, zero for pure regen, zero at SOC <= SOC_target - 0.05\n+    c_fsc = 0.20\n+    m_fsc = 0.05\n+    p_batt_w = float(self.P_batt)   # W, + = discharge\n+    p_mot_w = float(self.P_mot)     # W, motor electrical power\n+    # FC power into battery (kW): only when FC is charging battery (P_batt < 0 means charging)\n+    p_fc_to_batt_kw = float(np.maximum(0.0, np.minimum(-p_batt_w, p_mot_w - p_batt_w)) / 1000.0)\n+    g_soc = float(np.maximum(0.0, soc - soc_target + m_fsc) / m_fsc)\n+    term_fc_surplus_charge = c_fsc * g_soc * p_fc_to_batt_kw\n+\n+    # soc_cost = sum of all charge-sustaining terms (reshaped: now three terms)\n+    soc_cost = term_soc_anchor + term_drift_barrier + term_fc_surplus_charge\n+\n+    # --- Standard price terms ---\n+    h2_fcs = float(self.h2_fcs)\n+    h2_batt = float(self.h2_batt)\n+    h2_equal = float(self.h2_equal)\n     h2_cost = self.w_h2 * h2_fcs\n-    # Cost of fuel cell degradation (scaled)\n     fcs_soh_cost = self.w_fc * float(self.dSOH_FCS)\n-    # Cost of battery degradation (scaled)\n     batt_soh_cost = self.w_batt * float(self.dSOH_batt)\n \n+    # --- Catalog term: batt_ohmic (price, ADDED as extra_term) ---\n+    # c * P_batt_loss_kw; c=0.5 reward units per kW-step\n+    # Mean P_batt_loss_kw = 0.2907 kW -> mean extra cost = 0.145/step (non-zero, satisfies extra_terms: added)\n+    c_bo = 0.5\n+    p_batt_loss_kw = float(self.P_batt_loss_kw)\n+    term_batt_ohmic = c_bo * p_batt_loss_kw\n+\n     in_bounds = (soc_low < soc < soc_high)\n-    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost\n+\n+    # objective_cost includes soc_cost + price terms + extra batt_ohmic term\n+    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost + term_batt_ohmic\n+\n     reward = float(-objective_cost)\n \n-    self.info.update({'EMS_reward': reward,\n-                      'h2_fcs': float(h2_fcs),\n-                      'h2_batt': float(h2_batt),\n-                      'h2_equal': float(h2_equal),\n-                      'soc_cost': float(soc_cost),\n-                      'h2_cost': float(h2_cost),\n-                      'fcs_soh_cost': float(fcs_soh_cost),\n-                      'batt_soh_cost': float(batt_soh_cost),\n-                      'objective_cost': float(objective_cost),\n-                      'soc_in_bounds': int(in_bounds)})\n+    self.info.update({\n+        'EMS_reward': reward,\n+        'h2_fcs': float(h2_fcs),\n+        'h2_batt': float(h2_batt),\n+        'h2_equal': float(h2_equal),\n+        '"
}
```

[Training log](results/aroma_runs/seed41_obscur_20261017_035655_808241122/search/20261017_035655_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed41_obscur_seq_v3_catalog_iter6/trials/6bee131cb861a85ba8926eb3/iter_001/train_log.log)
[Evaluation records](results/aroma_runs/seed41_obscur_20261017_035655_808241122/search/20261017_035655_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed41_obscur_seq_v3_catalog_iter6/trials/6bee131cb861a85ba8926eb3/deterministic_evaluations.jsonl)
