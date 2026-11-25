def get_reward(self):
    soc = float(self.SOC)
    soc_low, soc_high = self.soc_bounds
    soc_init = float(self.SOC_init)
    soc_target = float(self.SOC_target)

    # ── term_soc_anchor (catalog: soc_anchor, symmetric quadratic, same shape as edit base) ──
    soc_err = (soc - soc_target) ** 2
    w_soc_step = np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10.0, self.w_soc)
    term_soc_anchor = float(w_soc_step * soc_err)

    # ── term_drift_barrier (catalog: drift_barrier) ──
    # Flat inside |SOC - SOC_init| <= 0.025, quadratic beyond.
    # c=60, d0=0.025, p=2.
    # Sizing: at mean drift 0.06 over 2778 steps → 60*(0.06-0.025)^2 * 2778 ≈ 204 reward units.
    # Checked: zero at |SOC-SOC_init|=0.01 ✓, positive at guard edge 0.05 ✓, nondecreasing ✓.
    c_barrier = 60.0
    d0_barrier = 0.025
    soc_abs_dev = float(np.abs(soc - soc_init))
    barrier_excess = float(np.maximum(0.0, soc_abs_dev - d0_barrier))
    term_drift_barrier = c_barrier * barrier_excess ** 2

    # ── term_fc_surplus_charge (catalog: fc_surplus_charge) ──
    # Price FC power flowing into the battery when SOC > SOC_target.
    # g(SOC) = max(0, SOC - SOC_target + m) / m, m=0.05; ramps 0→1 from SOC=0.55 to SOC=0.65.
    # P_fc_to_batt_kw = max(0, min(-P_batt, P_mot - P_batt)) / 1000
    # c=0.8; at mean FC->batt 3.37 kW, g≈1, ~1000 steps above target: ~2696 reward units.
    # Checked: zero while discharging ✓, zero for pure regen ✓,
    #          zero at SOC_target-0.1=0.50 ✓, positive at SOC_target+0.05 with FC charging ✓,
    #          nondecreasing in SOC and FC charging power ✓.
    m_surplus = 0.05
    g_surplus = float(np.maximum(0.0, soc - soc_target + m_surplus) / m_surplus)
    p_batt_w = float(self.P_batt)       # W, + = discharge
    p_mot_w = float(self.P_mot)         # W, motor electrical power
    p_fc_to_batt_kw = float(np.maximum(0.0, np.minimum(-p_batt_w, p_mot_w - p_batt_w))) / 1000.0
    c_surplus = 0.8
    term_fc_surplus_charge = c_surplus * g_surplus * p_fc_to_batt_kw

    # ── soc_cost = sum of all charge-sustaining terms ──
    soc_cost = term_soc_anchor + term_drift_barrier + term_fc_surplus_charge

    # ── standard price terms ──
    h2_fcs = self.h2_fcs
    h2_batt = self.h2_batt
    h2_equal = self.h2_equal
    h2_cost = self.w_h2 * float(h2_fcs)
    fcs_soh_cost = self.w_fc * float(self.dSOH_FCS)
    batt_soh_cost = self.w_batt * float(self.dSOH_batt)

    # ── term_fc_efficiency_gap (catalog: fc_efficiency_gap, NEW — not in edit base or champion) ──
    # Price hydrogen burned below the FC's peak efficiency (eta_ref=0.602 at 10-15 kW).
    # eta = P_FCS / (120 * h2_fcs) when h2_fcs > 0, else 0.
    # c=40; at 4 kW (eta=0.484, gap=0.196, h2_fcs≈0.0267 g/step): 40*0.0267*0.196/0.602≈0.347/step.
    # At 2 kW (eta=0.213, gap=0.646, h2_fcs≈0.0117 g/step): 40*0.0117*0.646/0.602≈0.501/step.
    # Mean over 1038 low-efficiency steps ≈ 0.40/step → ~416 reward units total.
    # Mean over full episode ≈ 0.12/step (within price-deviation tolerance).
    # Incentivizes FC to operate at 8-15 kW efficient band or turn off, reducing fc_low_power_soh_loss.
    # Checked: zero with FC off (h2_fcs=0) ✓, zero at eta>=eta_ref ✓, nonnegative ✓,
    #          nonincreasing in eta at fixed hydrogen ✓, enters objective_cost ✓.
    eta_ref = 0.602
    c_eff_gap = 40.0
    p_fcs_kw = float(self.P_FCS)
    h2_fcs_val = float(h2_fcs)
    # eta = P_FCS / (120 * h2_fcs); 120 kJ/g is H2 LHV, 1-s steps
    eta_fc = p_fcs_kw / (120.0 * h2_fcs_val) if h2_fcs_val > 0.0 else eta_ref
    efficiency_gap = float(np.maximum(0.0, eta_ref - eta_fc) / eta_ref)
    term_fc_efficiency_gap = c_eff_gap * h2_fcs_val * efficiency_gap

    in_bounds = (soc_low < soc < soc_high)
    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost + term_fc_efficiency_gap
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
        'term_soc_anchor': float(term_soc_anchor),
        'term_drift_barrier': float(term_drift_barrier),
        'term_fc_surplus_charge': float(term_fc_surplus_charge),
        'term_fc_efficiency_gap': float(term_fc_efficiency_gap),
    })
    return reward
