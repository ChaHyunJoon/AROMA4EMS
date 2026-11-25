# Iteration 4

Decision: **retain_champion**

```json
{
  "iteration": 4,
  "control": {
    "candidate_id": "eb92825323ba17b3c53a26167f4276edba0c98b8823ab4fd1114398bb4fe87c8",
    "seed": 81,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 11.012690244020076,
      "fc_loss": 0.00016522099994698003,
      "batt_loss": 0.0004471829724568277,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5356604535438519,
      "soc_max": 0.6594957067994687
    },
    "operating_cost": {
      "h2_usd": 7.708883170814053,
      "fc_usd": 20.82894347216633,
      "batt_usd": 3.5149127264366595,
      "degradation_usd": 24.34385619860299,
      "total_usd": 32.05273936941705,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 11.047211535207287,
      "soc_correction_gkm": -0.03452129118721069,
      "soc_final": 0.6174368328350545,
      "soc_final_minus_initial": 0.017436832835054483,
      "unaccepted_fc_kwh": 0.0,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.932573211532263,
      "fc_loss": 0.00024285443745112323,
      "batt_loss": 0.00043797167866345134
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.6174368328350545,
      "soc_final_minus_initial": 0.017436832835054483,
      "soc_swing": 0.12383525325561673,
      "soc_mean": 0.5934304569935521,
      "fc_power_kw_mean": 9.986558262293208,
      "fc_abs_ramp_kw_s_mean": 1.3469995077848216,
      "fc_on_pct": 83.60941586748038,
      "fc_start_stop_count": 8,
      "fc_start_stop_soh_loss": 0.0001568,
      "fc_low_power_count": 1220,
      "fc_low_power_soh_loss": 4.269999999999999e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 7,
      "fc_load_change_soh_loss": 4.151e-06,
      "battery_throughput_kwh": 4.082510594505293,
      "battery_ohmic_loss_kw_integral_kwh": 0.1977533812512255,
      "fc_low_output_pct": 49.636733507701244,
      "fc_regeneration_energy_kwh": 0.4969230146908743,
      "fc_energy_efficiency": 0.49019431860696255
    },
    "regimes": {
      "available": true,
      "groups": {
        "stopped": {
          "steps": 408,
          "available": true,
          "duration_s": 408.0,
          "hydrogen_g": 6.8275571669241,
          "fc_energy_kwh": 0.057250697549092545,
          "fc_energy_efficiency": 0.2515823234792764,
          "fc_low_output_pct": 25.245098039215684,
          "battery_throughput_kwh": 0.038532008909916364,
          "battery_ohmic_loss_kwh": 0.00023858230327318273,
          "soc_mean": 0.6217680053092913,
          "soc_delta": 0.023591570683975438
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 95.95283255522912,
          "fc_energy_kwh": 1.4328755502392463,
          "fc_energy_efficiency": 0.44803852495953145,
          "fc_low_output_pct": 60.45706371191135,
          "battery_throughput_kwh": 0.7143053955265158,
          "battery_ohmic_loss_kwh": 0.014824636289936905,
          "soc_mean": 0.6046046666402394,
          "soc_delta": -0.11263207686616838
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 224.7081130760012,
          "fc_energy_kwh": 3.7575757058972714,
          "fc_energy_efficiency": 0.5017110574609768,
          "fc_low_output_pct": 43.791469194312796,
          "battery_throughput_kwh": 1.7945661701066837,
          "battery_ohmic_loss_kwh": 0.09836172813944015,
          "soc_mean": 0.5900999221556504,
          "soc_delta": -1.0095780179439677
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 44.782449414305404,
          "fc_energy_kwh": 0.4969230146908743,
          "fc_energy_efficiency": 0.33292465137245253,
          "fc_low_output_pct": 88.18316100443131,
          "battery_throughput_kwh": 1.5136446440589968,
          "battery_ohmic_loss_kwh": 0.0849717671054913,
          "soc_mean": 0.6007234717725822,
          "soc_delta": 0.8902075051033946
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 298.74154730173143,
          "fc_energy_kwh": 5.150647487965471,
          "fc_energy_efficiency": 0.517286194446517,
          "fc_low_output_pct": 12.79826464208243,
          "battery_throughput_kwh": 0.8047919948563224,
          "battery_ohmic_loss_kwh": 0.02470204896219479,
          "soc_mean": 0.5763921954220459,
          "soc_delta": 0.08872821032779477
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
    "parent_reward_id": "eb92825323ba17b3c53a26167f4276edba0c98b8823ab4fd1114398bb4fe87c8",
    "selection_reason": "champion_improve: rank 1 of 1 (no fresh guard_repair target)"
  },
  "candidate": {
    "candidate_id": "cace7bb7665bd619ed081257896830a03675f705373f7993ed6fbfbc08312699",
    "seed": 81,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.737645847987707,
      "fc_loss": 0.0002648909999630744,
      "batt_loss": 0.00048737468724169286,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5256468229766352,
      "soc_max": 0.650451364373683
    },
    "operating_cost": {
      "h2_usd": 7.5163520935913954,
      "fc_usd": 33.39405805731137,
      "batt_usd": 3.8308245086283965,
      "degradation_usd": 37.224882565939765,
      "total_usd": 44.74123465953116,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.811646253653278,
      "soc_correction_gkm": -0.07400040566557037,
      "soc_final": 0.6386426703659265,
      "soc_final_minus_initial": 0.0386426703659265,
      "unaccepted_fc_kwh": 2.6533806274073868e-05,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.7083867517299,
      "fc_loss": 0.0002869641749639773,
      "batt_loss": 0.00048662378385561924
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.6386426703659265,
      "soc_final_minus_initial": 0.0386426703659265,
      "soc_swing": 0.12480454139704777,
      "soc_mean": 0.6001046250509583,
      "fc_power_kw_mean": 10.045613389292075,
      "fc_abs_ramp_kw_s_mean": 1.1703500317453313,
      "fc_on_pct": 84.07439697762278,
      "fc_start_stop_count": 13,
      "fc_start_stop_soh_loss": 0.0002548,
      "fc_low_power_count": 850,
      "fc_low_power_soh_loss": 2.9749999999999995e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 12,
      "fc_load_change_soh_loss": 7.116000000000001e-06,
      "battery_throughput_kwh": 4.479527307693387,
      "battery_ohmic_loss_kw_integral_kwh": 0.23046213619569075,
      "fc_low_output_pct": 44.81255448997384,
      "fc_regeneration_energy_kwh": 0.6496627275074051,
      "fc_energy_efficiency": 0.5067814739271126
    },
    "regimes": {
      "available": true,
      "groups": {
        "stopped": {
          "steps": 408,
          "available": true,
          "duration_s": 408.0,
          "hydrogen_g": 0.19791441288159384,
          "fc_energy_kwh": 0.0016220501357837437,
          "fc_energy_efficiency": 0.24589604163744752,
          "fc_low_output_pct": 0.7352941176470588,
          "battery_throughput_kwh": 0.0012793841980483828,
          "battery_ohmic_loss_kwh": 6.6619145388538445e-06,
          "soc_mean": 0.638676968060366,
          "soc_delta": 0.0005415699917398209
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 112.89516004412022,
          "fc_energy_kwh": 1.8715685030325289,
          "fc_energy_efficiency": 0.497387756357906,
          "fc_low_output_pct": 47.43767313019391,
          "battery_throughput_kwh": 0.7499921154470235,
          "battery_ohmic_loss_kwh": 0.016377947810337343,
          "soc_mean": 0.6180266206091082,
          "soc_delta": 0.13242214325825497
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 198.8421257734711,
          "fc_energy_kwh": 3.4149560367870677,
          "fc_energy_efficiency": 0.5152777692239972,
          "fc_low_output_pct": 52.41706161137441,
          "battery_throughput_kwh": 1.939697230115012,
          "battery_ohmic_loss_kwh": 0.11419634352198213,
          "soc_mean": 0.6016770012027557,
          "soc_delta": -1.2290834514528461
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 50.44469647865527,
          "fc_energy_kwh": 0.6496627275074051,
          "fc_energy_efficiency": 0.3864000057284632,
          "fc_low_output_pct": 86.85376661742984,
          "battery_throughput_kwh": 1.6467524364062458,
          "battery_ohmic_loss_kwh": 0.09719422548146428,
          "soc_mean": 0.6161061048782459,
          "soc_delta": 0.9637066096927636
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 293.7702562394087,
          "fc_energy_kwh": 5.118395847654962,
          "fc_energy_efficiency": 0.5227460196913679,
          "fc_low_output_pct": 3.7960954446854664,
          "battery_throughput_kwh": 1.1067156708282297,
          "battery_ohmic_loss_kwh": 0.04217286553927364,
          "soc_mean": 0.5526175729207655,
          "soc_delta": 0.05487965797094552
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
    "total_cost_delta_usd": 12.688495290114112,
    "cost_delta_usd": {
      "h2_usd": -0.1925310772226574,
      "fc_usd": 12.56511458514504,
      "batt_usd": 0.315911782191737
    },
    "soc_drift": 0.0386426703659265,
    "fuel_delta_gkm": -0.27504439603236897,
    "fc_loss_delta": 9.967000001609438e-05,
    "batt_loss_delta": 4.019171478486516e-05,
    "guards": {
      "reference": "baseline",
      "max_fuel_increase_fraction": 0.05,
      "max_batt_increase_fraction": 0.1,
      "fuel_gkm_max": 11.379965776372485,
      "batt_loss_max": 0.0006755079032101375,
      "soc_drift_abs_max": 0.05
    },
    "guard_reference": "baseline",
    "comparison_basis": "matched_fresh_training",
    "total_cost_delta_usd_vs_baseline": 8.82065351449367,
    "fuel_delta_gkm_vs_baseline": -0.10041679617656385,
    "fc_loss_delta_vs_baseline": 7.842649999234563e-05,
    "batt_loss_delta_vs_baseline": -0.0001267234065857048
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
        "mean": 10.7083867517299,
        "std": 0.018465861187582804,
        "slope_per_10_episodes": 0.011079455005008293,
        "ep399_better_than_fraction": 0.05
      },
      "fc_loss": {
        "n": 40,
        "mean": 0.0002869641749639773,
        "std": 2.4507323707052545e-05,
        "slope_per_10_episodes": 1.1556447466822893e-05,
        "ep399_better_than_fraction": 0.675
      },
      "batt_loss": {
        "n": 40,
        "mean": 0.00048662378385561924,
        "std": 7.786705381348397e-06,
        "slope_per_10_episodes": -3.9222616781755304e-06,
        "ep399_better_than_fraction": 0.5
      }
    },
    "lucky_checkpoint": false
  },
  "reward_diff": "--- parent:eb92825323ba\n+++ candidate\n@@ -4,47 +4,75 @@\n     soc_init = float(self.SOC_init)\n     soc_target = float(self.SOC_target)\n \n-    # ── soc_anchor (catalog: soc_anchor, symmetric quadratic, unchanged shape from edit base) ──\n+    # ── term_soc_anchor (catalog: soc_anchor, symmetric quadratic) ──\n+    # Unchanged shape from edit base: w_soc * (soc - soc_target)^2,\n+    # multiplied by 10 outside soc_bounds.\n     soc_err = (soc - soc_target) ** 2\n-    w_soc_step = np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10.0, self.w_soc)\n-    term_soc_anchor = float(w_soc_step * soc_err)\n+    w_soc_step = float(np.where(\n+        (soc >= soc_high) | (soc <= soc_low),\n+        self.w_soc * 10.0,\n+        self.w_soc\n+    ))\n+    term_soc_anchor = w_soc_step * soc_err\n \n-    # ── drift_barrier (catalog: drift_barrier, NEW — not in edit base) ──\n+    # ── term_drift_barrier (catalog: drift_barrier) ──\n     # Flat inside |SOC - SOC_init| <= 0.025, quadratic beyond.\n     # c=60, d0=0.025, p=2.\n-    # Sizing: at mean drift 0.06 → 60*(0.06-0.025)^2 = 0.0735/step;\n-    #         over 2778 steps → ~204 reward units (inside [670.3, 24830] combined with fc_surplus_charge).\n-    # Checked: zero at |SOC-SOC_init|=0.01 ✓, positive at guard edge 0.05 ✓, nondecreasing ✓.\n+    # Sizing: at |drift|=0.06 → 60*(0.06-0.025)^2=0.0735/step;\n+    #   over 952 steps with |drift|>0.025 → ~70 reward units.\n+    # Checked: zero at |SOC-SOC_init|=0.01 ✓, positive at guard edge 0.05 ✓,\n+    #          nondecreasing in |SOC-SOC_init| ✓.\n     c_barrier = 60.0\n     d0_barrier = 0.025\n     soc_abs_dev = float(np.abs(soc - soc_init))\n     barrier_excess = float(np.maximum(0.0, soc_abs_dev - d0_barrier))\n     term_drift_barrier = c_barrier * barrier_excess ** 2\n \n-    # ── fc_surplus_charge (catalog: fc_surplus_charge, NEW — not in edit base) ──\n+    # ── term_fc_surplus_charge (catalog: fc_surplus_charge) ──\n     # Price FC power flowing into the battery when SOC > SOC_target.\n-    # g(SOC) = max(0, SOC - SOC_target + 0.05) / 0.05, clamped to [0,1] for interpretability\n-    #   (ramps 0→1 from SOC=0.55 to SOC=0.65, saturates above).\n+    # g(SOC) = max(0, SOC - SOC_target + m) / m, m=0.05.\n+    # Ramps 0→1 from SOC=0.55 to SOC=0.65, unclamped above (nondecreasing).\n     # P_fc_to_batt_kw = max(0, min(-P_batt, P_mot - P_batt)) / 1000\n-    # c=0.8; at mean FC->batt 3.37 kW, g=1: 0.8*3.37=2.70/step;\n-    #   over ~1000 active steps above target: ~2700 reward units.\n-    # Combined with drift_barrier ~200: total ~2900, inside [670.3, 24830] ✓.\n+    # c=0.8; at mean FC->batt 1.52 kW above target, g≈0.5, ~952 steps:\n+    #   0.8 * 0.5 * 1.52 * 952 ≈ 580 reward units.\n     # Checked: zero while discharging ✓, zero for pure regen (no FC power) ✓,\n-    #          zero at SOC_target-0.1=0.50 ✓, positive at SOC_target+0.05=0.65 with FC charging ✓,\n+    #          zero at SOC_target-0.1=0.50 ✓, positive at SOC_target+0.05 with FC charging ✓,\n     #          nondecreasing in SOC and FC charging power ✓.\n     m_surplus = 0.05\n     g_surplus = float(np.maximum(0.0, soc - soc_target + m_surplus) / m_surplus)\n-    # Clamp g to [0, 1] — above SOC_target+m it stays at 1, which is fine (nondecreasing)\n-    # Actually catalog says g nondecreasing, no upper clamp required; leave unclamped for full signal\n-    p_batt_w = float(self.P_batt)      # W, + = discharge\n-    p_mot_w = float(self.P_mot)        # W, motor electrical power\n-    # FC power into battery (kW): positive only when FC is charging the battery\n-    p_fc_to_batt_kw = float(np.maximum(0.0, np.minimum(-p_batt_w, p_mot_w - p_batt_w))) / 1000.0\n+    p_batt_w = float(self.P_batt)    # W, + = discharge\n+    p_mot_w = float(self.P_mot)      # W, motor electrical power\n+    # FC power into battery (kW): positive only when FC is net-charging the battery\n+    p_fc_to_batt_kw = float(\n+        np.maximum(0.0, np.minimum(-p_batt_w, p_mot_w - p_batt_w))\n+    ) / 1000.0\n     c_surplus = 0.8\n     term_fc_surplus_charge = c_"
}
```

[Training log](results/aroma_runs/seed81_obscur_20261017_035710_165538473/search/20261017_035710_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed81_obscur_seq_v3_catalog_iter6/trials/b6a152de77396689c89b7da4/iter_001/train_log.log)
[Evaluation records](results/aroma_runs/seed81_obscur_20261017_035710_165538473/search/20261017_035710_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed81_obscur_seq_v3_catalog_iter6/trials/b6a152de77396689c89b7da4/deterministic_evaluations.jsonl)
