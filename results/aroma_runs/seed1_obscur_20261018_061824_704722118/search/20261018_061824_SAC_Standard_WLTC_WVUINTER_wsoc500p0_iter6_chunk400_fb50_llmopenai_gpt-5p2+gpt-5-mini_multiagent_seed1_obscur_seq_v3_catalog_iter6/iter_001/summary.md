# Iteration 1

Decision: **baseline_trained**

```json
{
  "iteration": 1,
  "decision": "baseline_trained",
  "candidate": {
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
  }
}
```

[Training log](results/aroma_runs/seed1_obscur_20261018_061824_704722118/search/20261018_061824_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed1_obscur_seq_v3_catalog_iter6/trials/806f1da4107778ebb8a31d19/iter_001/train_log.log)
[Evaluation records](results/aroma_runs/seed1_obscur_20261018_061824_704722118/search/20261018_061824_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed1_obscur_seq_v3_catalog_iter6/trials/806f1da4107778ebb8a31d19/deterministic_evaluations.jsonl)
