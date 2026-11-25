def get_reward(self):
    soc = float(self.SOC)
    soc_low, soc_high = self.soc_bounds
    soc_init = float(self.SOC_init)
    soc_target = float(self.SOC_target)

    # ------------------------------------------------------------------ #
    # CHARGE-SUSTAINING: soc_cost = soc_anchor + drift_barrier            #
    #                              + fc_surplus_charge                    #
    # ------------------------------------------------------------------ #

    # --- term_soc_anchor (catalog: soc_anchor, symmetric, p=2) ----------
    # Same shape as edit base (w_soc=500, x10 outside bounds).
    soc_err_sq = (soc - soc_target) ** 2
    in_bounds = (soc_low < soc < soc_high)
    k_bounds = 10.0 if not in_bounds else 1.0
    term_soc_anchor = self.w_soc * soc_err_sq * k_bounds

    # --- term_drift_barrier (catalog: drift_barrier, NEW) ---------------
    # Flat for |SOC - SOC_init| <= d0 = 0.025, quadratic beyond.
    # Structural addition: edit base has no drift_barrier.
    # Sizing: c_db=12000, d0=0.025 → ~7557 reward units over 1191 drift
    # steps (floor 2011, ceiling 50400, geometric mean 10070). ✓
    c_db = 12000.0
    d0 = 0.025
    drift_abs = abs(soc - soc_init)
    drift_excess = drift_abs - d0 if drift_abs > d0 else 0.0
    term_drift_barrier = c_db * drift_excess * drift_excess

    # --- term_fc_surplus_charge (catalog: fc_surplus_charge, NEW) -------
    # Price FC power pushed into the battery while SOC is above target.
    # g(SOC) = max(0, SOC - SOC_target + m) / m, m = 0.05
    # Zero at SOC <= SOC_target - 0.05, ramps to 1 at SOC = SOC_target + 0.05.
    # P_fc_to_batt_kw = max(0, min(-P_batt, P_mot - P_batt)) / 1000
    # Structural addition: edit base has no fc_surplus_charge.
    # Sizing: c_fsc=4.0 → ~3000 reward units over ~470 above-target steps. ✓
    p_batt_w = float(self.P_batt)   # W, + = discharge
    p_mot_w  = float(self.P_mot)    # W, motor electrical power
    # FC power into battery (kW): positive only when FC charges battery
    p_fc_to_batt_kw = max(0.0, min(-p_batt_w, p_mot_w - p_batt_w)) / 1000.0
    m_fsc = 0.05
    g_fsc_raw = (soc - soc_target + m_fsc) / m_fsc
    g_fsc = g_fsc_raw if g_fsc_raw > 0.0 else 0.0
    g_fsc = g_fsc if g_fsc < 1.0 else 1.0   # cap at 1 for interpretability
    c_fsc = 4.0
    term_fc_surplus_charge = c_fsc * g_fsc * p_fc_to_batt_kw

    # soc_cost = sum of all charge-sustaining terms
    soc_cost = term_soc_anchor + term_drift_barrier + term_fc_surplus_charge

    # ------------------------------------------------------------------ #
    # HYDROGEN COST (unchanged weight w_h2 = 10)                          #
    # ------------------------------------------------------------------ #
    h2_fcs  = float(self.h2_fcs)
    h2_batt = float(self.h2_batt)
    h2_equal = float(self.h2_equal)
    h2_cost = self.w_h2 * h2_fcs

    # ------------------------------------------------------------------ #
    # FC DEGRADATION COST (unchanged weight w_fc)                         #
    # ------------------------------------------------------------------ #
    fcs_soh_cost = self.w_fc * float(self.dSOH_FCS)

    # ------------------------------------------------------------------ #
    # BATTERY DEGRADATION COST (unchanged weight w_batt)                  #
    # ------------------------------------------------------------------ #
    batt_soh_cost = self.w_batt * float(self.dSOH_batt)

    # ------------------------------------------------------------------ #
    # OBJECTIVE COST                                                       #
    # ------------------------------------------------------------------ #
    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost
    reward = float(-objective_cost)

    # ------------------------------------------------------------------ #
    # LOGGING (all catalog terms + required keys)                          #
    # ------------------------------------------------------------------ #
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
        # catalog term logs
        'term_soc_anchor':       float(term_soc_anchor),
        'term_drift_barrier':    float(term_drift_barrier),
        'term_fc_surplus_charge': float(term_fc_surplus_charge),
    })
    return reward
