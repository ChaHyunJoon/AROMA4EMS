def get_reward(self):
    soc = float(self.SOC)
    soc_low, soc_high = self.soc_bounds

    # --- soc_anchor [charge_sustaining, term_soc_anchor] ---
    # Symmetric quadratic anchor pulling SOC to target, x10 outside bounds.
    soc_err = (soc - self.SOC_target) ** 2
    w_soc_step = np.where(
        (soc >= soc_high) | (soc <= soc_low),
        self.w_soc * 10.0,
        self.w_soc
    )
    term_soc_anchor = float(w_soc_step * soc_err)

    # --- fc_surplus_charge [charge_sustaining, term_fc_surplus_charge] ---
    # Price FC power flowing into the battery when SOC is above SOC_target - m.
    # Gate g = max(0, SOC - (SOC_target - m)) / m, linear from 0 at SOC_target-m
    # to 1.0 at SOC_target and beyond (uncapped above SOC_target).
    # P_fc_to_batt_kw = max(0, min(-P_batt, P_mot - P_batt)) / 1000
    # Catalog form: c * g(SOC) * P_fc_to_batt_kw
    # c = 0.70, m = 0.05
    _m = 0.05
    _c_surplus = 0.70
    _gate = float(np.maximum(0.0, soc - (float(self.SOC_target) - _m)) / _m)
    _p_batt_w = float(self.P_batt)          # W, + = discharge
    _p_mot_w  = float(self.P_mot)           # W, motor electrical power
    # FC power into battery (kW): positive only when FC is charging battery
    _p_fc_to_batt_kw = float(
        np.maximum(0.0, np.minimum(-_p_batt_w, _p_mot_w - _p_batt_w)) / 1000.0
    )
    term_fc_surplus_charge = float(_c_surplus * _gate * _p_fc_to_batt_kw)

    # soc_cost = sum of charge-sustaining terms
    soc_cost = term_soc_anchor + term_fc_surplus_charge

    # --- h2_cost [price] ---
    h2_fcs  = self.h2_fcs
    h2_batt = self.h2_batt
    h2_equal = self.h2_equal
    h2_cost = float(self.w_h2 * h2_fcs)

    # --- fcs_soh_cost [price] ---
    fcs_soh_cost = float(self.w_fc * float(self.dSOH_FCS))

    # --- batt_soh_cost [price] ---
    batt_soh_cost = float(self.w_batt * float(self.dSOH_batt))

    in_bounds = bool(soc_low < soc < soc_high)

    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost
    reward = float(-objective_cost)

    self.info.update({
        'EMS_reward':            reward,
        'h2_fcs':                float(h2_fcs),
        'h2_batt':               float(h2_batt),
        'h2_equal':              float(h2_equal),
        'soc_cost':              float(soc_cost),
        'h2_cost':               float(h2_cost),
        'fcs_soh_cost':          float(fcs_soh_cost),
        'batt_soh_cost':         float(batt_soh_cost),
        'objective_cost':        float(objective_cost),
        'soc_in_bounds':         int(in_bounds),
        # Catalog term logs (required)
        'term_soc_anchor':       term_soc_anchor,
        'term_fc_surplus_charge': term_fc_surplus_charge,
    })
    return reward
