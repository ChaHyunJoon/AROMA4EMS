# Iteration 3

Decision: **retain_champion**

```json
{
  "iteration": 3,
  "control": {
    "candidate_id": "660d8570c3e73f9cad5db4fa94604dac4c8f923e414676d1760bf92a494ec0eb",
    "seed": 61,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.719725613624318,
      "fc_loss": 0.00042764349997015394,
      "batt_loss": 0.00046634978763171464,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5644004883918264,
      "soc_max": 0.6509156081956919
    },
    "operating_cost": {
      "h2_usd": 7.503807929537023,
      "fc_usd": 53.91180473412037,
      "batt_usd": 3.6655662323457494,
      "degradation_usd": 57.57737096646612,
      "total_usd": 65.08117889600315,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.755483454503839,
      "soc_correction_gkm": -0.03575784087952028,
      "soc_final": 0.6185507818845699,
      "soc_final_minus_initial": 0.018550781884569933,
      "unaccepted_fc_kwh": 0.0,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.683347944895221,
      "fc_loss": 0.000492779724972256,
      "batt_loss": 0.00046153909333486454
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.6185507818845699,
      "soc_final_minus_initial": 0.018550781884569933,
      "soc_swing": 0.0865151198038655,
      "soc_mean": 0.6016795905189263,
      "fc_power_kw_mean": 9.98928444830163,
      "fc_abs_ramp_kw_s_mean": 1.6115215776497624,
      "fc_on_pct": 77.56466143562918,
      "fc_start_stop_count": 21,
      "fc_start_stop_soh_loss": 0.0004116,
      "fc_low_power_count": 687,
      "fc_low_power_soh_loss": 2.4044999999999996e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 23,
      "fc_load_change_soh_loss": 1.3639e-05,
      "battery_throughput_kwh": 4.272321186513147,
      "battery_ohmic_loss_kw_integral_kwh": 0.21537159137530928,
      "fc_low_output_pct": 45.62627143272305,
      "fc_regeneration_energy_kwh": 0.6089686670509872,
      "fc_energy_efficiency": 0.5034758365358409
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
          "battery_ohmic_loss_kwh": 3.9792224430251995e-08,
          "soc_mean": 0.6260006640881809,
          "soc_delta": -0.00012365057455809847
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 85.91449135277946,
          "fc_energy_kwh": 1.3719279989877704,
          "fc_energy_efficiency": 0.4791037637205075,
          "fc_low_output_pct": 51.73130193905817,
          "battery_throughput_kwh": 0.6879104914230655,
          "battery_ohmic_loss_kwh": 0.0137142471706455,
          "soc_mean": 0.6108007238841999,
          "soc_delta": -0.135522150759938
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 220.7509003188294,
          "fc_energy_kwh": 3.7030563956373315,
          "fc_energy_efficiency": 0.5032948993135234,
          "fc_low_output_pct": 47.67772511848341,
          "battery_throughput_kwh": 1.8563805098554955,
          "battery_ohmic_loss_kwh": 0.10745273594818933,
          "soc_mean": 0.5990634260968984,
          "soc_delta": -1.0462846653461197
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 43.54425747709631,
          "fc_energy_kwh": 0.6089686670509872,
          "fc_energy_efficiency": 0.41959349312248306,
          "fc_low_output_pct": 75.03692762186115,
          "battery_throughput_kwh": 1.6227295384536407,
          "battery_ohmic_loss_kwh": 0.09279467542037378,
          "soc_mean": 0.6094983051564076,
          "soc_delta": 0.9522884473072317
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 295.16346209426956,
          "fc_energy_kwh": 5.082761505787584,
          "fc_energy_efficiency": 0.5166564109971744,
          "fc_low_output_pct": 14.20824295010846,
          "battery_throughput_kwh": 0.7732138760899185,
          "battery_ohmic_loss_kwh": 0.020982459703649987,
          "soc_mean": 0.5863214547616523,
          "soc_delta": 0.05418995679254823
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
    "parent_reward_id": "17afbf80420cb9f947efdaac72a30bf9687444a44fa8df43fcfaa7ace533d083",
    "selection_reason": "fuel_leader: rank 1 of 2"
  },
  "candidate": {
    "candidate_id": "f75cd9a11d016f0ed928054e2f156783e58e50db17cf0a1a71ef859e5d92ac48",
    "seed": 61,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.24202396144441,
      "fc_loss": 0.0010790744999871205,
      "batt_loss": 0.00038181256555258614,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5662886862896508,
      "soc_max": 0.6541638687334753
    },
    "operating_cost": {
      "h2_usd": 7.169416773011088,
      "fc_usd": 136.03586571743602,
      "batt_usd": 3.001093352014382,
      "degradation_usd": 139.0369590694504,
      "total_usd": 146.20637584246148,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.271525940849278,
      "soc_correction_gkm": -0.029501979404867318,
      "soc_final": 0.6157618517814901,
      "soc_final_minus_initial": 0.015761851781490144,
      "unaccepted_fc_kwh": 0.0,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.3045110376659,
      "fc_loss": 0.001153278287485754,
      "batt_loss": 0.0004146952287387651
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.6157618517814901,
      "soc_final_minus_initial": 0.015761851781490144,
      "soc_swing": 0.08787518244382453,
      "soc_mean": 0.6104988846246244,
      "fc_power_kw_mean": 9.85285875875294,
      "fc_abs_ramp_kw_s_mean": 1.1634015259506512,
      "fc_on_pct": 64.05114792211566,
      "fc_start_stop_count": 55,
      "fc_start_stop_soh_loss": 0.001078,
      "fc_low_power_count": 307,
      "fc_low_power_soh_loss": 1.0745e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 0,
      "fc_load_change_soh_loss": 0.0,
      "battery_throughput_kwh": 3.4216104154633165,
      "battery_ohmic_loss_kw_integral_kwh": 0.14993728064087467,
      "fc_low_output_pct": 25.719267654751526,
      "fc_regeneration_energy_kwh": 0.21979095893743597,
      "fc_energy_efficiency": 0.5184940586723052
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
          "battery_ohmic_loss_kwh": 3.9742926436135574e-08,
          "soc_mean": 0.6305438535441991,
          "soc_delta": -0.00012357424840891973
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 85.71782957568045,
          "fc_energy_kwh": 1.4858887530763691,
          "fc_energy_efficiency": 0.5200915716723876,
          "fc_low_output_pct": 36.21883656509695,
          "battery_throughput_kwh": 0.7212921803673933,
          "battery_ohmic_loss_kwh": 0.01488572746173917,
          "soc_mean": 0.6188199133468695,
          "soc_delta": -0.05989385008949133
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 233.0936065261315,
          "fc_energy_kwh": 4.0159594873319,
          "fc_energy_efficiency": 0.516920371601095,
          "fc_low_output_pct": 20.85308056872038,
          "battery_throughput_kwh": 1.4334270486680705,
          "battery_ohmic_loss_kwh": 0.06851654435328683,
          "soc_mean": 0.6099072880008467,
          "soc_delta": -0.8410051020206718
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 16.93160803858734,
          "fc_energy_kwh": 0.21979095893743597,
          "fc_energy_efficiency": 0.38947205675415375,
          "fc_low_output_pct": 29.68980797636632,
          "battery_throughput_kwh": 1.316553978098774,
          "battery_ohmic_loss_kwh": 0.07098765995340804,
          "soc_mean": 0.6194482468903487,
          "soc_delta": 0.773800017227753
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 291.2393096235431,
          "fc_energy_kwh": 5.044658835381473,
          "fc_energy_efficiency": 0.5196925536842579,
          "fc_low_output_pct": 12.79826464208243,
          "battery_throughput_kwh": 0.5812089622476205,
          "battery_ohmic_loss_kwh": 0.013476764953637919,
          "soc_mean": 0.5902253328960715,
          "soc_delta": 0.0369230193800808
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
    "total_cost_delta_usd": 81.12519694645833,
    "cost_delta_usd": {
      "h2_usd": -0.33439115652593454,
      "fc_usd": 82.12406098331564,
      "batt_usd": -0.6644728803313673
    },
    "soc_drift": 0.015761851781490144,
    "fuel_delta_gkm": -0.477701652179908,
    "fc_loss_delta": 0.0006514310000169665,
    "batt_loss_delta": -8.45372220791285e-05,
    "guards": {
      "reference": "baseline",
      "max_fuel_increase_fraction": 0.05,
      "max_batt_increase_fraction": 0.1,
      "fuel_gkm_max": 10.887113439498048,
      "batt_loss_max": 0.0005258580204125286,
      "soc_drift_abs_max": 0.05
    },
    "guard_reference": "baseline",
    "comparison_basis": "matched_fresh_training",
    "total_cost_delta_usd_vs_baseline": 73.0435418189044,
    "fuel_delta_gkm_vs_baseline": -0.12665550474420684,
    "fc_loss_delta_vs_baseline": 0.0005861055000017101,
    "batt_loss_delta_vs_baseline": -9.624018027698522e-05
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
        "mean": 10.3045110376659,
        "std": 0.05218415403614901,
        "slope_per_10_episodes": -0.03042340212511567,
        "ep399_better_than_fraction": 0.925
      },
      "fc_loss": {
        "n": 40,
        "mean": 0.001153278287485754,
        "std": 0.00010790484524235244,
        "slope_per_10_episodes": 1.4744339118595259e-05,
        "ep399_better_than_fraction": 0.7
      },
      "batt_loss": {
        "n": 40,
        "mean": 0.0004146952287387651,
        "std": 2.379068099316865e-05,
        "slope_per_10_episodes": -1.5053710704218066e-05,
        "ep399_better_than_fraction": 0.875
      }
    },
    "lucky_checkpoint": true
  },
  "reward_diff": "--- parent:17afbf80420c\n+++ candidate\n@@ -1,30 +1,79 @@\n def get_reward(self):\n     soc = float(self.SOC)\n+    soc_t = float(self.SOC_target)\n+    soc_i = float(self.SOC_init)\n     soc_low, soc_high = self.soc_bounds\n-    # SOC deviation from target\n-    soc_err = (np.abs(soc - self.SOC_target)) ** 2\n-    w_soc = np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10, self.w_soc)\n-    soc_cost = w_soc * soc_err\n \n-    h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal\n-    h2_cost = self.w_h2 * h2_fcs\n-    # Cost of fuel cell degradation (scaled)\n-    fcs_soh_cost = self.w_fc * float(self.dSOH_FCS)\n-    # Cost of battery degradation (scaled)\n-    batt_soh_cost = self.w_batt * float(self.dSOH_batt)\n+    # -------------------------\n+    # Charge-sustaining terms (CATALOG): soc_anchor + drift_barrier\n+    # soc_cost MUST equal the sum of the logged catalog terms.\n+    # -------------------------\n \n-    in_bounds = (soc_low < soc < soc_high)\n+    # (1) soc_anchor (RESHAPED): asymmetric quadratic anchor\n+    # Penalize SOC deficit (below target) more than surplus to discourage deep discharge\n+    # that tends to lead to longer FC-off periods and then costly restarts.\n+    p = 2.0\n+    c_up = float(self.w_soc) * 0.75    # SOC above target (surplus) price\n+    c_down = float(self.w_soc) * 2.25  # SOC below target (deficit) price (stronger)\n+\n+    soc_above = max(0.0, soc - soc_t)\n+    soc_below = max(0.0, soc_t - soc)\n+\n+    term_soc_anchor = c_up * (soc_above ** p) + c_down * (soc_below ** p)\n+\n+    # Optional multiplier outside SOC operating bounds (baseline behavior k=10)\n+    if (soc >= float(soc_high)) or (soc <= float(soc_low)):\n+        term_soc_anchor *= 10.0\n+\n+    # (2) drift_barrier (ADDED): flat near SOC_init, steep beyond a deadband\n+    # This makes sustained drift expensive per-step (not terminal-only),\n+    # preventing the learned \"FC idles into battery\" drift mode from being attractive.\n+    d0 = 0.03  # deadband (< soc_drift_abs_max=0.05)\n+    drift = abs(soc - soc_i)\n+    drift_excess = max(0.0, drift - d0)\n+\n+    # Sized to be a meaningful lever on the baseline rollout over the 1191 steps with |drift|>0.025:\n+    # if typical drift_excess ~ O(0.01), then per-step term ~ c_drift * 1e-4;\n+    # with c_drift=1e5 this is ~10 per step, or ~1.2e4 over 1191 steps (inside the stated 2.0e3..5.0e4 range).\n+    c_drift = 1.0e5\n+    term_drift_barrier = c_drift * (drift_excess ** 2.0)\n+\n+    soc_cost = float(term_soc_anchor + term_drift_barrier)\n+\n+    # -------------------------\n+    # Price / wear terms (unchanged)\n+    # -------------------------\n+    h2_fcs = float(self.h2_fcs)\n+    h2_batt = float(self.h2_batt)\n+    h2_equal = float(self.h2_equal)\n+\n+    h2_cost = float(self.w_h2) * h2_fcs\n+    fcs_soh_cost = float(self.w_fc) * float(self.dSOH_FCS)\n+    batt_soh_cost = float(self.w_batt) * float(self.dSOH_batt)\n+\n+    in_bounds = (float(soc_low) < soc < float(soc_high))\n+\n     objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost\n     reward = float(-objective_cost)\n \n-    self.info.update({'EMS_reward': reward,\n-                      'h2_fcs': float(h2_fcs),\n-                      'h2_batt': float(h2_batt),\n-                      'h2_equal': float(h2_equal),\n-                      'soc_cost': float(soc_cost),\n-                      'h2_cost': float(h2_cost),\n-                      'fcs_soh_cost': float(fcs_soh_cost),\n-                      'batt_soh_cost': float(batt_soh_cost),\n-                      'objective_cost': float(objective_cost),\n-                      'soc_in_bounds': int(in_bounds)})\n+    # -------------------------\n+    # Logging (required + every catalog term as self.info['term_<id>'])\n+    # -------------------------\n+    self.info.update({\n+        'EMS_reward': reward,\n+        'h2_fcs': h2_fcs,\n+        'h2_batt': h2_batt,\n+        'h2_equal': h2_equal,\n+\n+        # Catalog term logs (plain values used in soc_cost sum)\n+        'term_soc_anchor': float(term_soc_"
}
```

[Training log](results/aroma_runs/seed61_obscur_20261016_033314_316752822/search/20261016_033314_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed61_obscur_seq_v3_catalog_iter6/trials/6d07652b282241a098a9269c/iter_001/train_log.log)
[Evaluation records](results/aroma_runs/seed61_obscur_20261016_033314_316752822/search/20261016_033314_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed61_obscur_seq_v3_catalog_iter6/trials/6d07652b282241a098a9269c/deterministic_evaluations.jsonl)
