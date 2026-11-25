def get_reward(self):
    soc = float(self.SOC)
    soc_low, soc_high = self.soc_bounds

    # -----------------------
    # Charge-sustaining terms (must sum into soc_cost)
    # -----------------------

    # term_soc_anchor (catalog: soc_anchor)
    soc_err = float(np.abs(soc - float(self.SOC_target))) ** 2
    w_soc_eff = float(np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10.0, self.w_soc))
    term_soc_anchor = w_soc_eff * soc_err

    # term_drift_barrier (catalog: drift_barrier)
    d0 = 0.025  # deadband half-width (< soc_drift_abs_max = 0.05)
    p = 2.0
    c_drift = 1100.0
    drift_excess = max(0.0, abs(soc - float(self.SOC_init)) - d0)
    term_drift_barrier = c_drift * (drift_excess ** p)

    # term_fc_surplus_charge (catalog: fc_surplus_charge)
    # Price FC power pushed into the battery while SOC is already high (measured drift mechanism).
    P_batt_w = float(self.P_batt)   # W, + = discharge, so charging => -P_batt_w > 0
    P_mot_w = float(self.P_mot)     # W, motor electrical power
    P_fc_to_batt_w = max(0.0, min(-P_batt_w, P_mot_w - P_batt_w))
    P_fc_to_batt_kw = P_fc_to_batt_w / 1000.0

    m_surplus = 0.05
    soc_gate_surplus = max(0.0, (soc - (float(self.SOC_target) - m_surplus)) / m_surplus)  # nondecreasing
    c_surplus = 4.0
    term_fc_surplus_charge = c_surplus * soc_gate_surplus * P_fc_to_batt_kw

    # term_fc_peak_shave (catalog: fc_peak_shave)  [ADDED STRUCTURAL TERM]
    # When SOC is not low, discourage high FC power so the battery carries peaks and SOC is pulled back by soc terms.
    P_cap = 15.0  # kW (near the efficient band peak at ~10-15 kW in EFFICIENCY FACTS)
    P_fcs_kw = float(self.P_FCS)
    peak_excess_kw = max(0.0, P_fcs_kw - P_cap)

    m_peak = 0.05  # ensure gate is 0 at/below SOC_target - 0.05
    soc_gate_peak = max(0.0, (soc - (float(self.SOC_target) - m_peak)) / m_peak)  # nondecreasing, >=0
    c_peak = 3.0   # reward-units per (kW-step) of FC power above cap when SOC is high
    term_fc_peak_shave = c_peak * soc_gate_peak * peak_excess_kw

    soc_cost = term_soc_anchor + term_drift_barrier + term_fc_surplus_charge + term_fc_peak_shave

    # -----------------------
    # Price-aligned operating-cost proxy terms (unchanged structure)
    # -----------------------
    h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal
    h2_cost = float(self.w_h2) * float(h2_fcs)

    fcs_soh_cost = float(self.w_fc) * float(self.dSOH_FCS)
    batt_soh_cost = float(self.w_batt) * float(self.dSOH_batt)

    in_bounds = (soc_low < soc < soc_high)

    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost
    reward = float(-objective_cost)

    # -----------------------
    # Required logging (log every catalog term as term_<id>)
    # -----------------------
    self.info.update({
        'EMS_reward': reward,
        'h2_fcs': float(h2_fcs),
        'h2_batt': float(h2_batt),
        'h2_equal': float(h2_equal),

        # catalog terms
        'term_soc_anchor': float(term_soc_anchor),
        'term_drift_barrier': float(term_drift_barrier),
        'term_fc_surplus_charge': float(term_fc_surplus_charge),
        'term_fc_peak_shave': float(term_fc_peak_shave),

        # aggregated costs
        'soc_cost': float(soc_cost),
        'h2_cost': float(h2_cost),
        'fcs_soh_cost': float(fcs_soh_cost),
        'batt_soh_cost': float(batt_soh_cost),
        'objective_cost': float(objective_cost),

        'soc_in_bounds': int(in_bounds),
    })
    return reward
