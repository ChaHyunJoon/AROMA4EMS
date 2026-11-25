# Iteration 2

Decision: **retain_champion**

```json
{
  "iteration": 2,
  "control": {
    "candidate_id": "17afbf80420cb9f947efdaac72a30bf9687444a44fa8df43fcfaa7ace533d083",
    "seed": 1,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.6562854090602,
      "fc_loss": 0.00022755816664343786,
      "batt_loss": 0.0005426791354884442,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5436408567243644,
      "soc_max": 0.6739097201102481
    },
    "operating_cost": {
      "h2_usd": 7.45939978634214,
      "fc_usd": 28.687613506557817,
      "batt_usd": 4.2655242198072045,
      "degradation_usd": 32.95313772636502,
      "total_usd": 40.41253751270716,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.673761753276468,
      "soc_correction_gkm": -0.01747634421626657,
      "soc_final": 0.6092110798875628,
      "soc_final_minus_initial": 0.009211079887562867,
      "unaccepted_fc_kwh": 0.0013104144617879854,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.653879374321736,
      "fc_loss": 0.00024918413539261054,
      "batt_loss": 0.000545478315356987
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.6092110798875628,
      "soc_final_minus_initial": 0.009211079887562867,
      "soc_swing": 0.13026886338588373,
      "soc_mean": 0.6144319802401514,
      "fc_power_kw_mean": 10.031732207036825,
      "fc_abs_ramp_kw_s_mean": 1.6468069579348108,
      "fc_on_pct": 78.17494914269108,
      "fc_start_stop_count": 11,
      "fc_start_stop_soh_loss": 0.00021559999999999998,
      "fc_low_power_count": 534,
      "fc_low_power_soh_loss": 1.8689999999999998e-06,
      "fc_high_power_soh_loss": 8.166666666666667e-09,
      "fc_load_change_count": 17,
      "fc_load_change_soh_loss": 1.0081e-05,
      "battery_throughput_kwh": 4.966083766525999,
      "battery_ohmic_loss_kw_integral_kwh": 0.2798767034022185,
      "fc_low_output_pct": 42.28421970357454,
      "fc_regeneration_energy_kwh": 0.8388188480629577,
      "fc_energy_efficiency": 0.5115023807111742
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
          "battery_ohmic_loss_kwh": 3.950502492830206e-08,
          "soc_mean": 0.6439403423091218,
          "soc_delta": -0.00012321992355279754
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 100.96585803455488,
          "fc_energy_kwh": 1.701678573259136,
          "fc_energy_efficiency": 0.5056705676346067,
          "fc_low_output_pct": 39.958448753462605,
          "battery_throughput_kwh": 0.8475848353926325,
          "battery_ohmic_loss_kwh": 0.01989636786945871,
          "soc_mean": 0.628104997332726,
          "soc_delta": 0.04702673189687556
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 192.26448409491476,
          "fc_energy_kwh": 3.226911590751169,
          "fc_energy_efficiency": 0.5035616946168914,
          "fc_low_output_pct": 48.530805687203795,
          "battery_throughput_kwh": 2.1738392680552603,
          "battery_ohmic_loss_kwh": 0.1441977979134814,
          "soc_mean": 0.6140984909097984,
          "soc_delta": -1.3347151370675276
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 53.47505966893712,
          "fc_energy_kwh": 0.8388188480629577,
          "fc_energy_efficiency": 0.47063214713387097,
          "fc_low_output_pct": 78.43426883308715,
          "battery_throughput_kwh": 1.8191868756018237,
          "battery_ohmic_loss_kwh": 0.11391632923905065,
          "soc_mean": 0.6283029742548273,
          "soc_delta": 1.0582728144367015
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 299.8736333139417,
          "fc_energy_kwh": 5.181548465675691,
          "fc_energy_efficiency": 0.518425039414961,
          "fc_low_output_pct": 11.930585683297181,
          "battery_throughput_kwh": 1.0729746277091563,
          "battery_ohmic_loss_kwh": 0.0396630429497996,
          "soc_mean": 0.5804159560739341,
          "soc_delta": 0.09481839406846948
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
    "candidate_id": "a961a1c2d67e57806c57dd8c9b78fd7e4a56f26ecb740246e70bfc923a65e262",
    "seed": 1,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.192362440466646,
      "fc_loss": 0.0006133604999949416,
      "batt_loss": 0.0005202309104312963,
      "soc_in_bounds": 100.0,
      "soc_min": 0.45525762044063994,
      "soc_max": 0.6160323130781702
    },
    "operating_cost": {
      "h2_usd": 7.134653708326652,
      "fc_usd": 77.32462088084483,
      "batt_usd": 4.089078431843082,
      "degradation_usd": 81.41369931268791,
      "total_usd": 88.54835302101456,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.05317366293388,
      "soc_correction_gkm": 0.13918877753276496,
      "soc_final": 0.5245823180234167,
      "soc_final_minus_initial": -0.07541768197658327,
      "unaccepted_fc_kwh": 0.0,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.185567481489851,
      "fc_loss": 0.0006766956749941655,
      "batt_loss": 0.0005121280825761742
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.5245823180234167,
      "soc_final_minus_initial": -0.07541768197658327,
      "soc_swing": 0.16077469263753025,
      "soc_mean": 0.5461161158190742,
      "fc_power_kw_mean": 9.764635503027417,
      "fc_abs_ramp_kw_s_mean": 0.8844633209282773,
      "fc_on_pct": 58.29700668410346,
      "fc_start_stop_count": 31,
      "fc_start_stop_soh_loss": 0.0006076,
      "fc_low_power_count": 121,
      "fc_low_power_soh_loss": 4.235e-07,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 9,
      "fc_load_change_soh_loss": 5.337e-06,
      "battery_throughput_kwh": 4.936204966791085,
      "battery_ohmic_loss_kw_integral_kwh": 0.26105981326382116,
      "fc_low_output_pct": 15.286253995931414,
      "fc_regeneration_energy_kwh": 0.46394766070116045,
      "fc_energy_efficiency": 0.5258436815203298
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
          "battery_ohmic_loss_kwh": 4.030622175107975e-08,
          "soc_mean": 0.5692704881606521,
          "soc_delta": -0.0001244087968048646
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 91.8015046869744,
          "fc_energy_kwh": 1.6569792541424875,
          "fc_energy_efficiency": 0.541541766975356,
          "fc_low_output_pct": 12.396121883656509,
          "battery_throughput_kwh": 1.1730794649068248,
          "battery_ohmic_loss_kwh": 0.036269492638961176,
          "soc_mean": 0.5582145760000784,
          "soc_delta": 0.037768293017765686
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 175.83594032194512,
          "fc_energy_kwh": 3.074447322355303,
          "fc_energy_efficiency": 0.5245949364285926,
          "fc_low_output_pct": 14.502369668246445,
          "battery_throughput_kwh": 2.161873759818211,
          "battery_ohmic_loss_kwh": 0.13641395747784693,
          "soc_mean": 0.5435951929352281,
          "soc_delta": -1.4128584152344592
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 28.311272763491704,
          "fc_energy_kwh": 0.46394766070116045,
          "fc_energy_efficiency": 0.49167064721884185,
          "fc_low_output_pct": 29.098966026587885,
          "battery_throughput_kwh": 1.5280561541484754,
          "battery_ohmic_loss_kwh": 0.08912792282412858,
          "soc_mean": 0.5601317594195151,
          "soc_delta": 0.9009008249338188
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 309.4368429599492,
          "fc_energy_kwh": 5.3675388569060765,
          "fc_energy_efficiency": 0.5204366370652884,
          "fc_low_output_pct": 4.4468546637744035,
          "battery_throughput_kwh": 1.2444470046945284,
          "battery_ohmic_loss_kwh": 0.051511209483204264,
          "soc_mean": 0.5164648580761999,
          "soc_delta": 0.19427031002555784
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
      "charge_sustaining": false,
      "fuel_within_guard": true,
      "battery_within_guard": true
    },
    "checkpoint_episode": 399,
    "cost_unit": "USD per 100 km",
    "total_cost_delta_usd": 48.1358155083074,
    "cost_delta_usd": {
      "h2_usd": -0.3247460780154885,
      "fc_usd": 48.637007374287016,
      "batt_usd": -0.17644578796412258
    },
    "soc_drift": -0.07541768197658327,
    "fuel_delta_gkm": -0.463922968593554,
    "fc_loss_delta": 0.0003858023333515037,
    "batt_loss_delta": -2.244822505714783e-05,
    "guards": {
      "reference": "baseline",
      "max_fuel_increase_fraction": 0.05,
      "max_batt_increase_fraction": 0.1,
      "fuel_gkm_max": 11.18909967951321,
      "batt_loss_max": 0.0005969470490372886,
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
        "mean": 10.185567481489851,
        "std": 0.05627749589281147,
        "slope_per_10_episodes": -0.01901596798595425,
        "ep399_better_than_fraction": 0.3
      },
      "fc_loss": {
        "n": 40,
        "mean": 0.0006766956749941655,
        "std": 9.152061700277377e-05,
        "slope_per_10_episodes": -2.6207548779662478e-05,
        "ep399_better_than_fraction": 0.925
      },
      "batt_loss": {
        "n": 40,
        "mean": 0.0005121280825761742,
        "std": 2.1819486581819883e-05,
        "slope_per_10_episodes": -9.434539588384041e-06,
        "ep399_better_than_fraction": 0.25
      }
    },
    "lucky_checkpoint": false
  },
  "reward_diff": "--- parent:17afbf80420c\n+++ candidate\n@@ -1,30 +1,62 @@\n def get_reward(self):\n     soc = float(self.SOC)\n     soc_low, soc_high = self.soc_bounds\n-    # SOC deviation from target\n-    soc_err = (np.abs(soc - self.SOC_target)) ** 2\n-    w_soc = np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10, self.w_soc)\n-    soc_cost = w_soc * soc_err\n \n+    # ---------- Charge-sustaining family (soc_cost = sum of catalog terms) ----------\n+    # Catalog term: soc_anchor (CHANGED SHAPE: asymmetric, still quadratic, still bounds-multiplied)\n+    soc_tgt = float(self.SOC_target)\n+    soc_err_up = float(np.maximum(0.0, soc - soc_tgt))\n+    soc_err_dn = float(np.maximum(0.0, soc_tgt - soc))\n+\n+    # Asymmetry: over-target SOC is priced more than under-target SOC to resist net overcharge drift\n+    c_up = 1.50 * float(self.w_soc)\n+    c_dn = 0.70 * float(self.w_soc)\n+    p = 2.0\n+\n+    out_of_bounds = (soc >= float(soc_high)) or (soc <= float(soc_low))\n+    k_bounds = 10.0 if out_of_bounds else 1.0\n+    term_soc_anchor = k_bounds * (c_up * (soc_err_up ** p) + c_dn * (soc_err_dn ** p))\n+    self.info[\"term_soc_anchor\"] = float(term_soc_anchor)\n+\n+    # Catalog term: fc_surplus_charge (ADDED)\n+    # FC power into the battery (kW), per catalog definition; only positive when FC is charging the pack.\n+    P_mot = float(self.P_mot)          # W\n+    P_batt = float(self.P_batt)        # W, + = discharge\n+    P_fc_to_batt_kw = float(np.maximum(0.0, np.minimum(-P_batt, P_mot - P_batt)) / 1000.0)\n+\n+    # SOC gate g(SOC): 0 at/below SOC_target - m, linear to 1 at SOC_target and above\n+    m = 0.05\n+    g_soc = float(np.clip((soc - (soc_tgt - m)) / m, 0.0, 1.0))\n+\n+    # Coefficient sized to land ~5-6k total added cost over the 1682 high-drift steps on the baseline replay.\n+    c_surplus = 2.0\n+    term_fc_surplus_charge = c_surplus * g_soc * P_fc_to_batt_kw\n+    self.info[\"term_fc_surplus_charge\"] = float(term_fc_surplus_charge)\n+\n+    soc_cost = float(term_soc_anchor + term_fc_surplus_charge)\n+    self.info[\"soc_cost\"] = float(soc_cost)\n+\n+    # ---------- Price-aligned operating terms (unchanged set; no extra catalog price terms added) ----------\n     h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal\n-    h2_cost = self.w_h2 * h2_fcs\n-    # Cost of fuel cell degradation (scaled)\n-    fcs_soh_cost = self.w_fc * float(self.dSOH_FCS)\n-    # Cost of battery degradation (scaled)\n-    batt_soh_cost = self.w_batt * float(self.dSOH_batt)\n+    h2_cost = float(self.w_h2) * float(h2_fcs)\n \n-    in_bounds = (soc_low < soc < soc_high)\n+    fcs_soh_cost = float(self.w_fc) * float(self.dSOH_FCS)\n+    batt_soh_cost = float(self.w_batt) * float(self.dSOH_batt)\n+\n     objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost\n     reward = float(-objective_cost)\n \n-    self.info.update({'EMS_reward': reward,\n-                      'h2_fcs': float(h2_fcs),\n-                      'h2_batt': float(h2_batt),\n-                      'h2_equal': float(h2_equal),\n-                      'soc_cost': float(soc_cost),\n-                      'h2_cost': float(h2_cost),\n-                      'fcs_soh_cost': float(fcs_soh_cost),\n-                      'batt_soh_cost': float(batt_soh_cost),\n-                      'objective_cost': float(objective_cost),\n-                      'soc_in_bounds': int(in_bounds)})\n+    in_bounds = (float(soc_low) < soc < float(soc_high))\n+\n+    self.info.update({\n+        \"EMS_reward\": float(reward),\n+        \"h2_fcs\": float(h2_fcs),\n+        \"h2_batt\": float(h2_batt),\n+        \"h2_equal\": float(h2_equal),\n+        \"h2_cost\": float(h2_cost),\n+        \"fcs_soh_cost\": float(fcs_soh_cost),\n+        \"batt_soh_cost\": float(batt_soh_cost),\n+        \"objective_cost\": float(objective_cost),\n+        \"soc_in_bounds\": int(in_bounds),\n+    })\n     return reward\n"
}
```

[Training log](results/aroma_runs/seed1_obscur_20261018_061824_704722118/search/20261018_061824_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed1_obscur_seq_v3_catalog_iter6/trials/d18c3f331a7a4b31c34adad8/iter_001/train_log.log)
[Evaluation records](results/aroma_runs/seed1_obscur_20261018_061824_704722118/search/20261018_061824_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed1_obscur_seq_v3_catalog_iter6/trials/d18c3f331a7a4b31c34adad8/deterministic_evaluations.jsonl)
