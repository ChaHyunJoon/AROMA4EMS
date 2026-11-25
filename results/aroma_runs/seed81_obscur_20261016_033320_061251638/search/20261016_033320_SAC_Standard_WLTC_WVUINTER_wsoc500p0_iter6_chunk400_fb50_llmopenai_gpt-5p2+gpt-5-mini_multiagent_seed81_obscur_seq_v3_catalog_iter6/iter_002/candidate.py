def get_reward(self):
    soc = float(self.SOC)
    soc_low, soc_high = self.soc_bounds

    # ---------- Charge-sustaining terms (must sum into soc_cost) ----------
    # term_soc_anchor (catalog: soc_anchor; symmetric quadratic with bounds multiplier k=10)
    soc_err2 = float(np.abs(soc - float(self.SOC_target)) ** 2)
    w_soc_eff = float(np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10.0, self.w_soc))
    term_soc_anchor = w_soc_eff * soc_err2

    # term_fc_surplus_charge (catalog: fc_surplus_charge)
    # g(SOC)=max(0,(SOC - SOC_target + 0.10)/0.10), nondecreasing; zero at/below SOC_target-0.10
    m = 0.10
    g_soc = float(np.maximum(0.0, (soc - float(self.SOC_target) + m) / m))

    # P_fc_to_batt_kw = max(0, min(-P_batt, P_mot - P_batt)) / 1000  (per catalog)
    # self.P_batt, self.P_mot are in W; self.P_batt > 0 means discharge, < 0 means charging
    P_batt_w = float(self.P_batt)
    P_mot_w = float(self.P_mot)
    fc_to_batt_w = float(np.maximum(0.0, np.minimum(-P_batt_w, P_mot_w - P_batt_w)))
    P_fc_to_batt_kw = fc_to_batt_w / 1000.0

    c_fc_surplus = 1.5  # reward_units per (kW*step), sized per orchestrator (DRIFT FACTS range)
    term_fc_surplus_charge = c_fc_surplus * g_soc * P_fc_to_batt_kw

    soc_cost = term_soc_anchor + term_fc_surplus_charge

    # ---------- Objective price terms (unchanged) ----------
    h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal
    h2_cost = float(self.w_h2) * float(h2_fcs)

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
        'term_fc_surplus_charge': float(term_fc_surplus_charge),

        # Keep these four logs truthful for their own terms
        'soc_cost': float(soc_cost),
        'h2_cost': float(h2_cost),
        'fcs_soh_cost': float(fcs_soh_cost),
        'batt_soh_cost': float(batt_soh_cost),

        'objective_cost': float(objective_cost),
        'soc_in_bounds': int(in_bounds),
    })
    return reward
