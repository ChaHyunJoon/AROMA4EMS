def get_reward(self):
    soc = float(self.SOC)
    soc_low, soc_high = self.soc_bounds
    soc_init = float(self.SOC_init)
    soc_target = float(self.SOC_target)

    # ------------------------------------------------------------------ #
    # CHARGE-SUSTAINING: soc_cost = soc_anchor + drift_barrier            #
    # ------------------------------------------------------------------ #

    # --- term_soc_anchor (catalog: soc_anchor, symmetric, p=2) ----------
    # Raised w_soc from 500 to 700 to keep combined soc_cost above the
    # charge-sustaining sizing floor after adding drift_barrier.
    w_soc_eff = 700.0
    soc_err_sq = (soc - soc_target) ** 2
    # multiply by 10 outside soc_bounds (same shape as edit base)
    in_bounds = (soc_low < soc < soc_high)
    k_bounds = 10.0 if not in_bounds else 1.0
    term_soc_anchor = w_soc_eff * soc_err_sq * k_bounds

    # --- term_drift_barrier (catalog: drift_barrier, new) ---------------
    # Flat for |SOC - SOC_init| <= d0 = 0.025, quadratic beyond.
    # Structural addition: the edit base has no drift_barrier.
    c_db = 800.0
    d0 = 0.025
    drift_excess = max(0.0, abs(soc - soc_init) - d0)
    term_drift_barrier = c_db * drift_excess ** 2

    # soc_cost = sum of charge-sustaining terms
    soc_cost = term_soc_anchor + term_drift_barrier

    # ------------------------------------------------------------------ #
    # HYDROGEN COST (reshaped: w_h2 raised from 10 to 12)                 #
    # CHANGE_SPEC: h2_cost "changed"                                       #
    # ------------------------------------------------------------------ #
    h2_fcs = float(self.h2_fcs)
    h2_batt = float(self.h2_batt)
    h2_equal = float(self.h2_equal)

    w_h2_eff = 12.0
    h2_cost = w_h2_eff * h2_fcs

    # ------------------------------------------------------------------ #
    # FC DEGRADATION COST (unchanged weight)                               #
    # ------------------------------------------------------------------ #
    fcs_soh_cost = self.w_fc * float(self.dSOH_FCS)

    # ------------------------------------------------------------------ #
    # BATTERY DEGRADATION COST (unchanged weight)                          #
    # ------------------------------------------------------------------ #
    batt_soh_cost = self.w_batt * float(self.dSOH_batt)

    # ------------------------------------------------------------------ #
    # EXTRA PRICE TERM: fc_efficiency_gap (catalog: fc_efficiency_gap)    #
    # New term: price H2 burned below peak efficiency eta_ref = 0.602.    #
    # eta = P_FCS / (120 * h2_fcs) when h2_fcs > 0, else 0.              #
    # CHANGE_SPEC: extra_terms "added"                                     #
    # ------------------------------------------------------------------ #
    eta_ref = 0.602
    p_fcs = float(self.P_FCS)   # kW
    if h2_fcs > 0.0:
        eta = p_fcs / (120.0 * h2_fcs)
        gap = max(0.0, eta_ref - eta) / eta_ref
        term_fc_efficiency_gap = 50.0 * h2_fcs * gap
    else:
        eta = 0.0
        gap = 0.0
        term_fc_efficiency_gap = 0.0

    # ------------------------------------------------------------------ #
    # OBJECTIVE COST                                                        #
    # ------------------------------------------------------------------ #
    objective_cost = (soc_cost
                      + h2_cost
                      + fcs_soh_cost
                      + batt_soh_cost
                      + term_fc_efficiency_gap)

    reward = float(-objective_cost)

    # ------------------------------------------------------------------ #
    # LOGGING (every catalog term logged as term_<id>)                     #
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
        'term_fc_efficiency_gap': float(term_fc_efficiency_gap),
    })
    return reward
