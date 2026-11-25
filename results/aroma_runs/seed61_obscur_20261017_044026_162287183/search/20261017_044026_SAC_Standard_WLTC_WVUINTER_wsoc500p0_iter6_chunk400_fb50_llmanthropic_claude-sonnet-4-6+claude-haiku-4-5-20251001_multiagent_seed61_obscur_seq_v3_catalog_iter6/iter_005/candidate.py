def get_reward(self):
    soc = float(self.SOC)
    soc_low, soc_high = self.soc_bounds
    soc_init = float(self.SOC_init)
    soc_target = float(self.SOC_target)

    # ------------------------------------------------------------------ #
    # CHARGE-SUSTAINING: soc_cost = term_soc_anchor + term_drift_barrier  #
    # ------------------------------------------------------------------ #

    # --- term_soc_anchor (catalog: soc_anchor, symmetric, p=2) ----------
    # Same shape as edit base (w_soc=500, x10 outside bounds).
    # Logged as term_soc_anchor; this IS the baseline's soc_cost form.
    soc_err_sq = (soc - soc_target) ** 2
    in_bounds = (soc_low < soc < soc_high)
    k_bounds = 10.0 if not in_bounds else 1.0
    term_soc_anchor = self.w_soc * soc_err_sq * k_bounds

    # --- term_drift_barrier (catalog: drift_barrier, NEW) ---------------
    # Structural addition: edit base has no drift_barrier.
    # Flat for |SOC - SOC_init| <= d0 = 0.025, quadratic beyond.
    # Sizing: c_db=3000, d0=0.025 → ~2232 reward units over 1191 drift
    # steps (floor 2011, ceiling 50400, geometric mean 10070). ✓
    # Checked: zero at |SOC-SOC_init|<=0.025, positive at guard boundary
    # 0.05 on both sides (3000*(0.05-0.025)^2=1.875>0), nondecreasing. ✓
    c_db = 3000.0
    d0 = 0.025
    drift_abs = abs(soc - soc_init)
    drift_excess = drift_abs - d0 if drift_abs > d0 else 0.0
    term_drift_barrier = c_db * drift_excess * drift_excess

    # soc_cost = sum of charge-sustaining terms
    soc_cost = term_soc_anchor + term_drift_barrier

    # ------------------------------------------------------------------ #
    # HYDROGEN COST (unchanged weight w_h2 = 10)                          #
    # ------------------------------------------------------------------ #
    h2_fcs = float(self.h2_fcs)
    h2_batt = float(self.h2_batt)
    h2_equal = float(self.h2_equal)
    h2_cost = self.w_h2 * h2_fcs

    # ------------------------------------------------------------------ #
    # FC DEGRADATION COST (CHANGED: w_fc scaled by 1.05)                  #
    # CHANGE_SPEC: fcs_soh_cost "changed"                                  #
    # Slight upward alignment toward selection prices; keeps FC/battery    #
    # ratio constant (both scaled equally).                                #
    # ------------------------------------------------------------------ #
    w_fc_eff = self.w_fc * 1.05
    fcs_soh_cost = w_fc_eff * float(self.dSOH_FCS)

    # ------------------------------------------------------------------ #
    # BATTERY DEGRADATION COST (CHANGED: w_batt scaled by 1.05)           #
    # CHANGE_SPEC: batt_soh_cost "changed"                                 #
    # Scaled in proportion with FC to avoid making battery a free buffer.  #
    # ------------------------------------------------------------------ #
    w_batt_eff = self.w_batt * 1.05
    batt_soh_cost = w_batt_eff * float(self.dSOH_batt)

    # ------------------------------------------------------------------ #
    # EXTRA PRICE TERM 1: fc_efficiency_gap (catalog: fc_efficiency_gap)  #
    # NEW term: price H2 burned below peak efficiency eta_ref = 0.602.    #
    # eta = P_FCS / (120 * h2_fcs) when h2_fcs > 0, else 0.              #
    # c=20: mean term ~0.169/step, well within deviation budget.           #
    # Checked: zero with FC off, zero at eta>=eta_ref, nonneg. ✓          #
    # ------------------------------------------------------------------ #
    eta_ref = 0.602
    p_fcs = float(self.P_FCS)
    if h2_fcs > 0.0:
        eta = p_fcs / (120.0 * h2_fcs)
        gap = (eta_ref - eta) / eta_ref
        gap = gap if gap > 0.0 else 0.0
        term_fc_efficiency_gap = 20.0 * h2_fcs * gap
    else:
        eta = 0.0
        gap = 0.0
        term_fc_efficiency_gap = 0.0

    # ------------------------------------------------------------------ #
    # EXTRA PRICE TERM 2: batt_ohmic (catalog: batt_ohmic)                #
    # NEW term: price battery ohmic loss directly.                         #
    # c=1.0: mean term = 1.0 * 0.2392 = 0.239/step — small, directional. #
    # Prevents battery from being a free buffer when FC wear is reduced.   #
    # Checked: zero at zero loss, nonneg, linear in P_batt_loss_kw. ✓    #
    # ------------------------------------------------------------------ #
    p_batt_loss_kw = float(self.P_batt_loss_kw)
    term_batt_ohmic = 1.0 * p_batt_loss_kw

    # ------------------------------------------------------------------ #
    # OBJECTIVE COST                                                        #
    # ------------------------------------------------------------------ #
    objective_cost = (soc_cost
                      + h2_cost
                      + fcs_soh_cost
                      + batt_soh_cost
                      + term_fc_efficiency_gap
                      + term_batt_ohmic)

    reward = float(-objective_cost)

    self.info.update({
        'EMS_reward':           reward,
        'h2_fcs':               float(h2_fcs),
        'h2_batt':              float(h2_batt),
        'h2_equal':             float(h2_equal),
        'soc_cost':             float(soc_cost),
        'h2_cost':              float(h2_cost),
        'fcs_soh_cost':         float(fcs_soh_cost),
        'batt_soh_cost':        float(batt_soh_cost),
        'objective_cost':       float(objective_cost),
        'soc_in_bounds':        int(in_bounds),
        # Catalog term logs
        'term_soc_anchor':      float(term_soc_anchor),
        'term_drift_barrier':   float(term_drift_barrier),
        'term_fc_efficiency_gap': float(term_fc_efficiency_gap),
        'term_batt_ohmic':      float(term_batt_ohmic),
    })
    return reward
