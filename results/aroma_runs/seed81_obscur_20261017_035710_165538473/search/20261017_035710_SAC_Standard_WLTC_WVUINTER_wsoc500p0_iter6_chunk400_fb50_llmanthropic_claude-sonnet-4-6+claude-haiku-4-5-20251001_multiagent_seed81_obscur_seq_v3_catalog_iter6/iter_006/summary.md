# Iteration 6

Decision: **retain_champion**

```json
{
  "iteration": 6,
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
    "iteration": 6
  },
  "edit_base": {
    "mode": "fuel_leader",
    "parent_reward_id": "cace7bb7665bd619ed081257896830a03675f705373f7993ed6fbfbc08312699",
    "selection_reason": "fuel_leader: rank 1 of 3"
  },
  "candidate": {
    "candidate_id": "3eefebda73f91ae84f8413f477e9268adae55d420a2c2245f31977c6b18f269c",
    "seed": 81,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.851982454042885,
      "fc_loss": 0.00022982999995579956,
      "batt_loss": 0.00045328771461572437,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5263367634976476,
      "soc_max": 0.6374577379288833
    },
    "operating_cost": {
      "h2_usd": 7.596387717830019,
      "fc_usd": 28.974017097242726,
      "batt_usd": 3.562896744674276,
      "degradation_usd": 32.536913841917,
      "total_usd": 40.133301559747025,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.831752006088191,
      "soc_correction_gkm": 0.02023044795469301,
      "soc_final": 0.5896464235305064,
      "soc_final_minus_initial": -0.01035357646949353,
      "unaccepted_fc_kwh": 0.0003816154473446787,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.85781928867934,
      "fc_loss": 0.00024278986245732104,
      "batt_loss": 0.00046333885665603147
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.5896464235305064,
      "soc_final_minus_initial": -0.01035357646949353,
      "soc_swing": 0.1111209744312357,
      "soc_mean": 0.5773650540897963,
      "fc_power_kw_mean": 9.903525358701629,
      "fc_abs_ramp_kw_s_mean": 1.3889039215379635,
      "fc_on_pct": 78.81429816913688,
      "fc_start_stop_count": 11,
      "fc_start_stop_soh_loss": 0.00021559999999999998,
      "fc_low_power_count": 1016,
      "fc_low_power_soh_loss": 3.555999999999999e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 18,
      "fc_load_change_soh_loss": 1.0674e-05,
      "battery_throughput_kwh": 4.216911052417159,
      "battery_ohmic_loss_kw_integral_kwh": 0.2068954873235086,
      "fc_low_output_pct": 44.20226678291194,
      "fc_regeneration_energy_kwh": 0.5563143755986137,
      "fc_energy_efficiency": 0.49667533877420805
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
          "battery_ohmic_loss_kwh": 3.998635316526359e-08,
          "soc_mean": 0.609256975146212,
          "soc_delta": -0.00012395671514797701
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 86.17922086574166,
          "fc_energy_kwh": 1.3078291078349427,
          "fc_energy_efficiency": 0.4553162203205545,
          "fc_low_output_pct": 49.584487534626035,
          "battery_throughput_kwh": 0.7471003532284008,
          "battery_ohmic_loss_kwh": 0.018030317773115,
          "soc_mean": 0.5894512276192672,
          "soc_delta": -0.17299990535026777
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 214.13893625930916,
          "fc_energy_kwh": 3.6137634062318407,
          "fc_energy_efficiency": 0.5063242885923224,
          "fc_low_output_pct": 41.32701421800948,
          "battery_throughput_kwh": 1.8264834917582913,
          "battery_ohmic_loss_kwh": 0.09658219538485248,
          "soc_mean": 0.5748914526688913,
          "soc_delta": -1.093129703362369
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 44.3331314820815,
          "fc_energy_kwh": 0.5563143755986137,
          "fc_energy_efficiency": 0.37649270015456493,
          "fc_low_output_pct": 83.16100443131462,
          "battery_throughput_kwh": 1.5693067083617118,
          "battery_ohmic_loss_kwh": 0.09324242513534627,
          "soc_mean": 0.5876618054135698,
          "soc_delta": 0.9212336975490718
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 298.5678077210051,
          "fc_energy_kwh": 5.145084764519917,
          "fc_energy_efficiency": 0.5170282118218824,
          "fc_low_output_pct": 13.015184381778742,
          "battery_throughput_kwh": 0.8245070084062763,
          "battery_ohmic_loss_kwh": 0.02771398265208124,
          "soc_mean": 0.5541974154933018,
          "soc_delta": 0.08258883384546034
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
    "total_cost_delta_usd": 8.080562190329978,
    "cost_delta_usd": {
      "h2_usd": -0.1124954529840334,
      "fc_usd": 8.145073625076396,
      "batt_usd": 0.04798401823761633
    },
    "soc_drift": -0.01035357646949353,
    "fuel_delta_gkm": -0.1607077899771916,
    "fc_loss_delta": 6.460900000881953e-05,
    "batt_loss_delta": 6.10474215889667e-06,
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
    "total_cost_delta_usd_vs_baseline": 4.212720414709537,
    "fuel_delta_gkm_vs_baseline": 0.01391980987861352,
    "fc_loss_delta_vs_baseline": 4.336549998507078e-05,
    "batt_loss_delta_vs_baseline": -0.0001608103792116733
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
        "mean": 10.85781928867934,
        "std": 0.03896263709015622,
        "slope_per_10_episodes": -0.01173628319965713,
        "ep399_better_than_fraction": 0.6
      },
      "fc_loss": {
        "n": 40,
        "mean": 0.00024278986245732104,
        "std": 1.7118703046219495e-05,
        "slope_per_10_episodes": -7.170022044841705e-06,
        "ep399_better_than_fraction": 0.675
      },
      "batt_loss": {
        "n": 40,
        "mean": 0.00046333885665603147,
        "std": 7.038545612889122e-06,
        "slope_per_10_episodes": -2.8325949670977966e-06,
        "ep399_better_than_fraction": 0.85
      }
    },
    "lucky_checkpoint": false
  },
  "reward_diff": "--- parent:cace7bb7665b\n+++ candidate\n@@ -18,8 +18,9 @@\n     # ── term_drift_barrier (catalog: drift_barrier) ──\n     # Flat inside |SOC - SOC_init| <= 0.025, quadratic beyond.\n     # c=60, d0=0.025, p=2.\n-    # Sizing: at |drift|=0.06 → 60*(0.06-0.025)^2=0.0735/step;\n-    #   over 952 steps with |drift|>0.025 → ~70 reward units.\n+    # Sizing: at |drift|=0.039 (edit base) → 60*(0.039-0.025)^2=0.01176/step;\n+    #   over 2020 steps with |drift|>0.025 → ~23.8 reward units.\n+    # At guard edge 0.05: 60*(0.05-0.025)^2=0.0375/step.\n     # Checked: zero at |SOC-SOC_init|=0.01 ✓, positive at guard edge 0.05 ✓,\n     #          nondecreasing in |SOC-SOC_init| ✓.\n     c_barrier = 60.0\n@@ -33,8 +34,8 @@\n     # g(SOC) = max(0, SOC - SOC_target + m) / m, m=0.05.\n     # Ramps 0→1 from SOC=0.55 to SOC=0.65, unclamped above (nondecreasing).\n     # P_fc_to_batt_kw = max(0, min(-P_batt, P_mot - P_batt)) / 1000\n-    # c=0.8; at mean FC->batt 1.52 kW above target, g≈0.5, ~952 steps:\n-    #   0.8 * 0.5 * 1.52 * 952 ≈ 580 reward units.\n+    # c=0.8; at mean FC->batt 1.97 kW above target (measured), g≈0.5, ~952 steps:\n+    #   0.8 * 0.5 * 1.97 * 952 ≈ 752 reward units.\n     # Checked: zero while discharging ✓, zero for pure regen (no FC power) ✓,\n     #          zero at SOC_target-0.1=0.50 ✓, positive at SOC_target+0.05 with FC charging ✓,\n     #          nondecreasing in SOC and FC charging power ✓.\n@@ -49,32 +50,14 @@\n     c_surplus = 0.8\n     term_fc_surplus_charge = c_surplus * g_surplus * p_fc_to_batt_kw\n \n-    # ── term_fc_peak_shave (catalog: fc_peak_shave, NEW — not in edit base) ──\n-    # When SOC is above target, price FC power above P_cap=20 kW.\n-    # Incentivizes battery to cover high-power transients; FC stays in efficient band.\n-    # g(SOC) = max(0, SOC - SOC_target + m) / m, m=0.05 (same ramp as surplus charge).\n-    # P_cap=20 kW (above the 10-15 kW peak-efficiency band).\n-    # c=15; at SOC_target+0.025 (g=0.5), P_FCS=30 kW: 15*0.5*10=75/step.\n-    # Over ~172 steps above 20 kW with g≈0.5: ~1290 reward units.\n-    # Checked: zero at P_FCS<=20 kW ✓, zero at SOC_target-0.1 ✓,\n-    #          positive at SOC_target+0.05 with P_FCS=60 kW ✓,\n-    #          nondecreasing in SOC and in P_FCS ✓.\n-    p_cap_kw = 20.0\n-    c_peak_shave = 15.0\n-    p_fcs_kw = float(self.P_FCS)\n-    fc_excess_kw = float(np.maximum(0.0, p_fcs_kw - p_cap_kw))\n-    # g_surplus is already computed above with the same m=0.05; reuse it.\n-    term_fc_peak_shave = c_peak_shave * g_surplus * fc_excess_kw\n-\n     # ── soc_cost = sum of ALL charge-sustaining terms (catalog contract) ──\n-    # soc_cost must equal exactly the sum of the four logged term_ values.\n+    # soc_cost must equal exactly the sum of the three logged term_ values.\n     term_soc_anchor = float(term_soc_anchor)\n     term_drift_barrier = float(term_drift_barrier)\n     term_fc_surplus_charge = float(term_fc_surplus_charge)\n-    term_fc_peak_shave = float(term_fc_peak_shave)\n-    soc_cost = term_soc_anchor + term_drift_barrier + term_fc_surplus_charge + term_fc_peak_shave\n+    soc_cost = term_soc_anchor + term_drift_barrier + term_fc_surplus_charge\n \n-    # ── standard price terms (unchanged from edit base) ──\n+    # ── standard price terms ──\n     h2_fcs = self.h2_fcs\n     h2_batt = self.h2_batt\n     h2_equal = self.h2_equal\n@@ -82,25 +65,50 @@\n     fcs_soh_cost = self.w_fc * float(self.dSOH_FCS)\n     batt_soh_cost = self.w_batt * float(self.dSOH_batt)\n \n+    # ── term_fc_efficiency_gap (catalog: fc_efficiency_gap, NEW — replaces fc_peak_shave) ──\n+    # Price hydrogen burned below the FC's peak efficiency (eta_ref=0.601 at 10-15 kW).\n+    # eta = P_FCS / (120 * h2_fcs) when h2_fcs > 0 (else term = 0; guards division by zero).\n+    # c=4 (vs. iteration 3's c=40 which caused 33 load changes; c=4 is 10x smaller).\n+    # Sizing at c=4:\n+    #   4 kW band (eta=0.484, gap=0.196, h2_fcs≈0.0267 g/step): 4*0.0267*0.196/0.601≈0.035/step\n+    #   2 kW band (eta=0.215, gap=0.646, h2_fcs≈0.0117 g/step): 4*0.0117"
}
```

[Training log](results/aroma_runs/seed81_obscur_20261017_035710_165538473/search/20261017_035710_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed81_obscur_seq_v3_catalog_iter6/trials/2eb0efa915b881f6cfa76b76/iter_001/train_log.log)
[Evaluation records](results/aroma_runs/seed81_obscur_20261017_035710_165538473/search/20261017_035710_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed81_obscur_seq_v3_catalog_iter6/trials/2eb0efa915b881f6cfa76b76/deterministic_evaluations.jsonl)
