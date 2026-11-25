# Iteration 3

Decision: **retain_champion**

```json
{
  "iteration": 3,
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
    "iteration": 3
  },
  "edit_base": {
    "mode": "fuel_leader",
    "parent_reward_id": "17afbf80420cb9f947efdaac72a30bf9687444a44fa8df43fcfaa7ace533d083",
    "selection_reason": "fuel_leader: rank 1 of 1"
  },
  "candidate": {
    "candidate_id": "1c4e906f1be317d4d62cd3035e09884c20c8217a66e1f5fa714db0dae3615554",
    "seed": 61,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.716361215701049,
      "fc_loss": 0.000613624499961607,
      "batt_loss": 0.00033356203225598513,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5625227225817524,
      "soc_max": 0.6387036861239694
    },
    "operating_cost": {
      "h2_usd": 7.501452850990735,
      "fc_usd": 77.35790260885817,
      "batt_usd": 2.6218382730255416,
      "degradation_usd": 79.97974088188371,
      "total_usd": 87.48119373287444,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.654558245911646,
      "soc_correction_gkm": 0.06180296978940328,
      "soc_final": 0.5684667572800809,
      "soc_final_minus_initial": -0.031533242719919086,
      "unaccepted_fc_kwh": 0.0,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.740476492362045,
      "fc_loss": 0.0006105842874593564,
      "batt_loss": 0.00032848818758600683
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.5684667572800809,
      "soc_final_minus_initial": -0.031533242719919086,
      "soc_swing": 0.07618096354221704,
      "soc_mean": 0.5795040730378379,
      "fc_power_kw_mean": 9.748226357075437,
      "fc_abs_ramp_kw_s_mean": 1.8902563617082262,
      "fc_on_pct": 73.03109561174077,
      "fc_start_stop_count": 30,
      "fc_start_stop_soh_loss": 0.000588,
      "fc_low_power_count": 883,
      "fc_low_power_soh_loss": 3.0904999999999995e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 38,
      "fc_load_change_soh_loss": 2.2534e-05,
      "battery_throughput_kwh": 2.9533716192953117,
      "battery_ohmic_loss_kw_integral_kwh": 0.1269675960716643,
      "fc_low_output_pct": 37.80877651845394,
      "fc_regeneration_energy_kwh": 0.2253296539914736,
      "fc_energy_efficiency": 0.4951616365682107
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
          "battery_ohmic_loss_kwh": 3.9997608485211944e-08,
          "soc_mean": 0.5970366760181873,
          "soc_delta": -0.00012396817674220628
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 72.60973010533871,
          "fc_energy_kwh": 1.0830141913383295,
          "fc_energy_efficiency": 0.44751130544791157,
          "fc_low_output_pct": 50.69252077562327,
          "battery_throughput_kwh": 0.5710427322736136,
          "battery_ohmic_loss_kwh": 0.01169339576519605,
          "soc_mean": 0.5847868913093653,
          "soc_delta": -0.2907890604530631
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 248.6503155258644,
          "fc_energy_kwh": 4.215129246442761,
          "fc_energy_efficiency": 0.5086119588395714,
          "fc_low_output_pct": 28.24644549763033,
          "battery_throughput_kwh": 1.242756331107734,
          "battery_ohmic_loss_kwh": 0.05281836265931629,
          "soc_mean": 0.5786355718054397,
          "soc_delta": -0.7195250948749903
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 28.00605215143409,
          "fc_energy_kwh": 0.2253296539914736,
          "fc_energy_efficiency": 0.24139659669831953,
          "fc_low_output_pct": 62.77695716395865,
          "battery_throughput_kwh": 1.29636517994134,
          "battery_ohmic_loss_kwh": 0.06960099341315244,
          "soc_mean": 0.5851077404943276,
          "soc_delta": 0.765536070479184
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 292.0047854365632,
          "fc_energy_kwh": 5.010971454295737,
          "fc_energy_efficiency": 0.5148688841585385,
          "fc_low_output_pct": 15.61822125813449,
          "battery_throughput_kwh": 0.3666815307584275,
          "battery_ohmic_loss_kwh": 0.0067174900513884426,
          "soc_mean": 0.5700841699043517,
          "soc_delta": 0.025751055259803257
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
    "total_cost_delta_usd": 14.318359709317363,
    "cost_delta_usd": {
      "h2_usd": 0.24337722465870293,
      "fc_usd": 15.210697123347728,
      "batt_usd": -1.1357146386890742
    },
    "soc_drift": -0.031533242719919086,
    "fuel_delta_gkm": 0.34768174951243225,
    "fc_loss_delta": 0.00012065549997619662,
    "batt_loss_delta": -0.00014449071357358623,
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
        "mean": 10.740476492362045,
        "std": 0.05729269981622539,
        "slope_per_10_episodes": 0.03674396203010724,
        "ep399_better_than_fraction": 0.625
      },
      "fc_loss": {
        "n": 40,
        "mean": 0.0006105842874593564,
        "std": 5.8226317173668156e-05,
        "slope_per_10_episodes": -3.8128446999865025e-05,
        "ep399_better_than_fraction": 0.45
      },
      "batt_loss": {
        "n": 40,
        "mean": 0.00032848818758600683,
        "std": 4.287968417999288e-06,
        "slope_per_10_episodes": 2.551972770521001e-06,
        "ep399_better_than_fraction": 0.1
      }
    },
    "lucky_checkpoint": false
  },
  "reward_diff": "--- parent:17afbf80420c\n+++ candidate\n@@ -1,30 +1,94 @@\n def get_reward(self):\n     soc = float(self.SOC)\n     soc_low, soc_high = self.soc_bounds\n-    # SOC deviation from target\n-    soc_err = (np.abs(soc - self.SOC_target)) ** 2\n-    w_soc = np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10, self.w_soc)\n-    soc_cost = w_soc * soc_err\n+    soc_init = float(self.SOC_init)\n+    soc_target = float(self.SOC_target)\n \n-    h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal\n+    # ------------------------------------------------------------------ #\n+    # CHARGE-SUSTAINING: soc_cost = soc_anchor + drift_barrier            #\n+    #                              + fc_surplus_charge                    #\n+    # ------------------------------------------------------------------ #\n+\n+    # --- term_soc_anchor (catalog: soc_anchor, symmetric, p=2) ----------\n+    # Same shape as edit base (w_soc=500, x10 outside bounds).\n+    soc_err_sq = (soc - soc_target) ** 2\n+    in_bounds = (soc_low < soc < soc_high)\n+    k_bounds = 10.0 if not in_bounds else 1.0\n+    term_soc_anchor = self.w_soc * soc_err_sq * k_bounds\n+\n+    # --- term_drift_barrier (catalog: drift_barrier, NEW) ---------------\n+    # Flat for |SOC - SOC_init| <= d0 = 0.025, quadratic beyond.\n+    # Structural addition: edit base has no drift_barrier.\n+    # Sizing: c_db=12000, d0=0.025 → ~7557 reward units over 1191 drift\n+    # steps (floor 2011, ceiling 50400, geometric mean 10070). ✓\n+    c_db = 12000.0\n+    d0 = 0.025\n+    drift_abs = abs(soc - soc_init)\n+    drift_excess = drift_abs - d0 if drift_abs > d0 else 0.0\n+    term_drift_barrier = c_db * drift_excess * drift_excess\n+\n+    # --- term_fc_surplus_charge (catalog: fc_surplus_charge, NEW) -------\n+    # Price FC power pushed into the battery while SOC is above target.\n+    # g(SOC) = max(0, SOC - SOC_target + m) / m, m = 0.05\n+    # Zero at SOC <= SOC_target - 0.05, ramps to 1 at SOC = SOC_target + 0.05.\n+    # P_fc_to_batt_kw = max(0, min(-P_batt, P_mot - P_batt)) / 1000\n+    # Structural addition: edit base has no fc_surplus_charge.\n+    # Sizing: c_fsc=4.0 → ~3000 reward units over ~470 above-target steps. ✓\n+    p_batt_w = float(self.P_batt)   # W, + = discharge\n+    p_mot_w  = float(self.P_mot)    # W, motor electrical power\n+    # FC power into battery (kW): positive only when FC charges battery\n+    p_fc_to_batt_kw = max(0.0, min(-p_batt_w, p_mot_w - p_batt_w)) / 1000.0\n+    m_fsc = 0.05\n+    g_fsc_raw = (soc - soc_target + m_fsc) / m_fsc\n+    g_fsc = g_fsc_raw if g_fsc_raw > 0.0 else 0.0\n+    g_fsc = g_fsc if g_fsc < 1.0 else 1.0   # cap at 1 for interpretability\n+    c_fsc = 4.0\n+    term_fc_surplus_charge = c_fsc * g_fsc * p_fc_to_batt_kw\n+\n+    # soc_cost = sum of all charge-sustaining terms\n+    soc_cost = term_soc_anchor + term_drift_barrier + term_fc_surplus_charge\n+\n+    # ------------------------------------------------------------------ #\n+    # HYDROGEN COST (unchanged weight w_h2 = 10)                          #\n+    # ------------------------------------------------------------------ #\n+    h2_fcs  = float(self.h2_fcs)\n+    h2_batt = float(self.h2_batt)\n+    h2_equal = float(self.h2_equal)\n     h2_cost = self.w_h2 * h2_fcs\n-    # Cost of fuel cell degradation (scaled)\n+\n+    # ------------------------------------------------------------------ #\n+    # FC DEGRADATION COST (unchanged weight w_fc)                         #\n+    # ------------------------------------------------------------------ #\n     fcs_soh_cost = self.w_fc * float(self.dSOH_FCS)\n-    # Cost of battery degradation (scaled)\n+\n+    # ------------------------------------------------------------------ #\n+    # BATTERY DEGRADATION COST (unchanged weight w_batt)                  #\n+    # ------------------------------------------------------------------ #\n     batt_soh_cost = self.w_batt * float(self.dSOH_batt)\n \n-    in_bounds = (soc_low < soc < soc_high)\n+    # -----------------------------------------------"
}
```

[Training log](results/aroma_runs/seed61_obscur_20261017_044026_162287183/search/20261017_044026_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed61_obscur_seq_v3_catalog_iter6/trials/115e25a2700ab75a645efa49/iter_001/train_log.log)
[Evaluation records](results/aroma_runs/seed61_obscur_20261017_044026_162287183/search/20261017_044026_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed61_obscur_seq_v3_catalog_iter6/trials/115e25a2700ab75a645efa49/deterministic_evaluations.jsonl)
