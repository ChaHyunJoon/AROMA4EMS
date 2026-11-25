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
    # Sizing: at |drift|=0.06 → 60*(0.06-0.025)^2=0.0735/step;
    #   over 952 steps with |drift|>0.025 → ~70 reward units.
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
    # c=0.8; at mean FC->batt 1.52 kW above target, g≈0.5, ~952 steps:
    #   0.8 * 0.5 * 1.52 * 952 ≈ 580 reward units.
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

    # ── term_fc_peak_shave (catalog: fc_peak_shave, NEW — not in edit base) ──
    # When SOC is above target, price FC power above P_cap=20 kW.
    # Incentivizes battery to cover high-power transients; FC stays in efficient band.
    # g(SOC) = max(0, SOC - SOC_target + m) / m, m=0.05 (same ramp as surplus charge).
    # P_cap=20 kW (above the 10-15 kW peak-efficiency band).
    # c=15; at SOC_target+0.025 (g=0.5), P_FCS=30 kW: 15*0.5*10=75/step.
    # Over ~172 steps above 20 kW with g≈0.5: ~1290 reward units.
    # Checked: zero at P_FCS<=20 kW ✓, zero at SOC_target-0.1 ✓,
    #          positive at SOC_target+0.05 with P_FCS=60 kW ✓,
    #          nondecreasing in SOC and in P_FCS ✓.
    p_cap_kw = 20.0
    c_peak_shave = 15.0
    p_fcs_kw = float(self.P_FCS)
    fc_excess_kw = float(np.maximum(0.0, p_fcs_kw - p_cap_kw))
    # g_surplus is already computed above with the same m=0.05; reuse it.
    term_fc_peak_shave = c_peak_shave * g_surplus * fc_excess_kw

    # ── soc_cost = sum of ALL charge-sustaining terms (catalog contract) ──
    # soc_cost must equal exactly the sum of the four logged term_ values.
    term_soc_anchor = float(term_soc_anchor)
    term_drift_barrier = float(term_drift_barrier)
    term_fc_surplus_charge = float(term_fc_surplus_charge)
    term_fc_peak_shave = float(term_fc_peak_shave)
    soc_cost = term_soc_anchor + term_drift_barrier + term_fc_surplus_charge + term_fc_peak_shave

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
        'EMS_reward':             reward,
        'h2_fcs':                 float(h2_fcs),
        'h2_batt':                float(h2_batt),
        'h2_equal':               float(h2_equal),
        'soc_cost':               float(soc_cost),
        'h2_cost':                float(h2_cost),
        'fcs_soh_cost':           float(fcs_soh_cost),
        'batt_soh_cost':          float(batt_soh_cost),
        'objective_cost':         float(objective_cost),
        'soc_in_bounds':          int(in_bounds),
        # catalog term logs (required; soc_cost == sum of these four)
        'term_soc_anchor':        term_soc_anchor,
        'term_drift_barrier':     term_drift_barrier,
        'term_fc_surplus_charge': term_fc_surplus_charge,
        'term_fc_peak_shave':     term_fc_peak_shave,
    })
    return reward
