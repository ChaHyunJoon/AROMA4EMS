def get_reward(self):
    soc = float(self.SOC)
    soc_low, soc_high = self.soc_bounds

    # ---------- Charge-sustaining family (soc_cost = sum of catalog terms) ----------
    # Catalog term: soc_anchor (CHANGED SHAPE: asymmetric, still quadratic, still bounds-multiplied)
    soc_tgt = float(self.SOC_target)
    soc_err_up = float(np.maximum(0.0, soc - soc_tgt))
    soc_err_dn = float(np.maximum(0.0, soc_tgt - soc))

    # Asymmetry: over-target SOC is priced more than under-target SOC to resist net overcharge drift
    c_up = 1.50 * float(self.w_soc)
    c_dn = 0.70 * float(self.w_soc)
    p = 2.0

    out_of_bounds = (soc >= float(soc_high)) or (soc <= float(soc_low))
    k_bounds = 10.0 if out_of_bounds else 1.0
    term_soc_anchor = k_bounds * (c_up * (soc_err_up ** p) + c_dn * (soc_err_dn ** p))
    self.info["term_soc_anchor"] = float(term_soc_anchor)

    # Catalog term: fc_surplus_charge (ADDED)
    # FC power into the battery (kW), per catalog definition; only positive when FC is charging the pack.
    P_mot = float(self.P_mot)          # W
    P_batt = float(self.P_batt)        # W, + = discharge
    P_fc_to_batt_kw = float(np.maximum(0.0, np.minimum(-P_batt, P_mot - P_batt)) / 1000.0)

    # SOC gate g(SOC): 0 at/below SOC_target - m, linear to 1 at SOC_target and above
    m = 0.05
    g_soc = float(np.clip((soc - (soc_tgt - m)) / m, 0.0, 1.0))

    # Coefficient sized to land ~5-6k total added cost over the 1682 high-drift steps on the baseline replay.
    c_surplus = 2.0
    term_fc_surplus_charge = c_surplus * g_soc * P_fc_to_batt_kw
    self.info["term_fc_surplus_charge"] = float(term_fc_surplus_charge)

    soc_cost = float(term_soc_anchor + term_fc_surplus_charge)
    self.info["soc_cost"] = float(soc_cost)

    # ---------- Price-aligned operating terms (unchanged set; no extra catalog price terms added) ----------
    h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal
    h2_cost = float(self.w_h2) * float(h2_fcs)

    fcs_soh_cost = float(self.w_fc) * float(self.dSOH_FCS)
    batt_soh_cost = float(self.w_batt) * float(self.dSOH_batt)

    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost
    reward = float(-objective_cost)

    in_bounds = (float(soc_low) < soc < float(soc_high))

    self.info.update({
        "EMS_reward": float(reward),
        "h2_fcs": float(h2_fcs),
        "h2_batt": float(h2_batt),
        "h2_equal": float(h2_equal),
        "h2_cost": float(h2_cost),
        "fcs_soh_cost": float(fcs_soh_cost),
        "batt_soh_cost": float(batt_soh_cost),
        "objective_cost": float(objective_cost),
        "soc_in_bounds": int(in_bounds),
    })
    return reward
