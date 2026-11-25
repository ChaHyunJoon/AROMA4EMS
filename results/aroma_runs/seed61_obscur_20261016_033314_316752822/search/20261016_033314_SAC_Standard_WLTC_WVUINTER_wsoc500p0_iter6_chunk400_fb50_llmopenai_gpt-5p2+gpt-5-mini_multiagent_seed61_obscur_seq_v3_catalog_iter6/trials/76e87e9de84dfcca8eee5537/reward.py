def get_reward(self):
    soc = float(self.SOC)
    soc_low, soc_high = self.soc_bounds

    # -------------------------
    # Charge-sustaining terms (CATALOG)
    # soc_cost MUST equal the sum of the logged catalog terms.
    # -------------------------
    # (1) soc_anchor (existing, but scaled per orchestrator term_ratio soc_cost = 7.0)
    soc_err = (np.abs(soc - float(self.SOC_target))) ** 2
    w_soc = np.where((soc >= float(soc_high)) | (soc <= float(soc_low)),
                     float(self.w_soc) * 10.0,
                     float(self.w_soc))
    term_soc_anchor_base = float(w_soc * soc_err)
    term_soc_anchor = 7.0 * term_soc_anchor_base  # orchestrator-required ratio

    # (2) fc_surplus_charge (existing in edit_base; keep unchanged)
    # FC power into the battery: max(0, min(-P_batt, P_mot - P_batt)) / 1000 [kW]
    P_batt_w = float(self.P_batt)   # + = discharge, - = charge
    P_mot_w = float(self.P_mot)
    P_fc_to_batt_w = max(0.0, min(-P_batt_w, P_mot_w - P_batt_w))
    P_fc_to_batt_kw = P_fc_to_batt_w / 1000.0

    # g(SOC): 0 at/below (SOC_target - m), linear ramp to 1 at SOC_target, nondecreasing above
    m = 0.05
    g_soc = max(0.0, soc - float(self.SOC_target) + m) / m

    c_surplus = 0.005  # reward-units per (kW-step) times g(SOC)
    term_fc_surplus_charge = float(c_surplus * g_soc * P_fc_to_batt_kw)

    # (3) drift_barrier (NEW catalog term; required change_spec)
    # Per-step penalty on sustained offset from SOC_init beyond a deadband.
    d0 = 0.02  # deadband (< soc_drift_abs_max=0.05)
    drift_excess = max(0.0, abs(soc - float(self.SOC_init)) - d0)
    c_drift = 2.0e5
    term_drift_barrier = float(c_drift * (drift_excess ** 2.0))

    soc_cost = float(term_soc_anchor + term_fc_surplus_charge + term_drift_barrier)

    # -------------------------
    # Price / wear terms (unchanged per orchestrator)
    # -------------------------
    h2_fcs = float(self.h2_fcs)
    h2_batt = float(self.h2_batt)
    h2_equal = float(self.h2_equal)

    h2_cost = float(self.w_h2) * h2_fcs
    fcs_soh_cost = float(self.w_fc) * float(self.dSOH_FCS)
    batt_soh_cost = float(self.w_batt) * float(self.dSOH_batt)

    in_bounds = (float(soc_low) < soc < float(soc_high))

    objective_cost = float(soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost)
    reward = float(-objective_cost)

    # -------------------------
    # Logging (required + every catalog term)
    # -------------------------
    self.info.update({
        'EMS_reward': reward,
        'h2_fcs': h2_fcs,
        'h2_batt': h2_batt,
        'h2_equal': h2_equal,

        # Catalog term logs (plain values used in soc_cost sum)
        'term_soc_anchor': float(term_soc_anchor),
        'term_fc_surplus_charge': float(term_fc_surplus_charge),
        'term_drift_barrier': float(term_drift_barrier),

        'soc_cost': float(soc_cost),
        'h2_cost': float(h2_cost),
        'fcs_soh_cost': float(fcs_soh_cost),
        'batt_soh_cost': float(batt_soh_cost),
        'objective_cost': float(objective_cost),
        'soc_in_bounds': int(in_bounds),
    })
    return reward
