# Iteration 5

Decision: **proposal_failed**

```json
{
  "iteration": 5,
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
  "decision": "proposal_failed",
  "experiment_plan": {
    "name": "archive",
    "iteration": 5
  },
  "edit_base": {
    "mode": "champion_improve",
    "parent_reward_id": "eb92825323ba17b3c53a26167f4276edba0c98b8823ab4fd1114398bb4fe87c8",
    "selection_reason": "champion_improve: rank 1 of 1"
  }
}
```
