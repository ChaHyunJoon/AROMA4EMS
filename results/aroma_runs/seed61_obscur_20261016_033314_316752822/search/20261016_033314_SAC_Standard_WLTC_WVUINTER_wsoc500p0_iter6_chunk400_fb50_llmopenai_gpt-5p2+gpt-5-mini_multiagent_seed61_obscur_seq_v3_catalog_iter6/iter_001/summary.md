# Iteration 1

Decision: **baseline_trained**

```json
{
  "iteration": 1,
  "decision": "baseline_trained",
  "candidate": {
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
  "forked_from": {
    "run_root": "results/aroma_runs/seed61_obscur_20261015_085323_832232197/search/20261015_085323_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed61_obscur_seq_v3_cost_iter6",
    "iteration": 1,
    "baseline_id": "17afbf80420cb9f947efdaac72a30bf9687444a44fa8df43fcfaa7ace533d083",
    "source_conditions_id": "90b5510520306ffdd82af0883a784aa337836d60c41882ebc05867a9ea25285f",
    "differing_proposal_side_sources": [
      "candidate_validation.py",
      "development_validation.py",
      "reward_terms.py",
      "sequential_workflow.py"
    ],
    "selection_policy_changed": true,
    "differing_proposal_side_args": {
      "reward_term_catalog": [
        null,
        true
      ],
      "cost_max_fuel_increase": [
        0.02,
        0.05
      ],
      "cost_max_soc_drift": [
        null,
        0.05
      ]
    }
  }
}
```

[Training log](results/aroma_runs/seed61_obscur_20261016_033314_316752822/search/20261016_033314_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed61_obscur_seq_v3_catalog_iter6/trials/5dd14214c01b19b3c17022b6/iter_001/train_log.log)
[Evaluation records](results/aroma_runs/seed61_obscur_20261016_033314_316752822/search/20261016_033314_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed61_obscur_seq_v3_catalog_iter6/trials/5dd14214c01b19b3c17022b6/deterministic_evaluations.jsonl)
