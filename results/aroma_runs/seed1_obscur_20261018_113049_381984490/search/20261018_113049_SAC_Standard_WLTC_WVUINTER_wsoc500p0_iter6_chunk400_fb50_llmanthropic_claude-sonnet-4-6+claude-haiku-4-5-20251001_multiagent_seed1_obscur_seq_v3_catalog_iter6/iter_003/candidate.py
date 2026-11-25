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
    # Catalog form: c * g(SOC) * P_fc_to_batt_kw
    # g = max(0, SOC - (SOC_target - m)) / m, linear from 0 at SOC_target-m upward
    # c = 0.70, m = 0.05
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

    # soc_cost = sum of charge-sustaining terms
    soc_cost = term_soc_anchor + term_fc_surplus_charge

    # --- h2_cost [price] ---
    h2_fcs = self.h2_fcs
    h2_batt = self.h2_batt
    h2_equal = self.h2_equal
    h2_cost = float(self.w_h2 * h2_fcs)

    # --- fcs_soh_cost [price] ---
    fcs_soh_cost = float(self.w_fc * float(self.dSOH_FCS))

    # --- batt_soh_cost [price] ---
    batt_soh_cost = float(self.w_batt * float(self.dSOH_batt))

    # --- term_fc_efficiency_gap [price, fc_efficiency_gap] ---
    # Price hydrogen burned below the FC's efficient operating point.
    # Catalog form: c * h2_fcs * max(0, eta_ref - eta) / eta_ref
    # eta = P_FCS / (120 * h2_fcs) when h2_fcs > 0, else 0
    # eta_ref = 0.602 (peak efficiency at 10-15 kW from measured data)
    # c = 5.0
    _eta_ref = 0.602
    _c_eff = 5.0
    _h2_fcs_val = float(h2_fcs)
    _p_fcs_kw = float(self.P_FCS)
    # Guard against division by zero when FC is off (h2_fcs = 0)
    _eta = (_p_fcs_kw / (120.0 * _h2_fcs_val)) if _h2_fcs_val > 0.0 else _eta_ref
    _eff_gap = float(np.maximum(0.0, _eta_ref - _eta) / _eta_ref)
    term_fc_efficiency_gap = float(_c_eff * _h2_fcs_val * _eff_gap)

    in_bounds = bool(soc_low < soc < soc_high)

    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost + term_fc_efficiency_gap
    reward = float(-objective_cost)

    self.info.update({
        'EMS_reward':              reward,
        'h2_fcs':                  float(h2_fcs),
        'h2_batt':                 float(h2_batt),
        'h2_equal':                float(h2_equal),
        'soc_cost':                float(soc_cost),
        'h2_cost':                 float(h2_cost),
        'fcs_soh_cost':            float(fcs_soh_cost),
        'batt_soh_cost':           float(batt_soh_cost),
        'objective_cost':          float(objective_cost),
        'soc_in_bounds':           int(in_bounds),
        # Catalog term logs (required)
        'term_soc_anchor':         float(term_soc_anchor),
        'term_fc_surplus_charge':  float(term_fc_surplus_charge),
        'term_fc_efficiency_gap':  float(term_fc_efficiency_gap),
    })
    return reward
