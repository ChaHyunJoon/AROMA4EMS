# Iteration 5

Decision: **retain_champion**

```json
{
  "iteration": 5,
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
    "iteration": 5
  },
  "edit_base": {
    "mode": "champion_improve",
    "parent_reward_id": "17afbf80420cb9f947efdaac72a30bf9687444a44fa8df43fcfaa7ace533d083",
    "selection_reason": "champion_improve: rank 1 of 1"
  },
  "candidate": {
    "candidate_id": "8a3dd1ba83610292c03f90510bc3819b7f0c51f985e5c191eee128a8381f1e19",
    "seed": 61,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.268683146551933,
      "fc_loss": 0.0007492609999890654,
      "batt_loss": 0.0004224572740161303,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5549580642666273,
      "soc_max": 0.646129311209192
    },
    "operating_cost": {
      "h2_usd": 7.188078202586352,
      "fc_usd": 94.457211974744,
      "batt_usd": 3.3205657197924543,
      "degradation_usd": 97.77777769453645,
      "total_usd": 104.96585589712281,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.250300125859637,
      "soc_correction_gkm": 0.01838302069229586,
      "soc_final": 0.590151870925712,
      "soc_final_minus_initial": -0.009848129074288003,
      "unaccepted_fc_kwh": 0.0014412334320013504,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.315233190600555,
      "fc_loss": 0.0007159962249883495,
      "batt_loss": 0.00044009632942712263
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.590151870925712,
      "soc_final_minus_initial": -0.009848129074288003,
      "soc_swing": 0.09117124694256473,
      "soc_mean": 0.5964221201299391,
      "fc_power_kw_mean": 9.837075737047526,
      "fc_abs_ramp_kw_s_mean": 1.140613536918144,
      "fc_on_pct": 67.13164777680906,
      "fc_start_stop_count": 38,
      "fc_start_stop_soh_loss": 0.0007448,
      "fc_low_power_count": 258,
      "fc_low_power_soh_loss": 9.03e-07,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 6,
      "fc_load_change_soh_loss": 3.5580000000000005e-06,
      "battery_throughput_kwh": 3.8044772566771594,
      "battery_ohmic_loss_kw_integral_kwh": 0.18031041413945553,
      "fc_low_output_pct": 33.420517291485034,
      "fc_regeneration_energy_kwh": 0.4394730198181196,
      "fc_energy_efficiency": 0.519905673214584
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
          "battery_ohmic_loss_kwh": 3.9850368347883056e-08,
          "soc_mean": 0.6160757939250443,
          "soc_delta": -0.00012374739987097705
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 79.98159552495963,
          "fc_energy_kwh": 1.4020064144218873,
          "fc_energy_efficiency": 0.5259259783010575,
          "fc_low_output_pct": 39.26592797783934,
          "battery_throughput_kwh": 0.684976990203705,
          "battery_ohmic_loss_kwh": 0.01304349382565804,
          "soc_mean": 0.6050006278969544,
          "soc_delta": -0.10486589474023289
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 222.00044329974966,
          "fc_energy_kwh": 3.830295966711587,
          "fc_energy_efficiency": 0.5176582953182826,
          "fc_low_output_pct": 37.535545023696685,
          "battery_throughput_kwh": 1.5412573926228255,
          "battery_ohmic_loss_kwh": 0.0791544645846374,
          "soc_mean": 0.5963992381200789,
          "soc_delta": -0.95547235118173
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 28.77305213538411,
          "fc_energy_kwh": 0.4394730198181196,
          "fc_energy_efficiency": 0.45825896687696366,
          "fc_low_output_pct": 45.79025110782865,
          "battery_throughput_kwh": 1.495538928284843,
          "battery_ohmic_loss_kwh": 0.08741126301317748,
          "soc_mean": 0.6062597806247235,
          "soc_delta": 0.8766382446091943
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 294.19396753266176,
          "fc_energy_kwh": 5.090838168061167,
          "fc_energy_efficiency": 0.5191827023672264,
          "fc_low_output_pct": 13.449023861171366,
          "battery_throughput_kwh": 0.7067389102255136,
          "battery_ohmic_loss_kwh": 0.017653669900115136,
          "soc_mean": 0.5755871313087226,
          "soc_delta": 0.06282829816323965
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
    "total_cost_delta_usd": 31.803021873565726,
    "cost_delta_usd": {
      "h2_usd": -0.06999742374568019,
      "fc_usd": 32.31000648923356,
      "batt_usd": -0.4369871919221615
    },
    "soc_drift": -0.009848129074288003,
    "fuel_delta_gkm": -0.0999963196366842,
    "fc_loss_delta": 0.00025629200000365504,
    "batt_loss_delta": -5.5595471813441044e-05,
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
        "mean": 10.315233190600555,
        "std": 0.04244487854855389,
        "slope_per_10_episodes": -0.030299888936023464,
        "ep399_better_than_fraction": 0.775
      },
      "fc_loss": {
        "n": 40,
        "mean": 0.0007159962249883495,
        "std": 8.039717981161233e-05,
        "slope_per_10_episodes": 4.469412195168874e-05,
        "ep399_better_than_fraction": 0.45
      },
      "batt_loss": {
        "n": 40,
        "mean": 0.00044009632942712263,
        "std": 1.3016080890359471e-05,
        "slope_per_10_episodes": -7.149373654601732e-06,
        "ep399_better_than_fraction": 0.925
      }
    },
    "lucky_checkpoint": false
  },
  "reward_diff": "--- parent:17afbf80420c\n+++ candidate\n@@ -1,30 +1,118 @@\n def get_reward(self):\n     soc = float(self.SOC)\n     soc_low, soc_high = self.soc_bounds\n-    # SOC deviation from target\n-    soc_err = (np.abs(soc - self.SOC_target)) ** 2\n-    w_soc = np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10, self.w_soc)\n-    soc_cost = w_soc * soc_err\n+    soc_init = float(self.SOC_init)\n+    soc_target = float(self.SOC_target)\n \n-    h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal\n+    # ------------------------------------------------------------------ #\n+    # CHARGE-SUSTAINING: soc_cost = term_soc_anchor + term_drift_barrier  #\n+    # ------------------------------------------------------------------ #\n+\n+    # --- term_soc_anchor (catalog: soc_anchor, symmetric, p=2) ----------\n+    # Same shape as edit base (w_soc=500, x10 outside bounds).\n+    # Logged as term_soc_anchor; this IS the baseline's soc_cost form.\n+    soc_err_sq = (soc - soc_target) ** 2\n+    in_bounds = (soc_low < soc < soc_high)\n+    k_bounds = 10.0 if not in_bounds else 1.0\n+    term_soc_anchor = self.w_soc * soc_err_sq * k_bounds\n+\n+    # --- term_drift_barrier (catalog: drift_barrier, NEW) ---------------\n+    # Structural addition: edit base has no drift_barrier.\n+    # Flat for |SOC - SOC_init| <= d0 = 0.025, quadratic beyond.\n+    # Sizing: c_db=3000, d0=0.025 → ~2232 reward units over 1191 drift\n+    # steps (floor 2011, ceiling 50400, geometric mean 10070). ✓\n+    # Checked: zero at |SOC-SOC_init|<=0.025, positive at guard boundary\n+    # 0.05 on both sides (3000*(0.05-0.025)^2=1.875>0), nondecreasing. ✓\n+    c_db = 3000.0\n+    d0 = 0.025\n+    drift_abs = abs(soc - soc_init)\n+    drift_excess = drift_abs - d0 if drift_abs > d0 else 0.0\n+    term_drift_barrier = c_db * drift_excess * drift_excess\n+\n+    # soc_cost = sum of charge-sustaining terms\n+    soc_cost = term_soc_anchor + term_drift_barrier\n+\n+    # ------------------------------------------------------------------ #\n+    # HYDROGEN COST (unchanged weight w_h2 = 10)                          #\n+    # ------------------------------------------------------------------ #\n+    h2_fcs = float(self.h2_fcs)\n+    h2_batt = float(self.h2_batt)\n+    h2_equal = float(self.h2_equal)\n     h2_cost = self.w_h2 * h2_fcs\n-    # Cost of fuel cell degradation (scaled)\n-    fcs_soh_cost = self.w_fc * float(self.dSOH_FCS)\n-    # Cost of battery degradation (scaled)\n-    batt_soh_cost = self.w_batt * float(self.dSOH_batt)\n \n-    in_bounds = (soc_low < soc < soc_high)\n-    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost\n+    # ------------------------------------------------------------------ #\n+    # FC DEGRADATION COST (CHANGED: w_fc scaled by 1.05)                  #\n+    # CHANGE_SPEC: fcs_soh_cost \"changed\"                                  #\n+    # Slight upward alignment toward selection prices; keeps FC/battery    #\n+    # ratio constant (both scaled equally).                                #\n+    # ------------------------------------------------------------------ #\n+    w_fc_eff = self.w_fc * 1.05\n+    fcs_soh_cost = w_fc_eff * float(self.dSOH_FCS)\n+\n+    # ------------------------------------------------------------------ #\n+    # BATTERY DEGRADATION COST (CHANGED: w_batt scaled by 1.05)           #\n+    # CHANGE_SPEC: batt_soh_cost \"changed\"                                 #\n+    # Scaled in proportion with FC to avoid making battery a free buffer.  #\n+    # ------------------------------------------------------------------ #\n+    w_batt_eff = self.w_batt * 1.05\n+    batt_soh_cost = w_batt_eff * float(self.dSOH_batt)\n+\n+    # ------------------------------------------------------------------ #\n+    # EXTRA PRICE TERM 1: fc_efficiency_gap (catalog: fc_efficiency_gap)  #\n+    # NEW term: price H2 burned below peak efficiency eta_ref = 0.602.    #\n+    # eta = P_FCS / (120 * h2_fcs) when h2_fcs > 0, else 0.              #\n+    # c=20: mean term ~0.169/step, well with"
}
```

[Training log](results/aroma_runs/seed61_obscur_20261017_044026_162287183/search/20261017_044026_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed61_obscur_seq_v3_catalog_iter6/trials/0cc34903736efe26f64727e8/iter_001/train_log.log)
[Evaluation records](results/aroma_runs/seed61_obscur_20261017_044026_162287183/search/20261017_044026_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed61_obscur_seq_v3_catalog_iter6/trials/0cc34903736efe26f64727e8/deterministic_evaluations.jsonl)
