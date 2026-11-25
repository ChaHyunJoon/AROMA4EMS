def get_reward(self):
    soc = float(self.SOC)
    soc_low, soc_high = self.soc_bounds
    soc_init = float(self.SOC_init)
    soc_target = float(self.SOC_target)

    # ── soc_anchor (catalog: soc_anchor, symmetric quadratic, unchanged shape from edit base) ──
    soc_err = (soc - soc_target) ** 2
    w_soc_step = np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10.0, self.w_soc)
    term_soc_anchor = float(w_soc_step * soc_err)

    # ── drift_barrier (catalog: drift_barrier, NEW — not in edit base) ──
    # Flat inside |SOC - SOC_init| <= 0.025, quadratic beyond.
    # c=60, d0=0.025, p=2.
    # Sizing: at mean drift 0.06 → 60*(0.06-0.025)^2 = 0.0735/step;
    #         over 2778 steps → ~204 reward units (inside [670.3, 24830] combined with fc_surplus_charge).
    # Checked: zero at |SOC-SOC_init|=0.01 ✓, positive at guard edge 0.05 ✓, nondecreasing ✓.
    c_barrier = 60.0
    d0_barrier = 0.025
    soc_abs_dev = float(np.abs(soc - soc_init))
    barrier_excess = float(np.maximum(0.0, soc_abs_dev - d0_barrier))
    term_drift_barrier = c_barrier * barrier_excess ** 2

    # ── fc_surplus_charge (catalog: fc_surplus_charge, NEW — not in edit base) ──
    # Price FC power flowing into the battery when SOC > SOC_target.
    # g(SOC) = max(0, SOC - SOC_target + 0.05) / 0.05, clamped to [0,1] for interpretability
    #   (ramps 0→1 from SOC=0.55 to SOC=0.65, saturates above).
    # P_fc_to_batt_kw = max(0, min(-P_batt, P_mot - P_batt)) / 1000
    # c=0.8; at mean FC->batt 3.37 kW, g=1: 0.8*3.37=2.70/step;
    #   over ~1000 active steps above target: ~2700 reward units.
    # Combined with drift_barrier ~200: total ~2900, inside [670.3, 24830] ✓.
    # Checked: zero while discharging ✓, zero for pure regen (no FC power) ✓,
    #          zero at SOC_target-0.1=0.50 ✓, positive at SOC_target+0.05=0.65 with FC charging ✓,
    #          nondecreasing in SOC and FC charging power ✓.
    m_surplus = 0.05
    g_surplus = float(np.maximum(0.0, soc - soc_target + m_surplus) / m_surplus)
    # Clamp g to [0, 1] — above SOC_target+m it stays at 1, which is fine (nondecreasing)
    # Actually catalog says g nondecreasing, no upper clamp required; leave unclamped for full signal
    p_batt_w = float(self.P_batt)      # W, + = discharge
    p_mot_w = float(self.P_mot)        # W, motor electrical power
    # FC power into battery (kW): positive only when FC is charging the battery
    p_fc_to_batt_kw = float(np.maximum(0.0, np.minimum(-p_batt_w, p_mot_w - p_batt_w))) / 1000.0
    c_surplus = 0.8
    term_fc_surplus_charge = c_surplus * g_surplus * p_fc_to_batt_kw

    # ── soc_cost = sum of all charge-sustaining terms ──
    soc_cost = term_soc_anchor + term_drift_barrier + term_fc_surplus_charge

    # ── standard price terms (unchanged from edit base) ──
    h2_fcs = self.h2_fcs
    h2_batt = self.h2_batt
    h2_equal = self.h2_equal
    h2_cost = self.w_h2 * float(h2_fcs)
    fcs_soh_cost = self.w_fc * float(self.dSOH_FCS)
    batt_soh_cost = self.w_batt * float(self.dSOH_batt)

    in_bounds = (soc_low < soc < soc_high)
    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost
    reward = float(-objective_cost)

    self.info.update({
        'EMS_reward':        reward,
        'h2_fcs':            float(h2_fcs),
        'h2_batt':           float(h2_batt),
        'h2_equal':          float(h2_equal),
        'soc_cost':          float(soc_cost),
        'h2_cost':           float(h2_cost),
        'fcs_soh_cost':      float(fcs_soh_cost),
        'batt_soh_cost':     float(batt_soh_cost),
        'objective_cost':    float(objective_cost),
        'soc_in_bounds':     int(in_bounds),
        # catalog term logs (required)
        'term_soc_anchor':        float(term_soc_anchor),
        'term_drift_barrier':     float(term_drift_barrier),
        'term_fc_surplus_charge': float(term_fc_surplus_charge),
    })
    return reward
