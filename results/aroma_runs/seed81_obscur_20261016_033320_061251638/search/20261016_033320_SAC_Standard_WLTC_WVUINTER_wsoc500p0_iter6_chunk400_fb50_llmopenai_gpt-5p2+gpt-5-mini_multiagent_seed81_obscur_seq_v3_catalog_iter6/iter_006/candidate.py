def get_reward(self):
    soc = float(self.SOC)
    soc_low, soc_high = self.soc_bounds

    # ---------- Charge-sustaining terms (must sum into soc_cost) ----------
    # term_soc_anchor (catalog: soc_anchor) RESHAPED: asymmetric quadratic anchor
    # Mechanism: penalize SOC depletion (below target) more than overcharge to discourage
    # battery rundown that leads to repeated FC off->on restarts (high dSOH_FCS via starts).
    soc_target = float(self.SOC_target)

    soc_err_up = float(np.maximum(0.0, soc - soc_target))
    soc_err_down = float(np.maximum(0.0, soc_target - soc))

    # Bounds multiplier k=10 exactly as before
    k_bounds = 10.0
    bounds_mult = float(np.where((soc >= soc_high) | (soc <= soc_low), k_bounds, 1.0))

    # Asymmetry (structural reshape of soc_anchor): c_down > c_up
    # Keep p=2 (quadratic) for smooth gradients.
    p = 2.0
    c_up = 1.5 * float(self.w_soc)
    c_down = 4.0 * float(self.w_soc)

    term_soc_anchor = bounds_mult * (c_up * (soc_err_up ** p) + c_down * (soc_err_down ** p))
    soc_cost = term_soc_anchor

    # ---------- Objective price terms (unchanged) ----------
    h2_fcs = float(self.h2_fcs)
    h2_batt = float(self.h2_batt)
    h2_equal = float(self.h2_equal)

    h2_cost = float(self.w_h2) * h2_fcs
    fcs_soh_cost = float(self.w_fc) * float(self.dSOH_FCS)
    batt_soh_cost = float(self.w_batt) * float(self.dSOH_batt)

    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost
    reward = float(-objective_cost)

    in_bounds = (soc_low < soc < soc_high)

    # ---------- Required logging ----------
    self.info.update({
        'EMS_reward': reward,
        'h2_fcs': float(h2_fcs),
        'h2_batt': float(h2_batt),
        'h2_equal': float(h2_equal),

        # Catalog-term logs (plain values, before summing)
        'term_soc_anchor': float(term_soc_anchor),

        # Keep these four logs truthful for their own terms
        'soc_cost': float(soc_cost),
        'h2_cost': float(h2_cost),
        'fcs_soh_cost': float(fcs_soh_cost),
        'batt_soh_cost': float(batt_soh_cost),

        'objective_cost': float(objective_cost),
        'soc_in_bounds': int(in_bounds),
    })
    return reward
