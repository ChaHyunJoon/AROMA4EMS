# Iteration 6

Decision: **retain_champion**

```json
{
  "iteration": 6,
  "control": {
    "candidate_id": "9a1a00b2da2f4836b7563a0ad13593c767d8ae9618ae004902187c2068ca2d83",
    "seed": 1,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.592957563806065,
      "fc_loss": 0.00014194499997055576,
      "batt_loss": 0.0004656390750389372,
      "soc_in_bounds": 100.0,
      "soc_min": 0.564684939325233,
      "soc_max": 0.6680178496457082
    },
    "operating_cost": {
      "h2_usd": 7.415070294664246,
      "fc_usd": 17.89460408478419,
      "batt_usd": 3.6599799446490873,
      "degradation_usd": 21.55458402943328,
      "total_usd": 28.969654324097526,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.550211884342488,
      "soc_correction_gkm": 0.042745679463576804,
      "soc_final": 0.5776486440139301,
      "soc_final_minus_initial": -0.022351355986069854,
      "unaccepted_fc_kwh": 0.0,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.522227783061224,
      "fc_loss": 0.0001434360749754615,
      "batt_loss": 0.00046901508513810255
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.5776486440139301,
      "soc_final_minus_initial": -0.022351355986069854,
      "soc_swing": 0.1033329103204752,
      "soc_mean": 0.608591370877483,
      "fc_power_kw_mean": 9.855238376195702,
      "fc_abs_ramp_kw_s_mean": 1.2217917655698105,
      "fc_on_pct": 74.16448706771287,
      "fc_start_stop_count": 7,
      "fc_start_stop_soh_loss": 0.0001372,
      "fc_low_power_count": 678,
      "fc_low_power_soh_loss": 2.3729999999999996e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 4,
      "fc_load_change_soh_loss": 2.3720000000000003e-06,
      "battery_throughput_kwh": 4.26299916139816,
      "battery_ohmic_loss_kw_integral_kwh": 0.2055063882301972,
      "fc_low_output_pct": 39.37808776518454,
      "fc_regeneration_energy_kwh": 0.6178704224733306,
      "fc_energy_efficiency": 0.507457121033949
    },
    "regimes": {
      "available": true,
      "groups": {
        "stopped": {
          "steps": 408,
          "available": true,
          "duration_s": 408.0,
          "hydrogen_g": 6.098756949610739,
          "fc_energy_kwh": 0.06888597520778209,
          "fc_energy_efficiency": 0.3388864242177843,
          "fc_low_output_pct": 20.588235294117645,
          "battery_throughput_kwh": 0.050882331185136555,
          "battery_ohmic_loss_kwh": 0.0005593326544359664,
          "soc_mean": 0.6370984588706933,
          "soc_delta": 0.03092862274807029
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 84.11022668311922,
          "fc_energy_kwh": 1.377717709890936,
          "fc_energy_efficiency": 0.4914463614388332,
          "fc_low_output_pct": 45.637119113573405,
          "battery_throughput_kwh": 0.8092733187436295,
          "battery_ohmic_loss_kwh": 0.017677134552075893,
          "soc_mean": 0.6182397956574345,
          "soc_delta": -0.12922202103733726
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 207.16541990768883,
          "fc_energy_kwh": 3.5361014721674118,
          "fc_energy_efficiency": 0.512120476369318,
          "fc_low_output_pct": 25.213270142180093,
          "battery_throughput_kwh": 1.8244561330050382,
          "battery_ohmic_loss_kwh": 0.09733479042926174,
          "soc_mean": 0.6077439865919851,
          "soc_delta": -1.1179537579548193
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 44.13869509781211,
          "fc_energy_kwh": 0.6178704224733306,
          "fc_energy_efficiency": 0.41999353242696796,
          "fc_low_output_pct": 76.36632200886262,
          "battery_throughput_kwh": 1.6286160509635785,
          "battery_ohmic_loss_kwh": 0.09510421128027824,
          "soc_mean": 0.6170530965803704,
          "soc_delta": 0.9527934349185635
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 295.21986880536116,
          "fc_energy_kwh": 5.094065697497729,
          "fc_energy_efficiency": 0.517706532656048,
          "fc_low_output_pct": 14.425162689804772,
          "battery_throughput_kwh": 0.7487375747775823,
          "battery_ohmic_loss_kwh": 0.019361372103325346,
          "soc_mean": 0.5879087000228408,
          "soc_delta": 0.059503462502564
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
    "parent_reward_id": "187b8f1ea4ae4ba8b0855af8f8741a1c4860a183c03e810145cc6243e5570d4e",
    "selection_reason": "fuel_leader: rank 1 of 3"
  },
  "candidate": {
    "candidate_id": "c1cb0fb6fc6313d594c06d75fd28148cd59afeee0e5a85068f05010b7067a4ba",
    "seed": 1,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.771970924700257,
      "fc_loss": 0.0002760774999639448,
      "batt_loss": 0.0004370954060959331,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5505518427863599,
      "soc_max": 0.6406775932365727
    },
    "operating_cost": {
      "h2_usd": 7.540379647290179,
      "fc_usd": 34.804308426479274,
      "batt_usd": 3.4356232240079727,
      "degradation_usd": 38.23993165048725,
      "total_usd": 45.78031129777743,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.843180895962197,
      "soc_correction_gkm": -0.0712099712619406,
      "soc_final": 0.63697230899,
      "soc_final_minus_initial": 0.036972308990000036,
      "unaccepted_fc_kwh": 0.00101039305482863,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.804009922244944,
      "fc_loss": 0.0002618748374615315,
      "batt_loss": 0.00045437877706424603
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.63697230899,
      "soc_final_minus_initial": 0.036972308990000036,
      "soc_swing": 0.09012575045021276,
      "soc_mean": 0.6009702688380721,
      "fc_power_kw_mean": 9.999981660904218,
      "fc_abs_ramp_kw_s_mean": 1.8219285594760801,
      "fc_on_pct": 80.67422260970648,
      "fc_start_stop_count": 13,
      "fc_start_stop_soh_loss": 0.0002548,
      "fc_low_power_count": 827,
      "fc_low_power_soh_loss": 2.8944999999999996e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 31,
      "fc_load_change_soh_loss": 1.8383e-05,
      "battery_throughput_kwh": 3.9421037445923877,
      "battery_ohmic_loss_kw_integral_kwh": 0.19691767465424784,
      "fc_low_output_pct": 48.21272885789015,
      "fc_regeneration_energy_kwh": 0.6111880543280431,
      "fc_energy_efficiency": 0.50102046905482
    },
    "regimes": {
      "available": true,
      "groups": {
        "stopped": {
          "steps": 408,
          "available": true,
          "duration_s": 408.0,
          "hydrogen_g": 2.520623042623157,
          "fc_energy_kwh": 0.029971305792389095,
          "fc_energy_efficiency": 0.3567487408769909,
          "fc_low_output_pct": 7.8431372549019605,
          "battery_throughput_kwh": 0.02298915010588698,
          "battery_ohmic_loss_kwh": 0.00047129430112767133,
          "soc_mean": 0.6349914656457515,
          "soc_delta": 0.013755530706200725
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 86.13452255654221,
          "fc_energy_kwh": 1.3560740761339858,
          "fc_energy_efficiency": 0.47235753685640675,
          "fc_low_output_pct": 56.371191135734065,
          "battery_throughput_kwh": 0.6613474219447196,
          "battery_ohmic_loss_kwh": 0.012310757359026387,
          "soc_mean": 0.6138696105848065,
          "soc_delta": -0.1467937626579957
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 224.43135917223475,
          "fc_energy_kwh": 3.8187766990519108,
          "fc_energy_efficiency": 0.5105113602216091,
          "fc_low_output_pct": 42.93838862559242,
          "battery_throughput_kwh": 1.6711888478107868,
          "battery_ohmic_loss_kwh": 0.090929405198254,
          "soc_mean": 0.5997923804015133,
          "soc_delta": -0.9705430183566335
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 46.91073221182245,
          "fc_energy_kwh": 0.6111880543280431,
          "fc_energy_efficiency": 0.39090149551657644,
          "fc_low_output_pct": 85.67208271787297,
          "battery_throughput_kwh": 1.6156094345859073,
          "battery_ohmic_loss_kwh": 0.09611627970822373,
          "soc_mean": 0.610246242705846,
          "soc_delta": 0.9453427698569689
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 296.8441311468796,
          "fc_energy_kwh": 5.085467154339873,
          "fc_energy_efficiency": 0.5140046797218139,
          "fc_low_output_pct": 14.533622559652928,
          "battery_throughput_kwh": 0.5993959354711302,
          "battery_ohmic_loss_kwh": 0.014553536962275947,
          "soc_mean": 0.5745784672287723,
          "soc_delta": 0.06186957432762785
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
    "total_cost_delta_usd": 16.810656973679905,
    "cost_delta_usd": {
      "h2_usd": 0.12530935262593346,
      "fc_usd": 16.909704341695083,
      "batt_usd": -0.22435672064111456
    },
    "soc_drift": 0.036972308990000036,
    "fuel_delta_gkm": 0.17901336089419218,
    "fc_loss_delta": 0.00013413249999338905,
    "batt_loss_delta": -2.8543668943004086e-05,
    "guards": {
      "reference": "baseline",
      "max_fuel_increase_fraction": 0.05,
      "max_batt_increase_fraction": 0.1,
      "fuel_gkm_max": 11.18909967951321,
      "batt_loss_max": 0.0005969470490372886,
      "soc_drift_abs_max": 0.05
    },
    "guard_reference": "baseline",
    "comparison_basis": "matched_fresh_training",
    "total_cost_delta_usd_vs_baseline": 5.36777378507027,
    "fuel_delta_gkm_vs_baseline": 0.1156855156400578,
    "fc_loss_delta_vs_baseline": 4.851933332050695e-05,
    "batt_loss_delta_vs_baseline": -0.00010558372939251104
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
        "mean": 10.804009922244944,
        "std": 0.06774716962689131,
        "slope_per_10_episodes": 0.01625138494072274,
        "ep399_better_than_fraction": 0.675
      },
      "fc_loss": {
        "n": 40,
        "mean": 0.0002618748374615315,
        "std": 2.7458862879927877e-05,
        "slope_per_10_episodes": 4.647142119104088e-06,
        "ep399_better_than_fraction": 0.25
      },
      "batt_loss": {
        "n": 40,
        "mean": 0.00045437877706424603,
        "std": 8.00202131715968e-06,
        "slope_per_10_episodes": -3.7046406630271244e-06,
        "ep399_better_than_fraction": 0.975
      }
    },
    "lucky_checkpoint": false
  },
  "reward_diff": "--- parent:187b8f1ea4ae\n+++ candidate\n@@ -11,16 +11,26 @@\n     term_soc_anchor = w_soc_eff * soc_err\n     self.info[\"term_soc_anchor\"] = float(term_soc_anchor)\n \n-    # Catalog term: drift_barrier (ADDED per orchestrator; symmetric quadratic barrier around SOC_init)\n+    # Catalog term: drift_barrier (existing in edit_base; symmetric quadratic barrier around SOC_init)\n     soc_init = float(self.SOC_init)\n-    d0 = 0.03  # deadband (< soc_drift_abs_max=0.05), keeps small drift cheap but prices guard-violating drift\n+    d0 = 0.03  # deadband (< soc_drift_abs_max=0.05)\n     p = 2.0\n     drift_excess = float(np.maximum(0.0, np.abs(soc - soc_init) - d0))\n-    c_drift = 20000.0  # sized to be several units/step when |drift| approaches the guard\n+    c_drift = 20000.0\n     term_drift_barrier = c_drift * (drift_excess ** p)\n     self.info[\"term_drift_barrier\"] = float(term_drift_barrier)\n \n-    soc_cost = float(term_soc_anchor + term_drift_barrier)\n+    # Catalog term: fc_peak_shave (ADDED; charge_sustaining; SOC-gated FC peak cap)\n+    # c * g(SOC) * max(0, P_FCS - P_cap), with g=0 at/below SOC_target-m and nondecreasing\n+    P_fcs_kw = float(self.P_FCS)\n+    P_cap = 12.0  # near the peak-efficiency band (10-15 kW); must be >= 8 kW\n+    m = 0.05\n+    g_soc = float(np.clip((soc - (soc_tgt - m)) / m, 0.0, 1.0))\n+    c_peak = 0.7  # sized so added drift-step cost is O(1e3-1e4) on the baseline replay, not just the MINIMUM\n+    term_fc_peak_shave = c_peak * g_soc * float(np.maximum(0.0, P_fcs_kw - P_cap))\n+    self.info[\"term_fc_peak_shave\"] = float(term_fc_peak_shave)\n+\n+    soc_cost = float(term_soc_anchor + term_drift_barrier + term_fc_peak_shave)\n \n     # ---------- Core operating-cost proxy terms (existing) ----------\n     h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal\n@@ -30,7 +40,6 @@\n \n     # ---------- Extra catalog price terms (existing in edit_base): fc_efficiency_gap, batt_ohmic ----------\n     # Catalog term: fc_efficiency_gap\n-    P_fcs_kw = float(self.P_FCS)\n     h2_fcs_g = float(h2_fcs)\n     eta_ref = 0.602  # peak measured band (10-15 kW) from EFFICIENCY FACTS\n     eta = float(P_fcs_kw / (120.0 * h2_fcs_g)) if h2_fcs_g > 0.0 else 0.0\n"
}
```

[Training log](results/aroma_runs/seed1_obscur_20261018_061824_704722118/search/20261018_061824_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed1_obscur_seq_v3_catalog_iter6/trials/25d731f24baf083038d76165/iter_001/train_log.log)
[Evaluation records](results/aroma_runs/seed1_obscur_20261018_061824_704722118/search/20261018_061824_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed1_obscur_seq_v3_catalog_iter6/trials/25d731f24baf083038d76165/deterministic_evaluations.jsonl)
