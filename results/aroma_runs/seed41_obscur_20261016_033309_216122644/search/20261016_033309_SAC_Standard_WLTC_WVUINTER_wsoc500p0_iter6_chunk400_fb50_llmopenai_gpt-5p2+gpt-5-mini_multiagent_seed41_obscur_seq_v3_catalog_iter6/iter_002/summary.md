# Iteration 2

Decision: **retain_champion**

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
  "decision": "retain_champion",
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
    "candidate_id": "fd453666c82582ad9c860a7d45df21f0efbe27b757448de0bce5c2349df38b3a",
    "seed": 41,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.945460379927066,
      "fc_loss": 0.00030301949995370503,
      "batt_loss": 0.0005413132853631097,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5538427837676912,
      "soc_max": 0.6655720038700221
    },
    "operating_cost": {
      "h2_usd": 7.661822265948946,
      "fc_usd": 38.20081005153846,
      "batt_usd": 4.254788471168191,
      "degradation_usd": 42.45559852270665,
      "total_usd": 50.1174207886556,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 11.05026122353892,
      "soc_correction_gkm": -0.10480084361185185,
      "soc_final": 0.6538578325032303,
      "soc_final_minus_initial": 0.053857832503230285,
      "unaccepted_fc_kwh": 0.0006613278440604237,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.940524808732565,
      "fc_loss": 0.0002731802249534454,
      "batt_loss": 0.0005391565545619009
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.6538578325032303,
      "soc_final_minus_initial": 0.053857832503230285,
      "soc_swing": 0.11172922010233088,
      "soc_mean": 0.6080677828599724,
      "fc_power_kw_mean": 10.14372014471417,
      "fc_abs_ramp_kw_s_mean": 1.8823573863121879,
      "fc_on_pct": 85.12060447544319,
      "fc_start_stop_count": 14,
      "fc_start_stop_soh_loss": 0.0002744,
      "fc_low_power_count": 1061,
      "fc_low_power_soh_loss": 3.7135e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 42,
      "fc_load_change_soh_loss": 2.4906e-05,
      "battery_throughput_kwh": 5.002777123330118,
      "battery_ohmic_loss_kw_integral_kwh": 0.2592116338539529,
      "fc_low_output_pct": 51.81633246149375,
      "fc_regeneration_energy_kwh": 0.673882467790042,
      "fc_energy_efficiency": 0.49873723503234124
    },
    "regimes": {
      "available": true,
      "groups": {
        "stopped": {
          "steps": 408,
          "available": true,
          "duration_s": 408.0,
          "hydrogen_g": 11.644219868286825,
          "fc_energy_kwh": 0.1932182651594675,
          "fc_energy_efficiency": 0.4978545349645388,
          "fc_low_output_pct": 28.676470588235293,
          "battery_throughput_kwh": 0.1567209177897611,
          "battery_ohmic_loss_kwh": 0.003707966794558852,
          "soc_mean": 0.6514262354831251,
          "soc_delta": 0.09450530073153318
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 108.1773762205656,
          "fc_energy_kwh": 1.7222715567950728,
          "fc_energy_efficiency": 0.47767209596485016,
          "fc_low_output_pct": 59.97229916897508,
          "battery_throughput_kwh": 0.9646279645481209,
          "battery_ohmic_loss_kwh": 0.021147679152868123,
          "soc_mean": 0.6256733881311606,
          "soc_delta": 0.04108248586527008
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 200.1980521247682,
          "fc_energy_kwh": 3.3145185400044967,
          "fc_energy_efficiency": 0.49673560603992856,
          "fc_low_output_pct": 52.60663507109005,
          "battery_throughput_kwh": 2.1375681641470794,
          "battery_ohmic_loss_kwh": 0.13569341158772313,
          "soc_mean": 0.6067012515237769,
          "soc_delta": -1.2847910761165329
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 49.38648809070447,
          "fc_energy_kwh": 0.673882467790042,
          "fc_energy_efficiency": 0.40939327060785924,
          "fc_low_output_pct": 87.44460856720828,
          "battery_throughput_kwh": 1.6692767832495574,
          "battery_ohmic_loss_kwh": 0.09710311493891921,
          "soc_mean": 0.619511683996013,
          "soc_delta": 0.9772372235533905
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 297.74098111966106,
          "fc_energy_kwh": 5.1652889049139326,
          "fc_energy_efficiency": 0.5204999458962313,
          "fc_low_output_pct": 12.364425162689804,
          "battery_throughput_kwh": 1.1849015077102345,
          "battery_ohmic_loss_kwh": 0.04703181341154351,
          "soc_mean": 0.57362142828625,
          "soc_delta": 0.08057752636699633
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
      "total_cost_strictly_improved": true,
      "charge_sustaining": false,
      "fuel_within_guard": true,
      "battery_within_guard": true
    },
    "checkpoint_episode": 399,
    "cost_unit": "USD per 100 km",
    "total_cost_delta_usd": -2.817933928574874,
    "cost_delta_usd": {
      "h2_usd": -0.22561211785544355,
      "fc_usd": -2.3233548622724953,
      "batt_usd": -0.2689669484469386
    },
    "soc_drift": 0.053857832503230285,
    "fuel_delta_gkm": -0.32230302550777523,
    "fc_loss_delta": -1.842949999308896e-05,
    "batt_loss_delta": -3.421918234114418e-05,
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
        "mean": 10.940524808732565,
        "std": 0.02534802721755073,
        "slope_per_10_episodes": -0.007493570532624257,
        "ep399_better_than_fraction": 0.375
      },
      "fc_loss": {
        "n": 40,
        "mean": 0.0002731802249534454,
        "std": 3.207254634012561e-05,
        "slope_per_10_episodes": 2.5052908069166517e-06,
        "ep399_better_than_fraction": 0.15
      },
      "batt_loss": {
        "n": 40,
        "mean": 0.0005391565545619009,
        "std": 7.32050618607468e-06,
        "slope_per_10_episodes": 8.78291723944876e-08,
        "ep399_better_than_fraction": 0.35
      }
    },
    "lucky_checkpoint": false
  },
  "reward_diff": "--- parent:17afbf80420c\n+++ candidate\n@@ -1,30 +1,60 @@\n def get_reward(self):\n     soc = float(self.SOC)\n     soc_low, soc_high = self.soc_bounds\n-    # SOC deviation from target\n-    soc_err = (np.abs(soc - self.SOC_target)) ** 2\n-    w_soc = np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10, self.w_soc)\n-    soc_cost = w_soc * soc_err\n \n+    # -----------------------\n+    # Charge-sustaining terms (must sum into soc_cost)\n+    # -----------------------\n+    # term_soc_anchor (catalog: soc_anchor) — baseline symmetric quadratic anchor to SOC_target,\n+    # with 10x penalty only when outside SOC operating bounds.\n+    soc_err = float(np.abs(soc - float(self.SOC_target))) ** 2\n+    w_soc_eff = float(np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10.0, self.w_soc))\n+    term_soc_anchor = w_soc_eff * soc_err\n+\n+    # term_drift_barrier (catalog: drift_barrier) — quadratic barrier beyond a deadband around SOC_init.\n+    # Sized to materially penalize the measured persistent drift (+0.185) per-step (terminal-only is too discounted).\n+    d0 = 0.025  # deadband half-width (must be < soc_drift_abs_max=0.05)\n+    p = 2.0\n+    c_drift = 1100.0  # reward-units per (SOC^2)-step beyond deadband (sized to land ~6.8k–8k total on the baseline drifted rollout)\n+    drift_excess = max(0.0, abs(soc - float(self.SOC_init)) - d0)\n+    term_drift_barrier = c_drift * (drift_excess ** p)\n+\n+    soc_cost = term_soc_anchor + term_drift_barrier\n+\n+    # -----------------------\n+    # Price-aligned operating-cost proxy terms (unchanged structure)\n+    # -----------------------\n     h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal\n-    h2_cost = self.w_h2 * h2_fcs\n-    # Cost of fuel cell degradation (scaled)\n-    fcs_soh_cost = self.w_fc * float(self.dSOH_FCS)\n-    # Cost of battery degradation (scaled)\n-    batt_soh_cost = self.w_batt * float(self.dSOH_batt)\n+    h2_cost = float(self.w_h2) * float(h2_fcs)\n+\n+    fcs_soh_cost = float(self.w_fc) * float(self.dSOH_FCS)\n+    batt_soh_cost = float(self.w_batt) * float(self.dSOH_batt)\n \n     in_bounds = (soc_low < soc < soc_high)\n+\n     objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost\n     reward = float(-objective_cost)\n \n-    self.info.update({'EMS_reward': reward,\n-                      'h2_fcs': float(h2_fcs),\n-                      'h2_batt': float(h2_batt),\n-                      'h2_equal': float(h2_equal),\n-                      'soc_cost': float(soc_cost),\n-                      'h2_cost': float(h2_cost),\n-                      'fcs_soh_cost': float(fcs_soh_cost),\n-                      'batt_soh_cost': float(batt_soh_cost),\n-                      'objective_cost': float(objective_cost),\n-                      'soc_in_bounds': int(in_bounds)})\n+    # -----------------------\n+    # Required logging (log every catalog term as term_<id>)\n+    # -----------------------\n+    self.info.update({\n+        'EMS_reward': reward,\n+        'h2_fcs': float(h2_fcs),\n+        'h2_batt': float(h2_batt),\n+        'h2_equal': float(h2_equal),\n+\n+        # catalog terms\n+        'term_soc_anchor': float(term_soc_anchor),\n+        'term_drift_barrier': float(term_drift_barrier),\n+\n+        # aggregated costs\n+        'soc_cost': float(soc_cost),\n+        'h2_cost': float(h2_cost),\n+        'fcs_soh_cost': float(fcs_soh_cost),\n+        'batt_soh_cost': float(batt_soh_cost),\n+        'objective_cost': float(objective_cost),\n+\n+        'soc_in_bounds': int(in_bounds),\n+    })\n     return reward\n"
}
```

[Training log](results/aroma_runs/seed41_obscur_20261016_033309_216122644/search/20261016_033309_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed41_obscur_seq_v3_catalog_iter6/trials/dd5993032a93a39733720b9b/iter_001/train_log.log)
[Evaluation records](results/aroma_runs/seed41_obscur_20261016_033309_216122644/search/20261016_033309_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed41_obscur_seq_v3_catalog_iter6/trials/dd5993032a93a39733720b9b/deterministic_evaluations.jsonl)
