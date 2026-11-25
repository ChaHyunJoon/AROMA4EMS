# Iteration 3

Decision: **retain_champion**

```json
{
  "iteration": 3,
  "control": {
    "candidate_id": "243cb08ab6af4c489bb4a513e82ca38174951dc2f56886c576a0b2e2e076b4bf",
    "seed": 1,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.725808877679976,
      "fc_loss": 0.00014844199996344454,
      "batt_loss": 0.0004703077050141058,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5018469924487504,
      "soc_max": 0.6313275900293815
    },
    "operating_cost": {
      "h2_usd": 7.508066214375983,
      "fc_usd": 18.71366247103032,
      "batt_usd": 3.6966759458957097,
      "degradation_usd": 22.41033841692603,
      "total_usd": 29.918404631302014,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.668283016490335,
      "soc_correction_gkm": 0.05752586118963991,
      "soc_final": 0.5702960217167853,
      "soc_final_minus_initial": -0.029703978283214694,
      "unaccepted_fc_kwh": 0.0,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.787422428223394,
      "fc_loss": 0.0001620712874608049,
      "batt_loss": 0.00048301075411801285
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.5702960217167853,
      "soc_final_minus_initial": -0.029703978283214694,
      "soc_swing": 0.12948059758063113,
      "soc_mean": 0.5768961336390546,
      "fc_power_kw_mean": 9.852657796228327,
      "fc_abs_ramp_kw_s_mean": 1.5006545312895228,
      "fc_on_pct": 72.36268526591107,
      "fc_start_stop_count": 7,
      "fc_start_stop_soh_loss": 0.0001372,
      "fc_low_power_count": 840,
      "fc_low_power_soh_loss": 2.9399999999999994e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 14,
      "fc_load_change_soh_loss": 8.302e-06,
      "battery_throughput_kwh": 4.342139311944416,
      "battery_ohmic_loss_kw_integral_kwh": 0.21966407495545923,
      "fc_low_output_pct": 36.38477186864284,
      "fc_regeneration_energy_kwh": 0.4981306110001591,
      "fc_energy_efficiency": 0.5011170624562508
    },
    "regimes": {
      "available": true,
      "groups": {
        "stopped": {
          "steps": 408,
          "available": true,
          "duration_s": 408.0,
          "hydrogen_g": 0.7236432513720152,
          "fc_energy_kwh": 0.005709424372376875,
          "fc_energy_efficiency": 0.23671866051765203,
          "fc_low_output_pct": 2.696078431372549,
          "battery_throughput_kwh": 0.003987026252458165,
          "battery_ohmic_loss_kwh": 2.837797650052858e-05,
          "soc_mean": 0.5916603657892554,
          "soc_delta": 0.002217751743423202
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 76.03984788493781,
          "fc_energy_kwh": 1.1858715658114998,
          "fc_energy_efficiency": 0.46790868123089985,
          "fc_low_output_pct": 40.30470914127424,
          "battery_throughput_kwh": 0.7825670038875701,
          "battery_ohmic_loss_kwh": 0.019608008872046057,
          "soc_mean": 0.5828876805772915,
          "soc_delta": -0.23123022965787354
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 220.38456353735307,
          "fc_energy_kwh": 3.7570413097912354,
          "fc_energy_efficiency": 0.5114809755075527,
          "fc_low_output_pct": 23.033175355450236,
          "battery_throughput_kwh": 1.9960529499032986,
          "battery_ohmic_loss_kwh": 0.1126804116438107,
          "soc_mean": 0.5757336859408861,
          "soc_delta": -1.0101679370907481
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 40.70883952299946,
          "fc_energy_kwh": 0.4981306110001591,
          "fc_energy_efficiency": 0.367129425609102,
          "fc_low_output_pct": 77.25258493353027,
          "battery_throughput_kwh": 1.5234783757616657,
          "battery_ohmic_loss_kwh": 0.08950753748053858,
          "soc_mean": 0.5826430488324731,
          "soc_delta": 0.8951258471443565
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 288.0947177366717,
          "fc_energy_kwh": 4.942058136886354,
          "fc_energy_efficiency": 0.5146799390445499,
          "fc_low_output_pct": 16.594360086767896,
          "battery_throughput_kwh": 0.9331601054663379,
          "battery_ohmic_loss_kwh": 0.0336285383920617,
          "soc_mean": 0.5629262846490506,
          "soc_delta": -0.03660153668027111
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
    "candidate_id": "f620dbe3ac6d20d738366cfb8048ad1a1ae672af29d2a7901ddd494df42c14ae",
    "seed": 1,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.825083492258189,
      "fc_loss": 0.0003627564999574284,
      "batt_loss": 0.00045505322881711496,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5215963962888979,
      "soc_max": 0.6300571642167309
    },
    "operating_cost": {
      "h2_usd": 7.577558444580733,
      "fc_usd": 45.73168443599105,
      "batt_usd": 3.576773901716009,
      "degradation_usd": 49.30845833770706,
      "total_usd": 56.88601678228779,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.854579623401976,
      "soc_correction_gkm": -0.02949613114378844,
      "soc_final": 0.615171490821696,
      "soc_final_minus_initial": 0.015171490821695999,
      "unaccepted_fc_kwh": 0.0,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.866872872651266,
      "fc_loss": 0.00034368618745487243,
      "batt_loss": 0.000463504741436932
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.615171490821696,
      "soc_final_minus_initial": 0.015171490821695999,
      "soc_swing": 0.10846076792783299,
      "soc_mean": 0.5842914957401709,
      "fc_power_kw_mean": 9.963668687019243,
      "fc_abs_ramp_kw_s_mean": 1.5822122140530048,
      "fc_on_pct": 81.19732635861668,
      "fc_start_stop_count": 18,
      "fc_start_stop_soh_loss": 0.0003528,
      "fc_low_power_count": 981,
      "fc_low_power_soh_loss": 3.4335e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 11,
      "fc_load_change_soh_loss": 6.523e-06,
      "battery_throughput_kwh": 4.2327872537726465,
      "battery_ohmic_loss_kw_integral_kwh": 0.20360239311858017,
      "fc_low_output_pct": 45.16129032258064,
      "fc_regeneration_energy_kwh": 0.5467319308882016,
      "fc_energy_efficiency": 0.4991727897833057
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
          "battery_ohmic_loss_kwh": 4.008767534378103e-08,
          "soc_mean": 0.6122779041834479,
          "soc_delta": -0.00012408771272975905
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 101.62430525617975,
          "fc_energy_kwh": 1.6148644171120592,
          "fc_energy_efficiency": 0.47676367842302775,
          "fc_low_output_pct": 50.48476454293629,
          "battery_throughput_kwh": 0.778682975968461,
          "battery_ohmic_loss_kwh": 0.020989059699594463,
          "soc_mean": 0.5962350101426399,
          "soc_delta": -0.006434051990723555
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 221.2473871617587,
          "fc_energy_kwh": 3.7411692666763114,
          "fc_energy_efficiency": 0.5073339128226031,
          "fc_low_output_pct": 47.39336492890995,
          "battery_throughput_kwh": 1.680063314939208,
          "battery_ohmic_loss_kwh": 0.08750151973452173,
          "soc_mean": 0.5866450634438168,
          "soc_delta": -1.0227404315295918
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 45.88411227212846,
          "fc_energy_kwh": 0.5467319308882016,
          "fc_energy_efficiency": 0.3575006134844367,
          "fc_low_output_pct": 83.45642540620383,
          "battery_throughput_kwh": 1.5605047817496254,
          "battery_ohmic_loss_kwh": 0.09064435684341543,
          "soc_mean": 0.5948596496007047,
          "soc_delta": 0.9164318612620312
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 288.6005997909306,
          "fc_energy_kwh": 5.035292497050773,
          "fc_energy_efficiency": 0.5234704377232579,
          "fc_low_output_pct": 3.68763557483731,
          "battery_throughput_kwh": 1.181661918081303,
          "battery_ohmic_loss_kwh": 0.0445807220125153,
          "soc_mean": 0.5544434558535538,
          "soc_delta": 0.008306801446857803
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
    "total_cost_delta_usd": 26.967612150985776,
    "cost_delta_usd": {
      "h2_usd": 0.06949223020474982,
      "fc_usd": 27.018021964960727,
      "batt_usd": -0.11990204417970052
    },
    "soc_drift": 0.015171490821695999,
    "fuel_delta_gkm": 0.09927461457821352,
    "fc_loss_delta": 0.0002143144999939839,
    "batt_loss_delta": -1.525447619699083e-05,
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
    "total_cost_delta_usd_vs_baseline": 16.47347926958063,
    "fuel_delta_gkm_vs_baseline": 0.1687980831979896,
    "fc_loss_delta_vs_baseline": 0.00013519833331399056,
    "batt_loss_delta_vs_baseline": -8.762590667132919e-05
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
        "mean": 10.866872872651266,
        "std": 0.04898831969351006,
        "slope_per_10_episodes": -0.033577382564434335,
        "ep399_better_than_fraction": 0.775
      },
      "fc_loss": {
        "n": 40,
        "mean": 0.00034368618745487243,
        "std": 4.033319502210656e-05,
        "slope_per_10_episodes": 1.137664118399097e-05,
        "ep399_better_than_fraction": 0.3
      },
      "batt_loss": {
        "n": 40,
        "mean": 0.000463504741436932,
        "std": 1.0410185476377982e-05,
        "slope_per_10_episodes": 2.5239270983256955e-06,
        "ep399_better_than_fraction": 0.825
      }
    },
    "lucky_checkpoint": false
  },
  "reward_diff": "--- parent:17afbf80420c\n+++ candidate\n@@ -1,30 +1,84 @@\n def get_reward(self):\n     soc = float(self.SOC)\n     soc_low, soc_high = self.soc_bounds\n-    # SOC deviation from target\n-    soc_err = (np.abs(soc - self.SOC_target)) ** 2\n-    w_soc = np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10, self.w_soc)\n-    soc_cost = w_soc * soc_err\n+    soc_target = float(self.SOC_target)\n+    soc_init = float(self.SOC_init)\n \n-    h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal\n-    h2_cost = self.w_h2 * h2_fcs\n-    # Cost of fuel cell degradation (scaled)\n-    fcs_soh_cost = self.w_fc * float(self.dSOH_FCS)\n-    # Cost of battery degradation (scaled)\n-    batt_soh_cost = self.w_batt * float(self.dSOH_batt)\n+    # --- term_soc_anchor [charge_sustaining, soc_anchor] ---\n+    # Symmetric quadratic anchor pulling SOC to target, x10 outside bounds.\n+    soc_err = (soc - soc_target) ** 2\n+    w_soc_step = float(np.where(\n+        (soc >= soc_high) | (soc <= soc_low),\n+        self.w_soc * 10.0,\n+        self.w_soc\n+    ))\n+    term_soc_anchor = float(w_soc_step * soc_err)\n \n-    in_bounds = (soc_low < soc < soc_high)\n-    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost\n+    # --- term_fc_surplus_charge [charge_sustaining, fc_surplus_charge] ---\n+    # Price FC power flowing into the battery when SOC is above SOC_target - m.\n+    # Catalog form: c * g(SOC) * P_fc_to_batt_kw\n+    # g = max(0, SOC - (SOC_target - m)) / m, linear from 0 at SOC_target-m upward\n+    # c = 0.70, m = 0.05\n+    _m_surplus = 0.05\n+    _c_surplus = 0.70\n+    _gate_surplus = float(np.maximum(0.0, soc - (soc_target - _m_surplus)) / _m_surplus)\n+    _p_batt_w = float(self.P_batt)       # W, + = discharge\n+    _p_mot_w = float(self.P_mot)         # W, motor electrical power\n+    # FC power into battery (kW): positive only when FC is charging battery\n+    _p_fc_to_batt_kw = float(\n+        np.maximum(0.0, np.minimum(-_p_batt_w, _p_mot_w - _p_batt_w)) / 1000.0\n+    )\n+    term_fc_surplus_charge = float(_c_surplus * _gate_surplus * _p_fc_to_batt_kw)\n+\n+    # soc_cost = sum of charge-sustaining terms\n+    soc_cost = term_soc_anchor + term_fc_surplus_charge\n+\n+    # --- h2_cost [price] ---\n+    h2_fcs = self.h2_fcs\n+    h2_batt = self.h2_batt\n+    h2_equal = self.h2_equal\n+    h2_cost = float(self.w_h2 * h2_fcs)\n+\n+    # --- fcs_soh_cost [price] ---\n+    fcs_soh_cost = float(self.w_fc * float(self.dSOH_FCS))\n+\n+    # --- batt_soh_cost [price] ---\n+    batt_soh_cost = float(self.w_batt * float(self.dSOH_batt))\n+\n+    # --- term_fc_efficiency_gap [price, fc_efficiency_gap] ---\n+    # Price hydrogen burned below the FC's efficient operating point.\n+    # Catalog form: c * h2_fcs * max(0, eta_ref - eta) / eta_ref\n+    # eta = P_FCS / (120 * h2_fcs) when h2_fcs > 0, else 0\n+    # eta_ref = 0.602 (peak efficiency at 10-15 kW from measured data)\n+    # c = 5.0\n+    _eta_ref = 0.602\n+    _c_eff = 5.0\n+    _h2_fcs_val = float(h2_fcs)\n+    _p_fcs_kw = float(self.P_FCS)\n+    # Guard against division by zero when FC is off (h2_fcs = 0)\n+    _eta = (_p_fcs_kw / (120.0 * _h2_fcs_val)) if _h2_fcs_val > 0.0 else _eta_ref\n+    _eff_gap = float(np.maximum(0.0, _eta_ref - _eta) / _eta_ref)\n+    term_fc_efficiency_gap = float(_c_eff * _h2_fcs_val * _eff_gap)\n+\n+    in_bounds = bool(soc_low < soc < soc_high)\n+\n+    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost + term_fc_efficiency_gap\n     reward = float(-objective_cost)\n \n-    self.info.update({'EMS_reward': reward,\n-                      'h2_fcs': float(h2_fcs),\n-                      'h2_batt': float(h2_batt),\n-                      'h2_equal': float(h2_equal),\n-                      'soc_cost': float(soc_cost),\n-                      'h2_cost': float(h2_cost),\n-                      'fcs_soh_cost': float(fcs_soh_cost),\n-                      'batt_soh_cost': float(batt_soh_cost),\n-                      'objective_cost': float(objective_cost),\n-                      'soc_i"
}
```

[Training log](results/aroma_runs/seed1_obscur_20261018_113049_381984490/search/20261018_113049_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed1_obscur_seq_v3_catalog_iter6/trials/0adf447ec53994d6c2e83e0e/iter_001/train_log.log)
[Evaluation records](results/aroma_runs/seed1_obscur_20261018_113049_381984490/search/20261018_113049_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed1_obscur_seq_v3_catalog_iter6/trials/0adf447ec53994d6c2e83e0e/deterministic_evaluations.jsonl)
