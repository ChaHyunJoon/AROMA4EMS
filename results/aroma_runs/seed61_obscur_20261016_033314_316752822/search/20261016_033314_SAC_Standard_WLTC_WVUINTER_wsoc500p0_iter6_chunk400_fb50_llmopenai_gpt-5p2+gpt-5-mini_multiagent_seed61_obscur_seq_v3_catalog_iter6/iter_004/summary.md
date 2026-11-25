# Iteration 4

Decision: **retain_champion**

```json
{
  "iteration": 4,
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
    "iteration": 4
  },
  "edit_base": {
    "mode": "champion_improve",
    "parent_reward_id": "660d8570c3e73f9cad5db4fa94604dac4c8f923e414676d1760bf92a494ec0eb",
    "selection_reason": "champion_improve: rank 1 of 1 (no fresh guard_repair target)"
  },
  "candidate": {
    "candidate_id": "bb7ba3255901de0c1a41b812e203528b001741e2d0915b1721b91bf638b26fb9",
    "seed": 61,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.463364130309108,
      "fc_loss": 0.0015751849999776635,
      "batt_loss": 0.000391178978461193,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5849387876342297,
      "soc_max": 0.6835191734691287
    },
    "operating_cost": {
      "h2_usd": 7.324354891216375,
      "fc_usd": 198.57911121024406,
      "batt_usd": 3.0747145003167162,
      "degradation_usd": 201.6538257105608,
      "total_usd": 208.97818060177718,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.450861035674091,
      "soc_correction_gkm": 0.012503094635016065,
      "soc_final": 0.5935127890731586,
      "soc_final_minus_initial": -0.006487210926841347,
      "unaccepted_fc_kwh": 0.0,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.452945073149063,
      "fc_loss": 0.00147255504997727,
      "batt_loss": 0.00037299276697920215
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.5935127890731586,
      "soc_final_minus_initial": -0.006487210926841347,
      "soc_swing": 0.09858038583489903,
      "soc_mean": 0.6226488652051347,
      "fc_power_kw_mean": 9.821208718233521,
      "fc_abs_ramp_kw_s_mean": 1.4224932609267795,
      "fc_on_pct": 59.95350188898576,
      "fc_start_stop_count": 80,
      "fc_start_stop_soh_loss": 0.0015680000000000002,
      "fc_low_power_count": 528,
      "fc_low_power_soh_loss": 1.848e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 9,
      "fc_load_change_soh_loss": 5.337e-06,
      "battery_throughput_kwh": 3.570184521510123,
      "battery_ohmic_loss_kw_integral_kwh": 0.13926258656339335,
      "fc_low_output_pct": 25.748328974135426,
      "fc_regeneration_energy_kwh": 0.06095375202432862,
      "fc_energy_efficiency": 0.5035333048675544
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
          "battery_ohmic_loss_kwh": 3.942004429772863e-08,
          "soc_mean": 0.627735136054075,
          "soc_delta": -0.00012311045476121052
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 63.98459590944931,
          "fc_energy_kwh": 0.9041558473399606,
          "fc_energy_efficiency": 0.42396748425832476,
          "fc_low_output_pct": 42.313019390581715,
          "battery_throughput_kwh": 0.8164834027127181,
          "battery_ohmic_loss_kwh": 0.01881096717451204,
          "soc_mean": 0.6224437408249971,
          "soc_delta": -0.3822477105069203
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 264.48875501729555,
          "fc_energy_kwh": 4.436858438513321,
          "fc_energy_efficiency": 0.5033070878692021,
          "fc_low_output_pct": 29.00473933649289,
          "battery_throughput_kwh": 1.4881383173930038,
          "battery_ohmic_loss_kwh": 0.05736644343547847,
          "soc_mean": 0.6175672922942752,
          "soc_delta": -0.5896021050774402
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 5.73632220823801,
          "fc_energy_kwh": 0.06095375202432862,
          "fc_energy_efficiency": 0.3188097484565159,
          "fc_low_output_pct": 10.635155096011816,
          "battery_throughput_kwh": 1.1920717382543948,
          "battery_ohmic_loss_kwh": 0.0643685982020403,
          "soc_mean": 0.6217727183414508,
          "soc_delta": 0.7000430408277143
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 300.3576168102078,
          "fc_energy_kwh": 5.148305366097883,
          "fc_energy_efficiency": 0.5142689873627714,
          "fc_low_output_pct": 14.316702819956618,
          "battery_throughput_kwh": 0.7254945447622706,
          "battery_ohmic_loss_kwh": 0.016536912976613565,
          "soc_mean": 0.6338631885886485,
          "soc_delta": 0.10146672489462039
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
    "total_cost_delta_usd": 143.89700170577402,
    "cost_delta_usd": {
      "h2_usd": -0.17945303832064763,
      "fc_usd": 144.66730647612368,
      "batt_usd": -0.5908517320290332
    },
    "soc_drift": -0.006487210926841347,
    "fuel_delta_gkm": -0.25636148331521014,
    "fc_loss_delta": 0.0011475415000075095,
    "batt_loss_delta": -7.517080917052166e-05,
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
    "total_cost_delta_usd_vs_baseline": 135.8153465782201,
    "fuel_delta_gkm_vs_baseline": 0.09468466412049104,
    "fc_loss_delta_vs_baseline": 0.0010822159999922532,
    "batt_loss_delta_vs_baseline": -8.687376736837837e-05
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
        "mean": 10.452945073149063,
        "std": 0.04184034804082018,
        "slope_per_10_episodes": 0.010204674397930227,
        "ep399_better_than_fraction": 0.3
      },
      "fc_loss": {
        "n": 40,
        "mean": 0.00147255504997727,
        "std": 0.00017826687971966246,
        "slope_per_10_episodes": 0.00011095525140630578,
        "ep399_better_than_fraction": 0.25
      },
      "batt_loss": {
        "n": 40,
        "mean": 0.00037299276697920215,
        "std": 1.4135014542990523e-05,
        "slope_per_10_episodes": 6.338277956414971e-08,
        "ep399_better_than_fraction": 0.05
      }
    },
    "lucky_checkpoint": false
  },
  "reward_diff": "--- parent:660d8570c3e7\n+++ candidate\n@@ -1,33 +1,41 @@\n def get_reward(self):\n     soc = float(self.SOC)\n+    soc_t = float(self.SOC_target)\n+    soc_i = float(self.SOC_init)\n     soc_low, soc_high = self.soc_bounds\n \n     # -------------------------\n     # Charge-sustaining terms (CATALOG)\n+    # soc_cost MUST equal the sum of the logged catalog terms.\n     # -------------------------\n-    # (1) soc_anchor (existing, but scaled per orchestrator term_ratio soc_cost = 7.0)\n-    soc_err = (np.abs(soc - float(self.SOC_target))) ** 2\n-    w_soc = np.where((soc >= soc_high) | (soc <= soc_low), float(self.w_soc) * 10.0, float(self.w_soc))\n+    # (1) soc_anchor (existing, orchestrator-required soc_cost ratio change kept: x7)\n+    soc_err = (np.abs(soc - soc_t)) ** 2\n+    w_soc = np.where((soc >= float(soc_high)) | (soc <= float(soc_low)),\n+                     float(self.w_soc) * 10.0,\n+                     float(self.w_soc))\n     term_soc_anchor_base = float(w_soc * soc_err)\n-    term_soc_anchor = 7.0 * term_soc_anchor_base  # orchestrator-required ratio\n+    term_soc_anchor = 7.0 * term_soc_anchor_base\n \n-    # (2) fc_surplus_charge (NEW catalog term per orchestrator)\n+    # (2) fc_surplus_charge (existing in edit_base; kept)\n     # FC power into the battery: max(0, min(-P_batt, P_mot - P_batt)) / 1000 [kW]\n-    P_batt_w = float(self.P_batt)   # + = discharge, - = charge\n+    P_batt_w = float(self.P_batt)  # + = discharge, - = charge\n     P_mot_w = float(self.P_mot)\n     P_fc_to_batt_w = max(0.0, min(-P_batt_w, P_mot_w - P_batt_w))\n     P_fc_to_batt_kw = P_fc_to_batt_w / 1000.0\n \n-    # g(SOC): 0 at/below (SOC_target - m), linear ramp to 1 at SOC_target, nondecreasing above\n-    m = 0.05\n-    g_soc = max(0.0, soc - float(self.SOC_target) + m) / m\n-\n-    # Small coefficient so soc_cost ratio stays ~7x on the baseline replay (orchestrator conformance),\n-    # while still providing a directional disincentive to FC->battery charging at high SOC.\n-    c_surplus = 0.005  # reward-units per (kW-step) times g(SOC)\n+    m = 0.05  # SOC ramp width\n+    g_soc = max(0.0, soc - soc_t + m) / m  # nondecreasing, 0 at/below soc_t-m\n+    c_surplus = 0.005\n     term_fc_surplus_charge = float(c_surplus * g_soc * P_fc_to_batt_kw)\n \n-    soc_cost = term_soc_anchor + term_fc_surplus_charge\n+    # (3) drift_barrier (NEW catalog term; required change_spec)\n+    # Price sustained offset from SOC_init beyond a deadband so drift is corrected per-step.\n+    d0 = 0.03  # deadband (< soc_drift_abs_max=0.05)\n+    drift_excess = max(0.0, abs(soc - soc_i) - d0)\n+    c_drift = 2.0e5  # sized from DRIFT FACTS geometric-mean guidance\n+    term_drift_barrier = float(c_drift * (drift_excess ** 2.0))\n+\n+    soc_cost = float(term_soc_anchor + term_fc_surplus_charge + term_drift_barrier)\n \n     # -------------------------\n     # Price / wear terms (unchanged per orchestrator)\n@@ -40,9 +48,9 @@\n     fcs_soh_cost = float(self.w_fc) * float(self.dSOH_FCS)\n     batt_soh_cost = float(self.w_batt) * float(self.dSOH_batt)\n \n-    in_bounds = (soc_low < soc < soc_high)\n+    in_bounds = (float(soc_low) < soc < float(soc_high))\n \n-    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost\n+    objective_cost = float(soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost)\n     reward = float(-objective_cost)\n \n     # -------------------------\n@@ -57,6 +65,7 @@\n         # Catalog term logs (plain values used in soc_cost sum)\n         'term_soc_anchor': float(term_soc_anchor),\n         'term_fc_surplus_charge': float(term_fc_surplus_charge),\n+        'term_drift_barrier': float(term_drift_barrier),\n \n         'soc_cost': float(soc_cost),\n         'h2_cost': float(h2_cost),\n"
}
```

[Training log](results/aroma_runs/seed61_obscur_20261016_033314_316752822/search/20261016_033314_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed61_obscur_seq_v3_catalog_iter6/trials/172de1a690afa78b3aba3821/iter_001/train_log.log)
[Evaluation records](results/aroma_runs/seed61_obscur_20261016_033314_316752822/search/20261016_033314_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed61_obscur_seq_v3_catalog_iter6/trials/172de1a690afa78b3aba3821/deterministic_evaluations.jsonl)
