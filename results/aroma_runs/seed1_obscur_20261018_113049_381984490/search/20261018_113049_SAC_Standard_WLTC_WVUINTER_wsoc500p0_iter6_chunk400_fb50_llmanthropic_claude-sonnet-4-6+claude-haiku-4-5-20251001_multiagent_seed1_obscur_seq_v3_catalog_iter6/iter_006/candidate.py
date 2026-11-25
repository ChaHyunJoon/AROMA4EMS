def get_reward(self):
    soc = float(self.SOC)
    soc_low, soc_high = self.soc_bounds
    soc_target = float(self.SOC_target)
    soc_init = float(self.SOC_init)

    # --- term_soc_anchor [charge_sustaining, soc_anchor] ---
    # Symmetric quadratic anchor pulling SOC to target, x10 outside bounds.
    soc_err = (soc - soc_target) ** 2
    w_soc_step = float(np.where(
        (soc >= soc_high) | (soc <= soc_low),
        self.w_soc * 10.0,
        self.w_soc
    ))
    term_soc_anchor = float(w_soc_step * soc_err)

    # --- term_fc_surplus_charge [charge_sustaining, fc_surplus_charge] ---
    # Price FC power flowing into the battery when SOC is above SOC_target - m.
    # Gate g = max(0, SOC - (SOC_target - m)) / m, linear from 0 at SOC_target-m upward.
    # Catalog form: c * g(SOC) * P_fc_to_batt_kw
    # c = 0.70, m = 0.05
    # Checks: zero while discharging ✓, zero for pure regen ✓,
    #         zero at SOC_target - 0.1 (gate = max(0, 0.6-0.1-(0.6-0.05))/0.05 = max(0,-0.05)/0.05=0) ✓,
    #         positive at SOC_target + 0.05 with FC charging ✓,
    #         nondecreasing in SOC and FC charging power ✓.
    _m_surplus = 0.05
    _c_surplus = 0.70
    _gate_surplus = float(np.maximum(0.0, soc - (soc_target - _m_surplus)) / _m_surplus)
    _p_batt_w = float(self.P_batt)       # W, + = discharge
    _p_mot_w = float(self.P_mot)         # W, motor electrical power
    # FC power into battery (kW): positive only when FC is charging battery
    _p_fc_to_batt_kw = float(
        np.maximum(0.0, np.minimum(-_p_batt_w, _p_mot_w - _p_batt_w)) / 1000.0
    )
    term_fc_surplus_charge = float(_c_surplus * _gate_surplus * _p_fc_to_batt_kw)

    # --- term_drift_barrier [charge_sustaining, drift_barrier] ---
    # RESHAPED from edit base: deadband widened from d0=0.025 to d0=0.040.
    # Flat inside |SOC - SOC_init| <= d0, quadratic outside.
    # Catalog form: c * max(0, |SOC - SOC_init| - d0)^p
    # d0 = 0.040 (widened from 0.025), p = 2, c = 8000 (symmetric, both sides).
    #
    # Shape change rationale: d0=0.025 forced the policy to cycle the FC on/off
    # to keep SOC within ±0.025 of SOC_init, producing 23 starts. Widening to
    # d0=0.040 gives the policy a larger band to absorb FC surplus without cycling.
    #
    # Catalog checks:
    #   zero at |SOC-SOC_init| <= 0.01 (0.01 < 0.040, so excess = max(0, 0.01-0.040) = 0) ✓
    #   positive at |SOC-SOC_init| = 0.05 (excess = 0.010, cost = 8000*0.010^2 = 0.80) ✓
    #   nondecreasing in |SOC-SOC_init| ✓
    #
    # Sizing: at guard boundary (excess=0.010): 0.80 reward units/step.
    # Still inside sizing range [1843, 47030] over active steps.
    _d0 = 0.040
    _c_barrier = 8000.0
    _drift_excess = float(np.maximum(0.0, float(np.abs(soc - soc_init)) - _d0))
    term_drift_barrier = float(_c_barrier * _drift_excess ** 2)

    # soc_cost = sum of all charge-sustaining terms
    soc_cost = term_soc_anchor + term_fc_surplus_charge + term_drift_barrier

    # --- h2_cost [price] ---
    h2_fcs = self.h2_fcs
    h2_batt = self.h2_batt
    h2_equal = self.h2_equal
    h2_cost = float(self.w_h2 * h2_fcs)

    # --- fcs_soh_cost [price] ---
    # Weight raised to 1.5 * w_fc to price FC starts more heavily.
    # One start: 4,275,000 * 1.5 * 1.96e-05 = 125.7 reward units (vs 83.8 at 1.0x).
    # Price deviation: mean fcs_soh_cost rises by ~0.142/step; total deviation ~6.28/step
    # = 0.776x of selection-priced cost 8.094, within the configured multiple.
    # term_ratio.fcs_soh_cost = "changed" (weight multiplier changed).
    _fcs_weight = float(self.w_fc) * 1.5
    fcs_soh_cost = float(_fcs_weight * float(self.dSOH_FCS))

    # --- batt_soh_cost [price] ---
    batt_soh_cost = float(self.w_batt * float(self.dSOH_batt))

    in_bounds = bool(soc_low < soc < soc_high)

    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost
    reward = float(-objective_cost)

    self.info.update({
        'EMS_reward':               reward,
        'h2_fcs':                   float(h2_fcs),
        'h2_batt':                  float(h2_batt),
        'h2_equal':                 float(h2_equal),
        'soc_cost':                 float(soc_cost),
        'h2_cost':                  float(h2_cost),
        'fcs_soh_cost':             float(fcs_soh_cost),
        'batt_soh_cost':            float(batt_soh_cost),
        'objective_cost':           float(objective_cost),
        'soc_in_bounds':            int(in_bounds),
        # Catalog term logs (required)
        'term_soc_anchor':          term_soc_anchor,
        'term_fc_surplus_charge':   term_fc_surplus_charge,
        'term_drift_barrier':       term_drift_barrier,
    })
    return reward
