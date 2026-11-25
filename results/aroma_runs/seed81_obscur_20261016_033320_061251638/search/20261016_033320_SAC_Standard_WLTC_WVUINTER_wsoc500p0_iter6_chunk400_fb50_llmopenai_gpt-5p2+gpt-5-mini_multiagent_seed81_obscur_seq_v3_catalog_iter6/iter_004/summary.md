# Iteration 4

Decision: **retain_champion**

```json
{
  "iteration": 4,
  "control": {
    "candidate_id": "17afbf80420cb9f947efdaac72a30bf9687444a44fa8df43fcfaa7ace533d083",
    "seed": 81,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.838062644164271,
      "fc_loss": 0.00018646449997072878,
      "batt_loss": 0.0006140980938273977,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5219102773508741,
      "soc_max": 0.7005968306189944
    },
    "operating_cost": {
      "h2_usd": 7.58664385091499,
      "fc_usd": 23.507051347603593,
      "batt_usd": 4.826885946518908,
      "degradation_usd": 28.3339372941225,
      "total_usd": 35.92058114503749,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 11.015494047079216,
      "soc_correction_gkm": -0.1774314029149446,
      "soc_final": 0.6933909074637872,
      "soc_final_minus_initial": 0.0933909074637872,
      "unaccepted_fc_kwh": 0.0029069897429724813,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 10.804265071761517,
      "fc_loss": 0.00023094022497543442,
      "batt_loss": 0.0006092576054848586
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.6933909074637872,
      "soc_final_minus_initial": 0.0933909074637872,
      "soc_swing": 0.17868655326812022,
      "soc_mean": 0.6141031181647345,
      "fc_power_kw_mean": 10.331529178127507,
      "fc_abs_ramp_kw_s_mean": 1.644182118823985,
      "fc_on_pct": 89.97384481255449,
      "fc_start_stop_count": 9,
      "fc_start_stop_soh_loss": 0.0001764,
      "fc_low_power_count": 673,
      "fc_low_power_soh_loss": 2.3554999999999997e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 13,
      "fc_load_change_soh_loss": 7.709000000000002e-06,
      "battery_throughput_kwh": 5.656315904706234,
      "battery_ohmic_loss_kw_integral_kwh": 0.3304574340924226,
      "fc_low_output_pct": 60.33129904097646,
      "fc_regeneration_energy_kwh": 1.149410317593584,
      "fc_energy_efficiency": 0.5108128448435574
    },
    "regimes": {
      "available": true,
      "groups": {
        "stopped": {
          "steps": 408,
          "available": true,
          "duration_s": 408.0,
          "hydrogen_g": 9.788494045905244,
          "fc_energy_kwh": 0.09399491909818601,
          "fc_energy_efficiency": 0.2881065843916917,
          "fc_low_output_pct": 34.55882352941176,
          "battery_throughput_kwh": 0.06651828580241553,
          "battery_ohmic_loss_kwh": 0.0007137165333119277,
          "soc_mean": 0.672912275543433,
          "soc_delta": 0.040520013822578194
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 123.53653394556694,
          "fc_energy_kwh": 2.0493771900734465,
          "fc_energy_efficiency": 0.4977269677627597,
          "fc_low_output_pct": 68.69806094182826,
          "battery_throughput_kwh": 0.9053698368957496,
          "battery_ohmic_loss_kwh": 0.019313540035792498,
          "soc_mean": 0.6393014847682068,
          "soc_delta": 0.21299188736798458
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 196.8043123343204,
          "fc_energy_kwh": 3.304912114645745,
          "fc_energy_efficiency": 0.5038369230387906,
          "fc_low_output_pct": 71.09004739336493,
          "battery_throughput_kwh": 2.361892024078149,
          "battery_ohmic_loss_kwh": 0.16692266367602734,
          "soc_mean": 0.6197806999084543,
          "soc_delta": -1.3162099965334892
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 69.1166456393207,
          "fc_energy_kwh": 1.149410317593584,
          "fc_energy_efficiency": 0.49895011230115044,
          "fc_low_output_pct": 81.0930576070901,
          "battery_throughput_kwh": 2.08403599630716,
          "battery_ohmic_loss_kwh": 0.13406456542167658,
          "soc_mean": 0.6334005963752112,
          "soc_delta": 1.2103126616978916
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 298.9610683091209,
          "fc_energy_kwh": 5.177544911456666,
          "fc_energy_efficiency": 0.5196057212748256,
          "fc_low_output_pct": 15.184381778741866,
          "battery_throughput_kwh": 1.1015617550527097,
          "battery_ohmic_loss_kwh": 0.042483578869247716,
          "soc_mean": 0.5516001004095981,
          "soc_delta": 0.09475896273611428
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
    "parent_reward_id": "17afbf80420cb9f947efdaac72a30bf9687444a44fa8df43fcfaa7ace533d083",
    "selection_reason": "champion_improve: rank 1 of 1 (no fresh guard_repair target)"
  },
  "candidate": {
    "candidate_id": "b4df71cded471020ba3c1c43e1f52cdcb7502976c62e4492f88d3500cae654f3",
    "seed": 81,
    "status": "complete",
    "final_ep399": {
      "fuel_gkm": 10.937016204169574,
      "fc_loss": 0.00020503649995406992,
      "batt_loss": 0.0004926985658025851,
      "soc_in_bounds": 100.0,
      "soc_min": 0.5382369297422444,
      "soc_max": 0.6468663631385758
    },
    "operating_cost": {
      "h2_usd": 7.655911342918702,
      "fc_usd": 25.848370780013656,
      "batt_usd": 3.872670843708809,
      "degradation_usd": 29.721041623722463,
      "total_usd": 37.37695296664117,
      "unit": "USD per 100 km"
    },
    "fuel_breakdown": {
      "raw_h2_gkm": 10.986543330854456,
      "soc_correction_gkm": -0.04952712668488162,
      "soc_final": 0.6258523577099372,
      "soc_final_minus_initial": 0.025852357709937213,
      "unaccepted_fc_kwh": 0.003863779158075832,
      "unaccepted_regen_kwh": 0.0
    },
    "tail_mean": {
      "fuel_gkm": 11.028830084935043,
      "fc_loss": 0.0002133421749482889,
      "batt_loss": 0.0004922919656886515
    },
    "physics": {
      "soc_initial": 0.6,
      "soc_final": 0.6258523577099372,
      "soc_final_minus_initial": 0.025852357709937213,
      "soc_swing": 0.10862943339633147,
      "soc_mean": 0.5889262982760293,
      "fc_power_kw_mean": 10.038006451487009,
      "fc_abs_ramp_kw_s_mean": 1.7904743769082654,
      "fc_on_pct": 85.58558558558559,
      "fc_start_stop_count": 10,
      "fc_start_stop_soh_loss": 0.000196,
      "fc_low_power_count": 1057,
      "fc_low_power_soh_loss": 3.6995000000000003e-06,
      "fc_high_power_soh_loss": 0.0,
      "fc_load_change_count": 9,
      "fc_load_change_soh_loss": 5.337e-06,
      "battery_throughput_kwh": 4.5552725159414935,
      "battery_ohmic_loss_kw_integral_kwh": 0.22632529419002403,
      "fc_low_output_pct": 52.80441732054635,
      "fc_regeneration_energy_kwh": 0.702422234031256,
      "fc_energy_efficiency": 0.49686954443555925
    },
    "regimes": {
      "available": true,
      "groups": {
        "stopped": {
          "steps": 408,
          "available": true,
          "duration_s": 408.0,
          "hydrogen_g": 7.931793204782205,
          "fc_energy_kwh": 0.07750693273043936,
          "fc_energy_efficiency": 0.29317967147249024,
          "fc_low_output_pct": 27.941176470588236,
          "battery_throughput_kwh": 0.05532146722380114,
          "battery_ohmic_loss_kwh": 0.0005771488335197507,
          "soc_mean": 0.6276977298064608,
          "soc_delta": 0.033774476242891094
        },
        "low_load": {
          "steps": 1444,
          "available": true,
          "duration_s": 1444.0,
          "hydrogen_g": 101.54851042514902,
          "fc_energy_kwh": 1.552359331150303,
          "fc_energy_efficiency": 0.45865209921112016,
          "fc_low_output_pct": 64.40443213296399,
          "battery_throughput_kwh": 0.8796945417613846,
          "battery_ohmic_loss_kwh": 0.01941534892951808,
          "soc_mean": 0.6036517128838768,
          "soc_delta": -0.05289115564828839
        },
        "acceleration": {
          "steps": 1055,
          "available": true,
          "duration_s": 1055.0,
          "hydrogen_g": 212.51438614499702,
          "fc_energy_kwh": 3.5376237805427824,
          "fc_energy_efficiency": 0.499445375319675,
          "fc_low_output_pct": 52.22748815165876,
          "battery_throughput_kwh": 1.8879526499514974,
          "battery_ohmic_loss_kwh": 0.10527526102529515,
          "soc_mean": 0.5874348504919725,
          "soc_delta": -1.146064660230875
        },
        "regeneration": {
          "steps": 677,
          "available": true,
          "duration_s": 677.0,
          "hydrogen_g": 50.70770930015033,
          "fc_energy_kwh": 0.702422234031256,
          "fc_energy_efficiency": 0.41561282868530297,
          "fc_low_output_pct": 84.78581979320532,
          "battery_throughput_kwh": 1.6920844428031245,
          "battery_ohmic_loss_kwh": 0.10060049692851633,
          "soc_mean": 0.5980262962405904,
          "soc_delta": 0.9920780921580102
        },
        "high_speed": {
          "steps": 922,
          "available": true,
          "duration_s": 922.0,
          "hydrogen_g": 298.9004402992163,
          "fc_energy_kwh": 5.158183501544689,
          "fc_energy_efficiency": 0.5177676586542682,
          "fc_low_output_pct": 12.906724511930587,
          "battery_throughput_kwh": 0.90567785138551,
          "battery_ohmic_loss_kwh": 0.029861372916065675,
          "soc_mean": 0.5635602892310686,
          "soc_delta": 0.08946034704929318
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
    "total_cost_delta_usd": 1.4563718216036818,
    "cost_delta_usd": {
      "h2_usd": 0.0692674920037124,
      "fc_usd": 2.3413194324100637,
      "batt_usd": -0.9542151028100987
    },
    "soc_drift": 0.025852357709937213,
    "fuel_delta_gkm": 0.09895356000530242,
    "fc_loss_delta": 1.8571999983341136e-05,
    "batt_loss_delta": -0.00012139952802481258,
    "guards": {
      "reference": "baseline",
      "max_fuel_increase_fraction": 0.05,
      "max_batt_increase_fraction": 0.1,
      "fuel_gkm_max": 11.379965776372485,
      "batt_loss_max": 0.0006755079032101375,
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
        "mean": 11.028830084935043,
        "std": 0.13435764051270474,
        "slope_per_10_episodes": -0.09189576186408059,
        "ep399_better_than_fraction": 0.7
      },
      "fc_loss": {
        "n": 40,
        "mean": 0.0002133421749482889,
        "std": 3.735354529066505e-05,
        "slope_per_10_episodes": 1.2270907134824564e-05,
        "ep399_better_than_fraction": 0.475
      },
      "batt_loss": {
        "n": 40,
        "mean": 0.0004922919656886515,
        "std": 1.0438645963636252e-05,
        "slope_per_10_episodes": -1.6517845609567774e-06,
        "ep399_better_than_fraction": 0.4
      }
    },
    "lucky_checkpoint": false
  },
  "reward_diff": "--- parent:17afbf80420c\n+++ candidate\n@@ -1,30 +1,54 @@\n def get_reward(self):\n     soc = float(self.SOC)\n     soc_low, soc_high = self.soc_bounds\n-    # SOC deviation from target\n-    soc_err = (np.abs(soc - self.SOC_target)) ** 2\n-    w_soc = np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10, self.w_soc)\n-    soc_cost = w_soc * soc_err\n \n+    # ---------- Charge-sustaining terms (must sum into soc_cost) ----------\n+    # term_soc_anchor (catalog: soc_anchor), RESHAPED to be asymmetric:\n+    # penalize SOC above target more than below to stop the observed +SOC drift.\n+    soc_target = float(self.SOC_target)\n+    soc_err_up = float(np.maximum(0.0, soc - soc_target))\n+    soc_err_down = float(np.maximum(0.0, soc_target - soc))\n+\n+    # bounds multiplier k=10 exactly as edit_base behavior (stronger near SOC limits)\n+    k_bounds = 10.0\n+    w_bounds = float(np.where((soc >= soc_high) | (soc <= soc_low), k_bounds, 1.0))\n+\n+    # Asymmetry: overcharge is the failure mode (reward_id 17afbf... ended +0.093 SOC),\n+    # so make c_up > c_down while keeping p=2.\n+    c_down = float(self.w_soc) * 1.0\n+    c_up = float(self.w_soc) * 4.0\n+    p = 2.0\n+\n+    term_soc_anchor = w_bounds * (c_up * (soc_err_up ** p) + c_down * (soc_err_down ** p))\n+    soc_cost = term_soc_anchor\n+\n+    # ---------- Objective price terms (unchanged) ----------\n     h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal\n-    h2_cost = self.w_h2 * h2_fcs\n-    # Cost of fuel cell degradation (scaled)\n-    fcs_soh_cost = self.w_fc * float(self.dSOH_FCS)\n-    # Cost of battery degradation (scaled)\n-    batt_soh_cost = self.w_batt * float(self.dSOH_batt)\n+    h2_cost = float(self.w_h2) * float(h2_fcs)\n+    fcs_soh_cost = float(self.w_fc) * float(self.dSOH_FCS)\n+    batt_soh_cost = float(self.w_batt) * float(self.dSOH_batt)\n \n     in_bounds = (soc_low < soc < soc_high)\n     objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost\n     reward = float(-objective_cost)\n \n-    self.info.update({'EMS_reward': reward,\n-                      'h2_fcs': float(h2_fcs),\n-                      'h2_batt': float(h2_batt),\n-                      'h2_equal': float(h2_equal),\n-                      'soc_cost': float(soc_cost),\n-                      'h2_cost': float(h2_cost),\n-                      'fcs_soh_cost': float(fcs_soh_cost),\n-                      'batt_soh_cost': float(batt_soh_cost),\n-                      'objective_cost': float(objective_cost),\n-                      'soc_in_bounds': int(in_bounds)})\n+    # ---------- Logging ----------\n+    self.info.update({\n+        'EMS_reward': reward,\n+        'h2_fcs': float(h2_fcs),\n+        'h2_batt': float(h2_batt),\n+        'h2_equal': float(h2_equal),\n+\n+        # Catalog-term logs (plain values, before summing)\n+        'term_soc_anchor': float(term_soc_anchor),\n+\n+        # Keep these four logs truthful for their own terms\n+        'soc_cost': float(soc_cost),\n+        'h2_cost': float(h2_cost),\n+        'fcs_soh_cost': float(fcs_soh_cost),\n+        'batt_soh_cost': float(batt_soh_cost),\n+\n+        'objective_cost': float(objective_cost),\n+        'soc_in_bounds': int(in_bounds),\n+    })\n     return reward\n"
}
```

[Training log](results/aroma_runs/seed81_obscur_20261016_033320_061251638/search/20261016_033320_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed81_obscur_seq_v3_catalog_iter6/trials/4feb15765188b52b0e09dc52/iter_001/train_log.log)
[Evaluation records](results/aroma_runs/seed81_obscur_20261016_033320_061251638/search/20261016_033320_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed81_obscur_seq_v3_catalog_iter6/trials/4feb15765188b52b0e09dc52/deterministic_evaluations.jsonl)
