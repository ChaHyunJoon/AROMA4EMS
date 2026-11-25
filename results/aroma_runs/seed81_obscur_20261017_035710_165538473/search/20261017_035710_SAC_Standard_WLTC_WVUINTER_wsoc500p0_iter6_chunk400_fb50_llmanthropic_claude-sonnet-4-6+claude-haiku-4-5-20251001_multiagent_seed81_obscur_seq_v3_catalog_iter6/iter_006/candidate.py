def get_reward(self):
    soc = float(self.SOC)
    soc_low, soc_high = self.soc_bounds
    soc_init = float(self.SOC_init)
    soc_target = float(self.SOC_target)

    # ── term_soc_anchor (catalog: soc_anchor, symmetric quadratic) ──
    # Unchanged shape from edit base: w_soc * (soc - soc_target)^2,
    # multiplied by 10 outside soc_bounds.
    soc_err = (soc - soc_target) ** 2
    w_soc_step = float(np.where(
        (soc >= soc_high) | (soc <= soc_low),
        self.w_soc * 10.0,
        self.w_soc
    ))
    term_soc_anchor = w_soc_step * soc_err

    # ── term_drift_barrier (catalog: drift_barrier) ──
    # Flat inside |SOC - SOC_init| <= 0.025, quadratic beyond.
    # c=60, d0=0.025, p=2.
    # Sizing: at |drift|=0.039 (edit base) → 60*(0.039-0.025)^2=0.01176/step;
    #   over 2020 steps with |drift|>0.025 → ~23.8 reward units.
    # At guard edge 0.05: 60*(0.05-0.025)^2=0.0375/step.
    # Checked: zero at |SOC-SOC_init|=0.01 ✓, positive at guard edge 0.05 ✓,
    #          nondecreasing in |SOC-SOC_init| ✓.
    c_barrier = 60.0
    d0_barrier = 0.025
    soc_abs_dev = float(np.abs(soc - soc_init))
    barrier_excess = float(np.maximum(0.0, soc_abs_dev - d0_barrier))
    term_drift_barrier = c_barrier * barrier_excess ** 2

    # ── term_fc_surplus_charge (catalog: fc_surplus_charge) ──
    # Price FC power flowing into the battery when SOC > SOC_target.
    # g(SOC) = max(0, SOC - SOC_target + m) / m, m=0.05.
    # Ramps 0→1 from SOC=0.55 to SOC=0.65, unclamped above (nondecreasing).
    # P_fc_to_batt_kw = max(0, min(-P_batt, P_mot - P_batt)) / 1000
    # c=0.8; at mean FC->batt 1.97 kW above target (measured), g≈0.5, ~952 steps:
    #   0.8 * 0.5 * 1.97 * 952 ≈ 752 reward units.
    # Checked: zero while discharging ✓, zero for pure regen (no FC power) ✓,
    #          zero at SOC_target-0.1=0.50 ✓, positive at SOC_target+0.05 with FC charging ✓,
    #          nondecreasing in SOC and FC charging power ✓.
    m_surplus = 0.05
    g_surplus = float(np.maximum(0.0, soc - soc_target + m_surplus) / m_surplus)
    p_batt_w = float(self.P_batt)    # W, + = discharge
    p_mot_w = float(self.P_mot)      # W, motor electrical power
    # FC power into battery (kW): positive only when FC is net-charging the battery
    p_fc_to_batt_kw = float(
        np.maximum(0.0, np.minimum(-p_batt_w, p_mot_w - p_batt_w))
    ) / 1000.0
    c_surplus = 0.8
    term_fc_surplus_charge = c_surplus * g_surplus * p_fc_to_batt_kw

    # ── soc_cost = sum of ALL charge-sustaining terms (catalog contract) ──
    # soc_cost must equal exactly the sum of the three logged term_ values.
    term_soc_anchor = float(term_soc_anchor)
    term_drift_barrier = float(term_drift_barrier)
    term_fc_surplus_charge = float(term_fc_surplus_charge)
    soc_cost = term_soc_anchor + term_drift_barrier + term_fc_surplus_charge

    # ── standard price terms ──
    h2_fcs = self.h2_fcs
    h2_batt = self.h2_batt
    h2_equal = self.h2_equal
    h2_cost = self.w_h2 * float(h2_fcs)
    fcs_soh_cost = self.w_fc * float(self.dSOH_FCS)
    batt_soh_cost = self.w_batt * float(self.dSOH_batt)

    # ── term_fc_efficiency_gap (catalog: fc_efficiency_gap, NEW — replaces fc_peak_shave) ──
    # Price hydrogen burned below the FC's peak efficiency (eta_ref=0.601 at 10-15 kW).
    # eta = P_FCS / (120 * h2_fcs) when h2_fcs > 0 (else term = 0; guards division by zero).
    # c=4 (vs. iteration 3's c=40 which caused 33 load changes; c=4 is 10x smaller).
    # Sizing at c=4:
    #   4 kW band (eta=0.484, gap=0.196, h2_fcs≈0.0267 g/step): 4*0.0267*0.196/0.601≈0.035/step
    #   2 kW band (eta=0.215, gap=0.646, h2_fcs≈0.0117 g/step): 4*0.0117*0.646/0.601≈0.050/step
    #   Mean over ~1070 low-efficiency steps ≈ 0.040/step → ~43 reward units total.
    #   Mean over full episode ≈ 0.013/step — well within price-deviation tolerance.
    # Incentivizes FC toward 10-15 kW efficient band without aggressive ramping.
    # Checked: zero with FC off (h2_fcs=0) ✓, zero at eta>=eta_ref ✓, nonnegative ✓,
    #          nonincreasing in eta at fixed hydrogen ✓, enters objective_cost ✓.
    eta_ref = 0.601
    c_eff_gap = 4.0
    p_fcs_kw = float(self.P_FCS)
    h2_fcs_val = float(h2_fcs)
    # Guard: only compute eta when FC is on (h2_fcs_val > 0); zero when FC is off.
    # This prevents float division by zero when h2_fcs = 0.0.
    if h2_fcs_val > 0.0:
        eta_fc = p_fcs_kw / (120.0 * h2_fcs_val)
        efficiency_gap = float(np.maximum(0.0, eta_ref - eta_fc) / eta_ref)
        term_fc_efficiency_gap = c_eff_gap * h2_fcs_val * efficiency_gap
    else:
        term_fc_efficiency_gap = 0.0

    in_bounds = (soc_low < soc < soc_high)
    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost + term_fc_efficiency_gap
    reward = float(-objective_cost)

    self.info.update({
        'EMS_reward':               reward,
        'h2_fcs':                   float(h2_fcs),
        'h2_batt':                  float(h2_batt),
        'h2_equal':                 float(h2_equal),
        'soc_cost':                 float(soc_cost),
        'h2_cost':                  float(h2_cost),
        'fcs_soh_cost':             float(fcs_soh_cost),
        'batt_soh_cost':            float(batt_soh_cost),
        'objective_cost':           float(objective_cost),
        'soc_in_bounds':            int(in_bounds),
        # catalog term logs (required; soc_cost == sum of first three)
        'term_soc_anchor':          term_soc_anchor,
        'term_drift_barrier':       term_drift_barrier,
        'term_fc_surplus_charge':   term_fc_surplus_charge,
        'term_fc_efficiency_gap':   term_fc_efficiency_gap,
    })
    return reward
