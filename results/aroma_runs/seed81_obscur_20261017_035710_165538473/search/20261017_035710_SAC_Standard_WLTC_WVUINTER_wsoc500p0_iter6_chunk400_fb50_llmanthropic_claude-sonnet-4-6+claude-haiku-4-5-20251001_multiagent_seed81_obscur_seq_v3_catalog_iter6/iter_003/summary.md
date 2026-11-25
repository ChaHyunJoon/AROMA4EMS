# Iteration 3

Decision: **retain_champion**

```json
{
  "iteration": 3,
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
    "iteration": 3
  },
  "edit_base": {
    "mode": "fuel_leader",
    "parent_reward_id": "17afbf80420cb9f947efdaac72a30bf9687444a44fa8df43fcfaa7ace533d083",
    "selection_reason": "fuel_leader: rank 1 of 2"
  },
  "candidate": {
    "candidate_id": "708790971f014bd8944f780e97f2cf0c3c2c9fce56c4e7bfdf3475d45b244a93",
    "seed": 81,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.799665982804488,
      "fc_loss": 0.00027744549996167045,
      "batt_loss": 0.00043181538769143657,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5214398328965935,
      "soc_max": 0.631791203737554
    },
    "operating_cost": {
      "h2_usd": 7.559766187963142,
      "fc_usd": 34.976768311310465,
      "batt_usd": 3.3941216351084167,
      "degradation_usd": 38.370889946418885,
      "total_usd": 45.930656134382026,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.842452428475918,
      "soc_correction_gkm": -0.04278644567143191,
      "soc_final": 0.6220533135687406,
      "soc_final_minus_initial": 0.02205331356874063,
      "unaccepted_fc_kwh": 0.0,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.818046680835934,
      "fc_loss": 0.00028804448745967657,
      "batt_loss": 0.0004221960868024871
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.6220533135687406,
      "soc_final_minus_initial": 0.02205331356874063,
      "soc_swing": 0.11035137084096058,
      "soc_mean": 0.5861451429753994,
      "fc_power_kw_mean": 9.966075672830543,
      "fc_abs_ramp_kw_s_mean": 1.9483727668488828,
      "fc_on_pct": 82.50508573089218,
      "fc_start_stop_count": 13,
      "fc_start_stop_soh_loss": 0.0002548,
      "fc_low_power_count": 879,
      "fc_low_power_soh_loss": 3.0765e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 33,
      "fc_load_change_soh_loss": 1.9569000000000002e-05,
      "battery_throughput_kwh": 3.9366308906715917,
      "battery_ohmic_loss_kw_integral_kwh": 0.19636399054527573,
      "fc_low_output_pct": 49.869224062772446,
      "fc_regeneration_energy_kwh": 0.6239376304036133,
      "fc_energy_efficiency": 0.5002134240506734
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
          "battery_ohmic_loss_kwh": 4.015959815573666e-08,
          "soc_mean": 0.6191301085071045,
          "soc_delta": -0.00012419345284298
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 91.6035654452397,
          "fc_energy_kwh": 1.4258042700005227,
          "fc_energy_efficiency": 0.46699498794271854,
          "fc_low_output_pct": 58.86426592797784,
          "battery_throughput_kwh": 0.5326538756971595,
          "battery_ohmic_loss_kwh": 0.009285163626232919,
          "soc_mean": 0.5988341898305274,
          "soc_delta": -0.11037013710821109
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 228.56969365485548,
          "fc_energy_kwh": 3.9000861186203695,
          "fc_energy_efficiency": 0.5119413825868077,
          "fc_low_output_pct": 49.763033175355446,
          "battery_throughput_kwh": 1.5860578430100916,
          "battery_ohmic_loss_kwh": 0.08623601432781956,
          "soc_mean": 0.5877441273435069,
          "soc_delta": -0.9329122807721659
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 47.187005480349235,
          "fc_energy_kwh": 0.6239376304036133,
          "fc_energy_efficiency": 0.39671940869389266,
          "fc_low_output_pct": 85.22895125553914,
          "battery_throughput_kwh": 1.627508470548657,
          "battery_ohmic_loss_kwh": 0.09720496670653435,
          "soc_mean": 0.5969526312319415,
          "soc_delta": 0.9541996530257336
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 291.4514030568742,
          "fc_energy_kwh": 4.990223425981502,
          "fc_energy_efficiency": 0.5137105993540985,
          "fc_low_output_pct": 17.787418655097614,
          "battery_throughput_kwh": 0.7382945115581396,
          "battery_ohmic_loss_kwh": 0.022174430981873276,
          "soc_mean": 0.5564077896165326,
          "soc_delta": -0.00033159243340352695
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
    "total_cost_delta_usd": 13.87791676496498,
    "cost_delta_usd": {
      "h2_usd": -0.14911698285091113,
      "fc_usd": 14.147824839144135,
      "batt_usd": -0.12079109132824284
    },
    "soc_drift": 0.02205331356874063,
    "fuel_delta_gkm": -0.2130242612155886,
    "fc_loss_delta": 0.00011222450001469042,
    "batt_loss_delta": -1.536758476539113e-05,
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
    "total_cost_delta_usd_vs_baseline": 10.010074989344538,
    "fuel_delta_gkm_vs_baseline": -0.03839666135978348,
    "fc_loss_delta_vs_baseline": 9.098099999094167e-05,
    "batt_loss_delta_vs_baseline": -0.0001822827061359611
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
        "mean": 10.818046680835934,
        "std": 0.022579310533316615,
        "slope_per_10_episodes": -0.011539751332672018,
        "ep399_better_than_fraction": 0.85
      },
      "fc_loss": {
        "n": 40,
        "mean": 0.00028804448745967657,
        "std": 2.1272716862796923e-05,
        "slope_per_10_episodes": -2.560464820558506e-06,
        "ep399_better_than_fraction": 0.65
      },
      "batt_loss": {
        "n": 40,
        "mean": 0.0004221960868024871,
        "std": 1.0895434150710392e-05,
        "slope_per_10_episodes": 7.391605521841984e-06,
        "ep399_better_than_fraction": 0.225
      }
    },
    "lucky_checkpoint": false
  },
  "reward_diff": "--- parent:17afbf80420c\n+++ candidate\n@@ -1,30 +1,89 @@\n def get_reward(self):\n     soc = float(self.SOC)\n     soc_low, soc_high = self.soc_bounds\n-    # SOC deviation from target\n-    soc_err = (np.abs(soc - self.SOC_target)) ** 2\n-    w_soc = np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10, self.w_soc)\n-    soc_cost = w_soc * soc_err\n+    soc_init = float(self.SOC_init)\n+    soc_target = float(self.SOC_target)\n \n-    h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal\n-    h2_cost = self.w_h2 * h2_fcs\n-    # Cost of fuel cell degradation (scaled)\n+    # ── term_soc_anchor (catalog: soc_anchor, symmetric quadratic, same shape as edit base) ──\n+    soc_err = (soc - soc_target) ** 2\n+    w_soc_step = np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10.0, self.w_soc)\n+    term_soc_anchor = float(w_soc_step * soc_err)\n+\n+    # ── term_drift_barrier (catalog: drift_barrier) ──\n+    # Flat inside |SOC - SOC_init| <= 0.025, quadratic beyond.\n+    # c=60, d0=0.025, p=2.\n+    # Sizing: at mean drift 0.06 over 2778 steps → 60*(0.06-0.025)^2 * 2778 ≈ 204 reward units.\n+    # Checked: zero at |SOC-SOC_init|=0.01 ✓, positive at guard edge 0.05 ✓, nondecreasing ✓.\n+    c_barrier = 60.0\n+    d0_barrier = 0.025\n+    soc_abs_dev = float(np.abs(soc - soc_init))\n+    barrier_excess = float(np.maximum(0.0, soc_abs_dev - d0_barrier))\n+    term_drift_barrier = c_barrier * barrier_excess ** 2\n+\n+    # ── term_fc_surplus_charge (catalog: fc_surplus_charge) ──\n+    # Price FC power flowing into the battery when SOC > SOC_target.\n+    # g(SOC) = max(0, SOC - SOC_target + m) / m, m=0.05; ramps 0→1 from SOC=0.55 to SOC=0.65.\n+    # P_fc_to_batt_kw = max(0, min(-P_batt, P_mot - P_batt)) / 1000\n+    # c=0.8; at mean FC->batt 3.37 kW, g≈1, ~1000 steps above target: ~2696 reward units.\n+    # Checked: zero while discharging ✓, zero for pure regen ✓,\n+    #          zero at SOC_target-0.1=0.50 ✓, positive at SOC_target+0.05 with FC charging ✓,\n+    #          nondecreasing in SOC and FC charging power ✓.\n+    m_surplus = 0.05\n+    g_surplus = float(np.maximum(0.0, soc - soc_target + m_surplus) / m_surplus)\n+    p_batt_w = float(self.P_batt)       # W, + = discharge\n+    p_mot_w = float(self.P_mot)         # W, motor electrical power\n+    p_fc_to_batt_kw = float(np.maximum(0.0, np.minimum(-p_batt_w, p_mot_w - p_batt_w))) / 1000.0\n+    c_surplus = 0.8\n+    term_fc_surplus_charge = c_surplus * g_surplus * p_fc_to_batt_kw\n+\n+    # ── soc_cost = sum of all charge-sustaining terms ──\n+    soc_cost = term_soc_anchor + term_drift_barrier + term_fc_surplus_charge\n+\n+    # ── standard price terms ──\n+    h2_fcs = self.h2_fcs\n+    h2_batt = self.h2_batt\n+    h2_equal = self.h2_equal\n+    h2_cost = self.w_h2 * float(h2_fcs)\n     fcs_soh_cost = self.w_fc * float(self.dSOH_FCS)\n-    # Cost of battery degradation (scaled)\n     batt_soh_cost = self.w_batt * float(self.dSOH_batt)\n \n+    # ── term_fc_efficiency_gap (catalog: fc_efficiency_gap, NEW — not in edit base or champion) ──\n+    # Price hydrogen burned below the FC's peak efficiency (eta_ref=0.602 at 10-15 kW).\n+    # eta = P_FCS / (120 * h2_fcs) when h2_fcs > 0, else 0.\n+    # c=40; at 4 kW (eta=0.484, gap=0.196, h2_fcs≈0.0267 g/step): 40*0.0267*0.196/0.602≈0.347/step.\n+    # At 2 kW (eta=0.213, gap=0.646, h2_fcs≈0.0117 g/step): 40*0.0117*0.646/0.602≈0.501/step.\n+    # Mean over 1038 low-efficiency steps ≈ 0.40/step → ~416 reward units total.\n+    # Mean over full episode ≈ 0.12/step (within price-deviation tolerance).\n+    # Incentivizes FC to operate at 8-15 kW efficient band or turn off, reducing fc_low_power_soh_loss.\n+    # Checked: zero with FC off (h2_fcs=0) ✓, zero at eta>=eta_ref ✓, nonnegative ✓,\n+    #          nonincreasing in eta at fixed hydrogen ✓, enters objective_cost ✓.\n+    eta_ref = 0.602\n+    c_eff_gap = 40.0\n+    p_fcs_kw = float(self.P_FCS)\n+    h2_fcs_val = float(h2_fcs)\n+    # eta = P_FCS / (120 * h2_fcs); 120 kJ/g is H2 LHV, 1-s steps\n+    eta_fc = "
}
```

[Training log](results/aroma_runs/seed81_obscur_20261017_035710_165538473/search/20261017_035710_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed81_obscur_seq_v3_catalog_iter6/trials/a58534518dbcceb28e7a8e2a/iter_001/train_log.log)
[Evaluation records](results/aroma_runs/seed81_obscur_20261017_035710_165538473/search/20261017_035710_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed81_obscur_seq_v3_catalog_iter6/trials/a58534518dbcceb28e7a8e2a/deterministic_evaluations.jsonl)
