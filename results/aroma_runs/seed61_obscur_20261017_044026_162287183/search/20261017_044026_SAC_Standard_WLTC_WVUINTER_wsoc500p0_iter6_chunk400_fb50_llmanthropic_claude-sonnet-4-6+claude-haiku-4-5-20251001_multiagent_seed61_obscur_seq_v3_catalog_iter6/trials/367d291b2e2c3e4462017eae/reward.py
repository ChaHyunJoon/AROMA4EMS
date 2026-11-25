def get_reward(self):
    soc = float(self.SOC)
    soc_low, soc_high = self.soc_bounds
    soc_init = float(self.SOC_init)
    soc_target = float(self.SOC_target)

    # ------------------------------------------------------------------ #
    # CHARGE-SUSTAINING: soc_cost = soc_anchor + drift_barrier            #
    #                              + fc_surplus_charge (NEW)              #
    # ------------------------------------------------------------------ #

    # --- term_soc_anchor (catalog: soc_anchor, symmetric, p=2) ----------
    # Raised w_soc from 500 to 700 (same as edit base) to keep combined
    # soc_cost above the charge-sustaining sizing floor.
    w_soc_eff = 700.0
    soc_err_sq = (soc - soc_target) ** 2
    in_bounds = (soc_low < soc < soc_high)
    k_bounds = 10.0 if not in_bounds else 1.0
    term_soc_anchor = w_soc_eff * soc_err_sq * k_bounds

    # --- term_drift_barrier (catalog: drift_barrier) --------------------
    # Retained from edit base: flat for |SOC - SOC_init| <= 0.025,
    # quadratic beyond. c_db=800, d0=0.025.
    c_db = 800.0
    d0 = 0.025
    drift_abs = abs(soc - soc_init)
    drift_excess = drift_abs - d0 if drift_abs > d0 else 0.0
    term_drift_barrier = c_db * drift_excess * drift_excess

    # --- term_fc_surplus_charge (catalog: fc_surplus_charge, NEW) -------
    # Price FC power pushed into the battery while SOC is above target.
    # Structural addition: the edit base has no fc_surplus_charge.
    #
    # g(SOC) = clamp(max(0, SOC - SOC_target + m) / m, 0, 1), m = 0.05
    #   zero at SOC <= SOC_target - 0.05 = 0.55
    #   ramps to 1 at SOC = SOC_target + 0.05 = 0.65
    #
    # P_fc_to_batt_kw = max(0, min(-P_batt, P_mot - P_batt)) / 1000
    #   positive only when FC is charging the battery (not pure regen)
    #
    # Sizing: c_fsc=8, g~1.0, P_fc_to_batt~4.47 kW at above-target steps
    #   ~453 above-target steps: 8 x 1.0 x 4.47 x 453 ~ 16,200 reward units
    #   inside [2011, 41650], above geometric mean 9152. ✓
    p_batt_w = float(self.P_batt)   # W, + = discharge
    p_mot_w  = float(self.P_mot)    # W, motor electrical power
    p_fc_to_batt_kw = max(0.0, min(-p_batt_w, p_mot_w - p_batt_w)) / 1000.0
    m_fsc = 0.05
    g_fsc_raw = (soc - soc_target + m_fsc) / m_fsc
    g_fsc = g_fsc_raw if g_fsc_raw > 0.0 else 0.0
    g_fsc = g_fsc if g_fsc < 1.0 else 1.0
    c_fsc = 8.0
    term_fc_surplus_charge = c_fsc * g_fsc * p_fc_to_batt_kw

    # soc_cost = sum of all charge-sustaining terms
    soc_cost = term_soc_anchor + term_drift_barrier + term_fc_surplus_charge

    # ------------------------------------------------------------------ #
    # HYDROGEN COST (reshaped: w_h2 raised from 10 to 12, same as edit   #
    # base)                                                               #
    # ------------------------------------------------------------------ #
    h2_fcs  = float(self.h2_fcs)
    h2_batt = float(self.h2_batt)
    h2_equal = float(self.h2_equal)

    w_h2_eff = 12.0
    h2_cost = w_h2_eff * h2_fcs

    # ------------------------------------------------------------------ #
    # FC DEGRADATION COST (unchanged weight)                              #
    # ------------------------------------------------------------------ #
    fcs_soh_cost = self.w_fc * float(self.dSOH_FCS)

    # ------------------------------------------------------------------ #
    # BATTERY DEGRADATION COST (unchanged weight)                         #
    # ------------------------------------------------------------------ #
    batt_soh_cost = self.w_batt * float(self.dSOH_batt)

    # ------------------------------------------------------------------ #
    # EXTRA PRICE TERM: fc_efficiency_gap (catalog: fc_efficiency_gap)   #
    # RESHAPED from edit base: coefficient reduced from 50 -> 20.        #
    # This is a shape change: at c=20 the term no longer dominates the   #
    # per-step objective at low FC power, reducing the incentive for the  #
    # policy to ramp the FC aggressively to stay in the efficient band.   #
    # Hypothesis: load-change events fall from 24 toward ~8-15, reducing  #
    # battery throughput ~0.15-0.25 kWh and ohmic loss ~0.015-0.025 kWh. #
    # Small fuel cost: +0.01-0.03 g/km, within 0.47 g/km headroom.      #
    # ------------------------------------------------------------------ #
    eta_ref = 0.602
    p_fcs = float(self.P_FCS)   # kW
    if h2_fcs > 0.0:
        eta = p_fcs / (120.0 * h2_fcs)
        gap = max(0.0, eta_ref - eta) / eta_ref
        term_fc_efficiency_gap = 20.0 * h2_fcs * gap
    else:
        eta = 0.0
        gap = 0.0
        term_fc_efficiency_gap = 0.0

    # ------------------------------------------------------------------ #
    # OBJECTIVE COST                                                      #
    # ------------------------------------------------------------------ #
    objective_cost = (soc_cost
                      + h2_cost
                      + fcs_soh_cost
                      + batt_soh_cost
                      + term_fc_efficiency_gap)

    reward = float(-objective_cost)

    # ------------------------------------------------------------------ #
    # LOGGING (every catalog term logged as term_<id>)                   #
    # ------------------------------------------------------------------ #
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
        # catalog term logs
        'term_soc_anchor':          float(term_soc_anchor),
        'term_drift_barrier':       float(term_drift_barrier),
        'term_fc_surplus_charge':   float(term_fc_surplus_charge),
        'term_fc_efficiency_gap':   float(term_fc_efficiency_gap),
    })
    return reward
