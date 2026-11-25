def get_reward(self):
    soc = float(self.SOC)
    soc_low, soc_high = self.soc_bounds

    # ---------- Charge-sustaining terms (must sum into soc_cost) ----------
    # term_soc_anchor (catalog: soc_anchor), RESHAPED to be asymmetric:
    # penalize SOC above target more than below to stop the observed +SOC drift.
    soc_target = float(self.SOC_target)
    soc_err_up = float(np.maximum(0.0, soc - soc_target))
    soc_err_down = float(np.maximum(0.0, soc_target - soc))

    # bounds multiplier k=10 exactly as edit_base behavior (stronger near SOC limits)
    k_bounds = 10.0
    w_bounds = float(np.where((soc >= soc_high) | (soc <= soc_low), k_bounds, 1.0))

    # Asymmetry: overcharge is the failure mode (reward_id 17afbf... ended +0.093 SOC),
    # so make c_up > c_down while keeping p=2.
    c_down = float(self.w_soc) * 1.0
    c_up = float(self.w_soc) * 4.0
    p = 2.0

    term_soc_anchor = w_bounds * (c_up * (soc_err_up ** p) + c_down * (soc_err_down ** p))
    soc_cost = term_soc_anchor

    # ---------- Objective price terms (unchanged) ----------
    h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal
    h2_cost = float(self.w_h2) * float(h2_fcs)
    fcs_soh_cost = float(self.w_fc) * float(self.dSOH_FCS)
    batt_soh_cost = float(self.w_batt) * float(self.dSOH_batt)

    in_bounds = (soc_low < soc < soc_high)
    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost
    reward = float(-objective_cost)

    # ---------- Logging ----------
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
