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
    # Checked: zero for |SOC - SOC_init| <= 0.025, positive at |drift| = 0.05 (guard)
    d0 = 0.025
    c_db = 2000.0
    soc_abs_drift = float(np.abs(soc - soc_init))
    drift_excess = float(np.maximum(0.0, soc_abs_drift - d0))
    term_drift_barrier = float(c_db * drift_excess ** 2)

    # --- Catalog term: fc_surplus_charge (charge_sustaining, RESHAPED: linear gate -> quadratic gate) ---
    # OLD (edit base): c * g_linear(SOC) * P_fc_to_batt_kw
    #   g_linear = max(0, SOC - SOC_target + m) / m, m=0.05
    #   Onset at SOC_target - 0.05, fully active (g=1) at SOC_target
    #   Constant drag on FC->battery even at SOC = SOC_target
    #
    # NEW (this candidate): c * g_quad(SOC) * P_fc_to_batt_kw
    #   g_quad = max(0, SOC - SOC_target)^2 / m^2, m=0.05
    #   Zero at SOC <= SOC_target (no drag at target), quadratic above target
    #   Steeper at large excursions (SOC > 0.62), zero drag at SOC_target
    #   Shape change: exponent 1 -> 2, onset moves from SOC_target-m to SOC_target
    #
    # Sizing: at SOC=0.625 (mean above-target from DRIFT FACTS):
    #   g_quad = (0.025/0.05)^2 = 0.25; mean FC->batt power above target = 4.39 kW
    #   term = 0.60 * 0.25 * 4.39 = 0.66/step
    #   At SOC=0.640: g_quad = (0.040/0.05)^2 = 0.64; term = 0.60*0.64*4.39 = 1.69/step
    #   Stronger suppression at high SOC excursions, zero drag at target
    #
    # c_fsc raised 0.20 -> 0.60 to keep high-SOC suppression effective
    # despite quadratic gate being zero at target (same sizing as champion iteration 5)
    #
    # Catalog checks:
    #   zero while discharging (p_fc_to_batt_kw=0): YES
    #   zero for pure regeneration (no FC power): YES (P_fc_to_batt_kw=0 when FC off)
    #   zero at SOC_target - 0.1 (SOC <= SOC_target): YES (g_quad=0)
    #   positive at SOC_target + 0.05 with FC charging: g_quad=(0.05/0.05)^2=1.0, YES
    #   nondecreasing in SOC and FC charging power: YES (quadratic in SOC above target)
    c_fsc = 0.60
    m_fsc = 0.05
    p_batt_w = float(self.P_batt)    # W, + = discharge
    p_mot_w = float(self.P_mot)      # W, motor electrical power
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

    # --- Catalog term: batt_ohmic (price, extra term) ---
    # c * P_batt_loss_kw; c=0.5 reward units per kW-step
    # Mean P_batt_loss_kw = 0.2907 kW -> mean extra cost = 0.145/step
    # Prices battery round-trip loss not seen by other terms
    c_bo = 0.5
    p_batt_loss_kw = float(self.P_batt_loss_kw)
    term_batt_ohmic = float(c_bo * p_batt_loss_kw)

    # --- Catalog term: fc_efficiency_gap (price, present in edit base, unchanged) ---
    # c * h2_fcs * max(0, eta_ref - eta) / eta_ref
    # eta = P_FCS / (120 * h2_fcs) when h2_fcs > 0, else 0
    # eta_ref = 0.602 (peak efficiency at 10-15 kW band, from EFFICIENCY FACTS)
    # 120 kJ/g is H2 LHV; 1-s steps so h2_fcs is g per step
    # When FC is off (h2_fcs=0), term is zero: h2_fcs * anything = 0
    # Catalog checks:
    #   zero with FC off (h2_fcs=0): YES
    #   zero at eta >= eta_ref: YES
    #   nonnegative: YES
    #   nonincreasing in eta at fixed hydrogen: YES
    c_feg = 8.0
    eta_ref = 0.602
    p_fcs_kw = float(self.P_FCS)
    h2_fcs_safe = float(np.maximum(h2_fcs, 1e-9))
    eta_fcs = float(np.where(h2_fcs > 1e-9, p_fcs_kw / (120.0 * h2_fcs_safe), eta_ref))
    efficiency_gap = float(np.maximum(0.0, eta_ref - eta_fcs) / eta_ref)
    # When h2_fcs=0, h2_fcs * efficiency_gap = 0 (FC off, no cost)
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
