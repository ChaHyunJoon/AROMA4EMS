def get_reward(self):
    soc = float(self.SOC)
    soc_low, soc_high = self.soc_bounds

    # -----------------------
    # Charge-sustaining terms (must sum exactly into soc_cost)
    # -----------------------

    # term_soc_anchor (catalog: soc_anchor) — baseline symmetric quadratic anchor to SOC_target,
    # with 10x penalty only when outside SOC operating bounds.
    soc_err = float(np.abs(soc - float(self.SOC_target))) ** 2
    w_soc_eff = float(np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10.0, self.w_soc))
    term_soc_anchor = w_soc_eff * soc_err

    # term_drift_barrier (catalog: drift_barrier) — quadratic barrier beyond a deadband around SOC_init.
    # Asymmetric: penalize over-charge drift (SOC above SOC_init) more than depletion drift, matching the
    # measured failure mode (+SOC drift).
    d0 = 0.02  # deadband half-width (< soc_drift_abs_max = 0.05)
    p = 2.0

    soc_init = float(self.SOC_init)
    drift_up_excess = max(0.0, (soc - soc_init) - d0)
    drift_down_excess = max(0.0, (soc_init - soc) - d0)

    c_up = 1600.0   # reward-units per (SOC^2)-step beyond deadband (overcharge side)
    c_down = 900.0  # reward-units per (SOC^2)-step beyond deadband (depletion side)
    term_drift_barrier = c_up * (drift_up_excess ** p) + c_down * (drift_down_excess ** p)

    soc_cost = term_soc_anchor + term_drift_barrier

    # -----------------------
    # Price-aligned operating-cost proxy terms (unchanged structure/weights)
    # -----------------------
    h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal
    h2_cost = float(self.w_h2) * float(h2_fcs)

    # Cost of fuel cell degradation (scaled)
    fcs_soh_cost = float(self.w_fc) * float(self.dSOH_FCS)

    # Cost of battery degradation (scaled)
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

        # aggregated costs
        'soc_cost': float(soc_cost),
        'h2_cost': float(h2_cost),
        'fcs_soh_cost': float(fcs_soh_cost),
        'batt_soh_cost': float(batt_soh_cost),
        'objective_cost': float(objective_cost),

        'soc_in_bounds': int(in_bounds),
    })
    return reward
