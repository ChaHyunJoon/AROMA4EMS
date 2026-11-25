def get_reward(self):
    soc = float(self.SOC)
    soc_low, soc_high = self.soc_bounds
    soc_init = float(self.SOC_init)
    soc_target = float(self.SOC_target)

    # ------------------------------------------------------------------ #
    # CHARGE-SUSTAINING: soc_cost = term_soc_anchor                       #
    #                              + term_drift_barrier                   #
    #                              + term_fc_surplus_charge               #
    # ------------------------------------------------------------------ #

    # --- term_soc_anchor (catalog: soc_anchor, symmetric, p=2) ----------
    # Same shape as edit base (w_soc=500, x10 outside bounds).
    # Checked: zero at SOC_target, nonneg, nondecreasing away from target. ✓
    soc_err_sq = (soc - soc_target) ** 2
    in_bounds = (soc_low < soc < soc_high)
    k_bounds = 10.0 if not in_bounds else 1.0
    term_soc_anchor = self.w_soc * soc_err_sq * k_bounds

    # --- term_drift_barrier (catalog: drift_barrier, RESHAPED) ----------
    # Edit base had c_db=3000; now c_db=7000 — steeper quadratic beyond
    # d0=0.025. Shape change: same functional form, coefficient raised to
    # make staying near SOC_init cheaper than switching FC off and drifting.
    # Checked: zero for |SOC-SOC_init|<=0.025, positive at guard boundary
    # 0.05 on both sides (7000*(0.05-0.025)^2=4.375>0), nondecreasing. ✓
    c_db = 7000.0
    d0 = 0.025
    drift_abs = abs(soc - soc_init)
    drift_excess = drift_abs - d0 if drift_abs > d0 else 0.0
    term_drift_barrier = c_db * drift_excess * drift_excess

    # --- term_fc_surplus_charge (catalog: fc_surplus_charge, NEW) -------
    # Structural addition: edit base has no fc_surplus_charge.
    # Prices FC power pushed into the battery while SOC is above target.
    # This directly addresses the measured drift mechanism (FC kept on at
    # low load, surplus charges battery, SOC creeps high) without penalizing
    # low-power FC operation per se — unlike fc_efficiency_gap which caused
    # the policy to switch the FC off and incur starts.
    #
    # g(SOC) = clamp(max(0, SOC - SOC_target + m) / m, 0, 1), m = 0.05
    #   zero at SOC <= SOC_target - 0.05 = 0.55
    #   ramps linearly to 1 at SOC = SOC_target + 0.05 = 0.65
    #
    # P_fc_to_batt_kw = max(0, min(-P_batt, P_mot - P_batt)) / 1000
    #   positive only when FC is charging the battery (not pure regen)
    #   zero while discharging, zero for pure regeneration. ✓
    #
    # Sizing: edit base 0.166 kWh FC->batt above target over ~221 steps
    # at mean 2.67 kW; c=6.0: 6.0 x 1.0 x 2.67 x 221 = 3,540 reward
    # units — above floor 3,100, inside ceiling 72,310. ✓
    #
    # Checked: zero while discharging, zero for pure regen (no FC power),
    # zero at SOC_target - 0.05, positive at SOC_target + 0.05 with FC
    # charging, nondecreasing in SOC and in FC charging power. ✓
    p_batt_w = float(self.P_batt)   # W, + = discharge
    p_mot_w  = float(self.P_mot)    # W, motor electrical power
    p_fc_to_batt_kw = max(0.0, min(-p_batt_w, p_mot_w - p_batt_w)) / 1000.0
    m_fsc = 0.05
    g_fsc_raw = (soc - soc_target + m_fsc) / m_fsc
    g_fsc = g_fsc_raw if g_fsc_raw > 0.0 else 0.0
    g_fsc = g_fsc if g_fsc < 1.0 else 1.0
    c_fsc = 6.0
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
    # FC DEGRADATION COST (settings weight w_fc, no multiplier)           #
    # Reverted from edit base's x1.05: weight-only change, not structural.#
    # Using settings w_fc keeps the FC/battery price ratio at settings    #
    # values and avoids stressing the deviation check.                    #
    # ------------------------------------------------------------------ #
    fcs_soh_cost = self.w_fc * float(self.dSOH_FCS)

    # ------------------------------------------------------------------ #
    # BATTERY DEGRADATION COST (settings weight w_batt, no multiplier)   #
    # Reverted from edit base's x1.05 for same reason as FC above.       #
    # ------------------------------------------------------------------ #
    batt_soh_cost = self.w_batt * float(self.dSOH_batt)

    # ------------------------------------------------------------------ #
    # EXTRA PRICE TERM: batt_ohmic (catalog: batt_ohmic)                  #
    # Retained from edit base: prices battery ohmic loss directly.        #
    # c=1.0: mean term = 1.0 x 0.2392 = 0.239/step — small, directional. #
    # Prevents battery from being a free buffer when FC wear is reduced.  #
    # Checked: zero at zero loss, nonneg, linear in P_batt_loss_kw. ✓    #
    # ------------------------------------------------------------------ #
    p_batt_loss_kw = float(self.P_batt_loss_kw)
    term_batt_ohmic = 1.0 * p_batt_loss_kw

    # ------------------------------------------------------------------ #
    # OBJECTIVE COST                                                       #
    # ------------------------------------------------------------------ #
    objective_cost = (soc_cost
                      + h2_cost
                      + fcs_soh_cost
                      + batt_soh_cost
                      + term_batt_ohmic)

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
        # Catalog term logs
        'term_soc_anchor':          float(term_soc_anchor),
        'term_drift_barrier':       float(term_drift_barrier),
        'term_fc_surplus_charge':   float(term_fc_surplus_charge),
        'term_batt_ohmic':          float(term_batt_ohmic),
    })
    return reward
