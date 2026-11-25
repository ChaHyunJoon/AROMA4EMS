def get_reward(self):
    soc = float(self.SOC)
    soc_low, soc_high = self.soc_bounds

    # ---------- Charge-sustaining terms (must sum into soc_cost) ----------
    # term_soc_anchor (catalog: soc_anchor; symmetric quadratic with bounds multiplier k=10)
    soc_err2 = float(np.abs(soc - float(self.SOC_target)) ** 2)
    w_soc_eff = float(np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10.0, self.w_soc))
    term_soc_anchor = w_soc_eff * soc_err2

    # term_fc_surplus_charge (catalog: fc_surplus_charge)  [UNCHANGED FORM]
    # g(SOC)=max(0,(SOC - SOC_target + 0.10)/0.10), nondecreasing; zero at/below SOC_target-0.10
    m = 0.10
    g_soc = float(np.maximum(0.0, (soc - float(self.SOC_target) + m) / m))

    # P_fc_to_batt_kw = max(0, min(-P_batt, P_mot - P_batt)) / 1000  (per catalog)
    P_batt_w = float(self.P_batt)  # + discharge, - charge
    P_mot_w = float(self.P_mot)
    fc_to_batt_w = float(np.maximum(0.0, np.minimum(-P_batt_w, P_mot_w - P_batt_w)))
    P_fc_to_batt_kw = fc_to_batt_w / 1000.0

    c_fc_surplus = 1.5  # reward_units per (kW*step)  [UNCHANGED]
    term_fc_surplus_charge = c_fc_surplus * g_soc * P_fc_to_batt_kw

    # term_drift_barrier (catalog: drift_barrier)  [ADDED PER CHANGE_SPEC]
    # Penalize sustained drift away from SOC_init beyond a small band (per-step, not terminal-only).
    # d0 must be < soc_drift_abs_max (=0.05); choose d0=0.02 to start pricing before the guard.
    d0 = 0.02
    drift_abs = float(np.abs(soc - float(self.SOC_init)))
    drift_excess = float(np.maximum(0.0, drift_abs - d0))
    # Coefficient sizing target (from DRIFT FACTS on edit_base rollout):
    # 1377 steps have |SOC-SOC_init|>0.025. We want total added cost ~ geometric mean 1.343e4,
    # i.e. ~9.75 reward-units/step over those steps. With typical drift_excess ~0.02-0.03,
    # drift_excess^2 ~4e-4..9e-4, so c ~ (9.75)/(4e-4..9e-4) ≈ 1.1e4..2.4e4. Pick 1.5e4.
    c_drift = 15000.0
    term_drift_barrier = c_drift * (drift_excess ** 2)

    soc_cost = term_soc_anchor + term_fc_surplus_charge + term_drift_barrier

    # ---------- Objective price terms (unchanged) ----------
    h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal
    h2_cost = float(self.w_h2) * float(h2_fcs)

    fcs_soh_cost = float(self.w_fc) * float(self.dSOH_FCS)
    batt_soh_cost = float(self.w_batt) * float(self.dSOH_batt)

    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost
    reward = float(-objective_cost)

    in_bounds = (soc_low < soc < soc_high)

    # ---------- Required logging ----------
    self.info.update({
        'EMS_reward': reward,
        'h2_fcs': float(h2_fcs),
        'h2_batt': float(h2_batt),
        'h2_equal': float(h2_equal),

        # Catalog-term logs (plain values, before summing)
        'term_soc_anchor': float(term_soc_anchor),
        'term_fc_surplus_charge': float(term_fc_surplus_charge),
        'term_drift_barrier': float(term_drift_barrier),

        # Keep these four logs truthful for their own terms
        'soc_cost': float(soc_cost),
        'h2_cost': float(h2_cost),
        'fcs_soh_cost': float(fcs_soh_cost),
        'batt_soh_cost': float(batt_soh_cost),

        'objective_cost': float(objective_cost),
        'soc_in_bounds': int(in_bounds),
    })
    return reward
