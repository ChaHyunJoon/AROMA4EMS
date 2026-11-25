def get_reward(self):
    soc = float(self.SOC)
    soc_low, soc_high = self.soc_bounds

    # ---------- Charge-sustaining terms (must sum into soc_cost) ----------
    # term_soc_anchor (catalog: soc_anchor) [same as edit_base: symmetric quadratic, k=10 outside bounds]
    soc_err2 = float(np.abs(soc - float(self.SOC_target)) ** 2)
    w_soc_eff = float(np.where((soc >= soc_high) | (soc <= soc_low), float(self.w_soc) * 10.0, float(self.w_soc)))
    term_soc_anchor = w_soc_eff * soc_err2

    # term_drift_barrier (catalog: drift_barrier) [ADDED]
    # Deadband d0 must be < soc_drift_abs_max and checked to be zero for |SOC-SOC_init|<=0.01.
    d0 = 0.01
    drift_abs = float(np.abs(soc - float(self.SOC_init)))
    drift_excess = float(np.maximum(0.0, drift_abs - d0))
    # Coefficient sized to matter per-step (not terminal-only) while staying within DRIFT FACTS range on edit_base rollout.
    c_drift = 500.0
    term_drift_barrier = c_drift * (drift_excess ** 2)

    soc_cost = term_soc_anchor + term_drift_barrier

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
        'term_drift_barrier': float(term_drift_barrier),

        # Keep these four logs truthful for their own terms
        'soc_cost': float(soc_cost),
        'h2_cost': float(h2_cost),
        'fcs_soh_cost': float(fcs_soh_cost),
        'batt_soh_cost': float(batt_soh_cost),

        'objective_cost': float(objective_cost),
        'soc_in_bounds': int(in_bounds),
    })
    return reward
