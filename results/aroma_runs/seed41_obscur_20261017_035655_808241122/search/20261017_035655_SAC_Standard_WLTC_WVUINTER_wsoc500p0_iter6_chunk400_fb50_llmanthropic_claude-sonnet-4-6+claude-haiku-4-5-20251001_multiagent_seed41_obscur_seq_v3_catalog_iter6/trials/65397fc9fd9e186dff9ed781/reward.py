def get_reward(self):
    soc = float(self.SOC)
    soc_init = float(self.SOC_init)
    soc_target = float(self.SOC_target)
    soc_low, soc_high = self.soc_bounds

    # --- Catalog term: soc_anchor (charge_sustaining) ---
    # Symmetric quadratic anchor: c_up = c_down = w_soc, p = 2, x10 outside bounds
    soc_err_sq = (soc - soc_target) ** 2
    w_soc_eff = float(np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10.0, self.w_soc))
    term_soc_anchor = float(w_soc_eff * soc_err_sq)

    # --- Catalog term: drift_barrier (charge_sustaining) ---
    # c * max(0, |SOC - SOC_init| - d0)^2, d0=0.025, c=2000
    # Flat inside +-0.025 of SOC_init, steep beyond; symmetric
    d0 = 0.025
    c_db = 2000.0
    soc_abs_drift = float(np.abs(soc - soc_init))
    drift_excess = float(np.maximum(0.0, soc_abs_drift - d0))
    term_drift_barrier = float(c_db * drift_excess ** 2)

    # --- Catalog term: fc_surplus_charge (charge_sustaining) ---
    # c * g(SOC) * P_fc_to_batt_kw
    # g(SOC) = max(0, SOC - SOC_target + m) / m, m=0.05
    # P_fc_to_batt_kw = max(0, min(-P_batt, P_mot - P_batt)) / 1000
    # Zero while discharging, zero for pure regen, zero at SOC <= SOC_target - 0.05
    c_fsc = 0.20
    m_fsc = 0.05
    p_batt_w = float(self.P_batt)    # W, + = discharge
    p_mot_w = float(self.P_mot)      # W, motor electrical power
    p_fc_to_batt_kw = float(np.maximum(0.0, np.minimum(-p_batt_w, p_mot_w - p_batt_w)) / 1000.0)
    g_soc_fsc = float(np.maximum(0.0, soc - soc_target + m_fsc) / m_fsc)
    term_fc_surplus_charge = float(c_fsc * g_soc_fsc * p_fc_to_batt_kw)

    # soc_cost = sum of all charge-sustaining terms
    soc_cost = term_soc_anchor + term_drift_barrier + term_fc_surplus_charge

    # --- Standard price terms ---
    h2_fcs = float(self.h2_fcs)
    h2_batt = float(self.h2_batt)
    h2_equal = float(self.h2_equal)
    h2_cost = float(self.w_h2 * h2_fcs)
    fcs_soh_cost = float(self.w_fc * float(self.dSOH_FCS))
    batt_soh_cost = float(self.w_batt * float(self.dSOH_batt))

    # --- Catalog term: batt_ohmic (price, extra term) ---
    # c * P_batt_loss_kw; c=0.5 reward units per kW-step
    # Mean P_batt_loss_kw = 0.2907 kW -> mean extra cost = 0.145/step
    c_bo = 0.5
    p_batt_loss_kw = float(self.P_batt_loss_kw)
    term_batt_ohmic = float(c_bo * p_batt_loss_kw)

    # --- Catalog term: fc_efficiency_gap (price, ADDED - absent from edit base) ---
    # c * h2_fcs * max(0, eta_ref - eta) / eta_ref
    # eta = P_FCS / (120 * h2_fcs) when h2_fcs > 0, else 0
    # eta_ref = 0.602 (peak efficiency at 10-15 kW band, from EFFICIENCY FACTS)
    # 120 kJ/g is H2 LHV; 1-s steps so h2_fcs is g per step
    # Sizing: at 2 kW (eta=0.364), gap=0.395, h2~0.0458 g/step -> term = 8*0.0458*0.395 = 0.145/step
    # At 10-15 kW (eta>=0.602), gap=0 -> term=0
    # Mean over all steps ~0.035/step; well within price-deviation tolerance
    c_feg = 8.0
    eta_ref = 0.602
    p_fcs_kw = float(self.P_FCS)
    # eta = P_FCS / (120 * h2_fcs); guard h2_fcs > 0 to avoid division by zero
    # When h2_fcs = 0 (FC off), term = 0 by catalog definition
    h2_fcs_safe = float(np.maximum(h2_fcs, 1e-9))
    eta_fcs = float(np.where(h2_fcs > 1e-9, p_fcs_kw / (120.0 * h2_fcs_safe), eta_ref))
    efficiency_gap = float(np.maximum(0.0, eta_ref - eta_fcs) / eta_ref)
    # When FC is off (h2_fcs=0), term is zero: h2_fcs * anything = 0
    term_fc_efficiency_gap = float(c_feg * h2_fcs * efficiency_gap)

    in_bounds = bool((soc_low < soc < soc_high))

    # objective_cost: four core terms + two extra price terms (batt_ohmic, fc_efficiency_gap)
    objective_cost = (soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost
                      + term_batt_ohmic + term_fc_efficiency_gap)

    reward = float(-objective_cost)

    self.info.update({
        'EMS_reward': reward,
        'h2_fcs': float(h2_fcs),
        'h2_batt': float(h2_batt),
        'h2_equal': float(h2_equal),
        'soc_cost': float(soc_cost),
        'h2_cost': float(h2_cost),
        'fcs_soh_cost': float(fcs_soh_cost),
        'batt_soh_cost': float(batt_soh_cost),
        'objective_cost': float(objective_cost),
        'soc_in_bounds': int(in_bounds),
        # Catalog term logs (charge-sustaining terms sum to soc_cost)
        'term_soc_anchor': float(term_soc_anchor),
        'term_drift_barrier': float(term_drift_barrier),
        'term_fc_surplus_charge': float(term_fc_surplus_charge),
        # Extra price terms
        'term_batt_ohmic': float(term_batt_ohmic),
        'term_fc_efficiency_gap': float(term_fc_efficiency_gap),
    })
    return reward
