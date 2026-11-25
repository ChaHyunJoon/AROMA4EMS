def get_reward(self):
    soc = float(self.SOC)
    soc_low, soc_high = self.soc_bounds

    # ---------- Charge-sustaining family (soc_cost = sum of catalog terms) ----------
    # Catalog term: soc_anchor (baseline symmetric quadratic anchor with bounds multiplier)
    soc_tgt = float(self.SOC_target)
    soc_err = float(np.abs(soc - soc_tgt)) ** 2
    out_of_bounds = (soc >= float(soc_high)) or (soc <= float(soc_low))
    w_soc_eff = float(self.w_soc) * (10.0 if out_of_bounds else 1.0)
    term_soc_anchor = w_soc_eff * soc_err
    self.info["term_soc_anchor"] = float(term_soc_anchor)

    # Catalog term: drift_barrier (existing in edit_base; symmetric quadratic barrier around SOC_init)
    soc_init = float(self.SOC_init)
    d0 = 0.03  # deadband (< soc_drift_abs_max=0.05)
    p = 2.0
    drift_excess = float(np.maximum(0.0, np.abs(soc - soc_init) - d0))
    c_drift = 20000.0
    term_drift_barrier = c_drift * (drift_excess ** p)
    self.info["term_drift_barrier"] = float(term_drift_barrier)

    # Catalog term: fc_peak_shave (ADDED; charge_sustaining; SOC-gated FC peak cap)
    # c * g(SOC) * max(0, P_FCS - P_cap), with g=0 at/below SOC_target-m and nondecreasing
    P_fcs_kw = float(self.P_FCS)
    P_cap = 12.0  # near the peak-efficiency band (10-15 kW); must be >= 8 kW
    m = 0.05
    g_soc = float(np.clip((soc - (soc_tgt - m)) / m, 0.0, 1.0))
    c_peak = 0.7  # sized so added drift-step cost is O(1e3-1e4) on the baseline replay, not just the MINIMUM
    term_fc_peak_shave = c_peak * g_soc * float(np.maximum(0.0, P_fcs_kw - P_cap))
    self.info["term_fc_peak_shave"] = float(term_fc_peak_shave)

    soc_cost = float(term_soc_anchor + term_drift_barrier + term_fc_peak_shave)

    # ---------- Core operating-cost proxy terms (existing) ----------
    h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal
    h2_cost = float(self.w_h2) * float(h2_fcs)
    fcs_soh_cost = float(self.w_fc) * float(self.dSOH_FCS)
    batt_soh_cost = float(self.w_batt) * float(self.dSOH_batt)

    # ---------- Extra catalog price terms (existing in edit_base): fc_efficiency_gap, batt_ohmic ----------
    # Catalog term: fc_efficiency_gap
    h2_fcs_g = float(h2_fcs)
    eta_ref = 0.602  # peak measured band (10-15 kW) from EFFICIENCY FACTS
    eta = float(P_fcs_kw / (120.0 * h2_fcs_g)) if h2_fcs_g > 0.0 else 0.0
    eta_gap_frac = float(np.maximum(0.0, eta_ref - eta) / eta_ref) if h2_fcs_g > 0.0 else 0.0
    c_eff_gap = 5.0
    term_fc_efficiency_gap = c_eff_gap * h2_fcs_g * eta_gap_frac
    self.info["term_fc_efficiency_gap"] = float(term_fc_efficiency_gap)

    # Catalog term: batt_ohmic
    P_batt_loss_kw = float(self.P_batt_loss_kw)
    c_batt_ohmic = 2.0
    term_batt_ohmic = c_batt_ohmic * float(np.maximum(0.0, P_batt_loss_kw))
    self.info["term_batt_ohmic"] = float(term_batt_ohmic)

    # Total objective
    objective_cost = (
        soc_cost
        + h2_cost
        + fcs_soh_cost
        + batt_soh_cost
        + term_fc_efficiency_gap
        + term_batt_ohmic
    )
    reward = float(-objective_cost)

    in_bounds = (float(soc_low) < soc < float(soc_high))
    self.info.update(
        {
            "EMS_reward": float(reward),
            "h2_fcs": float(h2_fcs),
            "h2_batt": float(h2_batt),
            "h2_equal": float(h2_equal),
            "soc_cost": float(soc_cost),
            "h2_cost": float(h2_cost),
            "fcs_soh_cost": float(fcs_soh_cost),
            "batt_soh_cost": float(batt_soh_cost),
            "objective_cost": float(objective_cost),
            "soc_in_bounds": int(in_bounds),
        }
    )
    return reward
