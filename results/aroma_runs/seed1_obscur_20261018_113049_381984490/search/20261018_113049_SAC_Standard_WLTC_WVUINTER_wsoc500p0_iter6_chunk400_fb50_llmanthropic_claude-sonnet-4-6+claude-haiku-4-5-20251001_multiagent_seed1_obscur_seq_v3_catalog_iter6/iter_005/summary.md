# Iteration 5

Decision: **retain_champion**

```json
{
  "iteration": 5,
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
    "iteration": 5
  },
  "edit_base": {
    "mode": "champion_improve",
    "parent_reward_id": "243cb08ab6af4c489bb4a513e82ca38174951dc2f56886c576a0b2e2e076b4bf",
    "selection_reason": "champion_improve: rank 1 of 1"
  },
  "candidate": {
    "candidate_id": "5ad74a2db6ee37574ab237eab766fd3e0581647dafde726cc1549328112eeb91",
    "seed": 1,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.672690978900759,
      "fc_loss": 0.00035644999996953253,
      "batt_loss": 0.0004675783512551046,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5146222301827066,
      "soc_max": 0.6556013285258075
    },
    "operating_cost": {
      "h2_usd": 7.470883685230531,
      "fc_usd": 44.93664184578003,
      "batt_usd": 3.675222892328499,
      "degradation_usd": 48.61186473810853,
      "total_usd": 56.08274842333906,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.700621462767506,
      "soc_correction_gkm": -0.027930483866748974,
      "soc_final": 0.614561079994109,
      "soc_final_minus_initial": 0.01456107999410905,
      "unaccepted_fc_kwh": 0.0,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.631884529455856,
      "fc_loss": 0.000392847024973228,
      "batt_loss": 0.00048335594595836083
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.614561079994109,
      "soc_final_minus_initial": 0.01456107999410905,
      "soc_swing": 0.14097909834310096,
      "soc_mean": 0.5839791356381101,
      "fc_power_kw_mean": 9.957488402662777,
      "fc_abs_ramp_kw_s_mean": 1.2745900260850989,
      "fc_on_pct": 77.70996803254869,
      "fc_start_stop_count": 18,
      "fc_start_stop_soh_loss": 0.0003528,
      "fc_low_power_count": 704,
      "fc_low_power_soh_loss": 2.4639999999999996e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 2,
      "fc_load_change_soh_loss": 1.1860000000000002e-06,
      "battery_throughput_kwh": 4.307190635841747,
      "battery_ohmic_loss_kw_integral_kwh": 0.21702186248965374,
      "fc_low_output_pct": 43.94071490845685,
      "fc_regeneration_energy_kwh": 0.5960565345415345,
      "fc_energy_efficiency": 0.5059444413199823
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
          "battery_ohmic_loss_kwh": 3.976186694446715e-08,
          "soc_mean": 0.6221685377944352,
          "soc_delta": -0.00012362602307802728
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 91.40648034914243,
          "fc_energy_kwh": 1.4652001884853456,
          "fc_energy_efficiency": 0.4809330971591477,
          "fc_low_output_pct": 49.23822714681441,
          "battery_throughput_kwh": 0.7604940389406167,
          "battery_ohmic_loss_kwh": 0.018148816164126627,
          "soc_mean": 0.5987163530562838,
          "soc_delta": -0.08536315972322106
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 206.36939079616482,
          "fc_energy_kwh": 3.5304830174496935,
          "fc_energy_efficiency": 0.5132790411559548,
          "fc_low_output_pct": 44.45497630331754,
          "battery_throughput_kwh": 1.7869724696939344,
          "battery_ohmic_loss_kwh": 0.09747490356561656,
          "soc_mean": 0.5812715557151487,
          "soc_delta": -1.143167473642913
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 43.71312304531679,
          "fc_energy_kwh": 0.5960565345415345,
          "fc_energy_efficiency": 0.4091101970944731,
          "fc_low_output_pct": 77.25258493353027,
          "battery_throughput_kwh": 1.6102356782284146,
          "battery_ohmic_loss_kwh": 0.09806406858604647,
          "soc_mean": 0.5952037475877838,
          "soc_delta": 0.9429640816446315
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 304.1626091373797,
          "fc_energy_kwh": 5.246622879864194,
          "fc_energy_efficiency": 0.5175337898538708,
          "fc_low_output_pct": 10.412147505422993,
          "battery_throughput_kwh": 0.9594310849917825,
          "battery_ohmic_loss_kwh": 0.031727602841629836,
          "soc_mean": 0.5578197308657541,
          "soc_delta": 0.140559757176976
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
    "total_cost_delta_usd": 26.164343792037048,
    "cost_delta_usd": {
      "h2_usd": -0.03718252914545239,
      "fc_usd": 26.22297937474971,
      "batt_usd": -0.021453053567210834
    },
    "soc_drift": 0.01456107999410905,
    "fuel_delta_gkm": -0.05311789877921669,
    "fc_loss_delta": 0.000208008000006088,
    "batt_loss_delta": -2.729353759001185e-06,
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
    "total_cost_delta_usd_vs_baseline": 15.670210910631901,
    "fuel_delta_gkm_vs_baseline": 0.01640556984055941,
    "fc_loss_delta_vs_baseline": 0.00012889183332609466,
    "batt_loss_delta_vs_baseline": -7.510078423333955e-05
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
        "mean": 10.631884529455856,
        "std": 0.038209477232721736,
        "slope_per_10_episodes": 0.01073335579985427,
        "ep399_better_than_fraction": 0.025
      },
      "fc_loss": {
        "n": 40,
        "mean": 0.000392847024973228,
        "std": 8.14654533861485e-05,
        "slope_per_10_episodes": -5.393070356569858e-05,
        "ep399_better_than_fraction": 0.525
      },
      "batt_loss": {
        "n": 40,
        "mean": 0.00048335594595836083,
        "std": 1.6325401704153337e-05,
        "slope_per_10_episodes": -5.01834786884809e-06,
        "ep399_better_than_fraction": 0.95
      }
    },
    "lucky_checkpoint": false
  },
  "reward_diff": "--- parent:243cb08ab6af\n+++ candidate\n@@ -4,40 +4,39 @@\n \n     # --- soc_anchor [charge_sustaining, term_soc_anchor] ---\n     # Symmetric quadratic anchor pulling SOC to target, x10 outside bounds.\n-    soc_err = (soc - self.SOC_target) ** 2\n-    w_soc_step = np.where(\n+    soc_err = (soc - float(self.SOC_target)) ** 2\n+    w_soc_step = float(np.where(\n         (soc >= soc_high) | (soc <= soc_low),\n         self.w_soc * 10.0,\n         self.w_soc\n-    )\n+    ))\n     term_soc_anchor = float(w_soc_step * soc_err)\n \n     # --- fc_surplus_charge [charge_sustaining, term_fc_surplus_charge] ---\n     # Price FC power flowing into the battery when SOC is above SOC_target - m.\n     # Gate g = max(0, SOC - (SOC_target - m)) / m, linear from 0 at SOC_target-m\n     # to 1.0 at SOC_target and beyond (uncapped above SOC_target).\n-    # P_fc_to_batt_kw = max(0, min(-P_batt, P_mot - P_batt)) / 1000\n     # Catalog form: c * g(SOC) * P_fc_to_batt_kw\n     # c = 0.70, m = 0.05\n-    _m = 0.05\n+    _m_surplus = 0.05\n     _c_surplus = 0.70\n-    _gate = float(np.maximum(0.0, soc - (float(self.SOC_target) - _m)) / _m)\n-    _p_batt_w = float(self.P_batt)          # W, + = discharge\n-    _p_mot_w  = float(self.P_mot)           # W, motor electrical power\n+    _gate_surplus = float(np.maximum(0.0, soc - (float(self.SOC_target) - _m_surplus)) / _m_surplus)\n+    _p_batt_w = float(self.P_batt)       # W, + = discharge\n+    _p_mot_w  = float(self.P_mot)        # W, motor electrical power\n     # FC power into battery (kW): positive only when FC is charging battery\n     _p_fc_to_batt_kw = float(\n         np.maximum(0.0, np.minimum(-_p_batt_w, _p_mot_w - _p_batt_w)) / 1000.0\n     )\n-    term_fc_surplus_charge = float(_c_surplus * _gate * _p_fc_to_batt_kw)\n+    term_fc_surplus_charge = float(_c_surplus * _gate_surplus * _p_fc_to_batt_kw)\n \n     # soc_cost = sum of charge-sustaining terms\n     soc_cost = term_soc_anchor + term_fc_surplus_charge\n \n     # --- h2_cost [price] ---\n-    h2_fcs  = self.h2_fcs\n-    h2_batt = self.h2_batt\n+    h2_fcs   = self.h2_fcs\n+    h2_batt  = self.h2_batt\n     h2_equal = self.h2_equal\n-    h2_cost = float(self.w_h2 * h2_fcs)\n+    h2_cost  = float(self.w_h2 * h2_fcs)\n \n     # --- fcs_soh_cost [price] ---\n     fcs_soh_cost = float(self.w_fc * float(self.dSOH_FCS))\n@@ -45,24 +44,43 @@\n     # --- batt_soh_cost [price] ---\n     batt_soh_cost = float(self.w_batt * float(self.dSOH_batt))\n \n+    # --- fc_efficiency_gap [price, term_fc_efficiency_gap] ---\n+    # Price hydrogen burned below the FC's efficient operating point.\n+    # Catalog form: c * h2_fcs * max(0, eta_ref - eta) / eta_ref\n+    # eta = P_FCS / (120 * h2_fcs) when h2_fcs > 0, else eta_ref (no penalty when FC off).\n+    # eta_ref = 0.602 (peak efficiency at 10-15 kW, measured on edit base rollout).\n+    # c = 0.4: breakeven vs. one start = 83.79 / (0.4 * mean_gap_term_per_step) >> 3441 steps,\n+    # so the policy will not prefer starts over sustained low-power operation.\n+    # Mean per-step contribution ~0.003 reward units, negligible vs. selection-priced cost 8.094.\n+    _eta_ref = 0.602\n+    _c_eff   = 0.4\n+    _h2_fcs_val = float(h2_fcs)\n+    _p_fcs_kw   = float(self.P_FCS)\n+    # When FC is off (h2_fcs = 0), set eta = eta_ref so gap = 0 (no penalty).\n+    _eta = (_p_fcs_kw / (120.0 * _h2_fcs_val)) if _h2_fcs_val > 1e-9 else _eta_ref\n+    _eff_gap = float(np.maximum(0.0, _eta_ref - _eta) / _eta_ref)\n+    term_fc_efficiency_gap = float(_c_eff * _h2_fcs_val * _eff_gap)\n+\n     in_bounds = bool(soc_low < soc < soc_high)\n \n-    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost\n+    objective_cost = (soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost\n+                      + term_fc_efficiency_gap)\n     reward = float(-objective_cost)\n \n     self.info.update({\n-        'EMS_reward':            reward,\n-        'h2_fcs':                float(h2_fcs),\n-        'h2_batt':               float(h2_batt),\n-        'h2_equal':              float(h2_equal),\n-        'soc_"
}
```

[Training log](results/aroma_runs/seed1_obscur_20261018_113049_381984490/search/20261018_113049_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed1_obscur_seq_v3_catalog_iter6/trials/df36edb3ae5bd1ca7c9be8bf/iter_001/train_log.log)
[Evaluation records](results/aroma_runs/seed1_obscur_20261018_113049_381984490/search/20261018_113049_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed1_obscur_seq_v3_catalog_iter6/trials/df36edb3ae5bd1ca7c9be8bf/deterministic_evaluations.jsonl)
