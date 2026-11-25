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

    # --- Catalog term: fc_surplus_charge (charge_sustaining, RESHAPED: linear gate -> quadratic gate) ---
    # OLD (edit base): c * g_linear(SOC) * P_fc_to_batt_kw
    #   g_linear = max(0, SOC - SOC_target + m) / m, m=0.05
    #   Activates from SOC_target - 0.05, fully active at SOC_target (g=1)
    #   Constant drag on FC->battery even at SOC = SOC_target
    #
    # NEW (this candidate): c * g_quad(SOC) * P_fc_to_batt_kw
    #   g_quad = max(0, SOC - SOC_target)^2 / m^2, m=0.05
    #   Zero at SOC <= SOC_target (no drag at target), quadratic above target
    #   Steeper at large excursions (SOC > 0.62), gentler at small ones
    #   Shape change: exponent 1 -> 2, onset moves from SOC_target-m to SOC_target
    #
    # Sizing: at SOC=0.625 (mean above-target), g_quad=0.25 vs g_linear=1.5
    #   New term per step = 0.60 * 0.25 * 2.25 = 0.338 (vs old 0.675)
    #   At SOC=0.640, g_quad=0.64, term = 0.60*0.64*2.25 = 0.864 (vs old 0.81)
    #   Stronger suppression at high SOC excursions, zero drag at target
    #
    # c_fsc raised 0.20 -> 0.60 to keep high-SOC suppression effective
    # despite quadratic gate being weaker near target
    c_fsc = 0.60
    m_fsc = 0.05
    p_batt_w = float(self.P_batt)    # W, + = discharge
    p_mot_w = float(self.P_mot)      # W, motor electrical power
    # FC power into battery (kW): positive only when FC is net-charging battery
    p_fc_to_batt_kw = float(np.maximum(0.0, np.minimum(-p_batt_w, p_mot_w - p_batt_w)) / 1000.0)
    # Quadratic gate: zero at SOC <= SOC_target, quadratic above
    soc_above_target = float(np.maximum(0.0, soc - soc_target))
    g_soc_fsc = float((soc_above_target ** 2) / (m_fsc ** 2))
    term_fc_surplus_charge = float(c_fsc * g_soc_fsc * p_fc_to_batt_kw)

    # soc_cost = sum of all charge-sustaining terms
    # term_soc_anchor is the baseline's soc_cost (soc_anchor)
    soc_cost = term_soc_anchor + term_drift_barrier + term_fc_surplus_charge

    # --- Standard price terms ---
    h2_fcs = float(self.h2_fcs)
    h2_batt = float(self.h2_batt)
    h2_equal = float(self.h2_equal)
    h2_cost = float(self.w_h2 * h2_fcs)
    fcs_soh_cost = float(self.w_fc * float(self.dSOH_FCS))
    batt_soh_cost = float(self.w_batt * float(self.dSOH_batt))

    # --- Catalog term: batt_ohmic (price) ---
    # c * P_batt_loss_kw; c=0.5 reward units per kW-step
    # Mean P_batt_loss_kw = 0.2907 kW -> mean extra cost = 0.145/step
    # Unchanged from edit base: no structural change here
    c_bo = 0.5
    p_batt_loss_kw = float(self.P_batt_loss_kw)
    term_batt_ohmic = float(c_bo * p_batt_loss_kw)

    in_bounds = (soc_low < soc < soc_high)

    # objective_cost: soc_cost + price terms + batt_ohmic
    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost + term_batt_ohmic

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
        # Price term log
        'term_batt_ohmic': float(term_batt_ohmic),
    })
    return reward
