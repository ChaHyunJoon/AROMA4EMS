def get_reward(self):
    soc = float(self.SOC)
    soc_low, soc_high = self.soc_bounds

    # -----------------------
    # Charge-sustaining terms (must sum exactly into soc_cost)
    # -----------------------

    # term_soc_anchor (catalog: soc_anchor) — baseline symmetric quadratic anchor to SOC_target,
    # with 10x penalty only when outside SOC operating bounds.
    soc_err = float(np.abs(soc - float(self.SOC_target))) ** 2
    w_soc_eff = float(np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10.0, self.w_soc))
    term_soc_anchor = w_soc_eff * soc_err

    # term_fc_surplus_charge (catalog: fc_surplus_charge) — price FC power that is pushed into the battery
    # while SOC is already high (measured drift mechanism).
    #
    # P_fc_to_batt_kw = max(0, min(-P_batt, P_mot - P_batt)) / 1000
    # where P_batt is W (+ discharge), so -P_batt > 0 indicates battery charging.
    P_batt_w = float(self.P_batt)
    P_mot_w = float(self.P_mot)
    P_fc_to_batt_w = max(0.0, min(-P_batt_w, P_mot_w - P_batt_w))
    P_fc_to_batt_kw = P_fc_to_batt_w / 1000.0

    # SOC gate g(SOC): 0 at/below SOC_target - m, linear to 1 at SOC_target, >=0 and nondecreasing
    m = 0.1
    soc_gate = max(0.0, (soc - (float(self.SOC_target) - m)) / m)

    # Coefficient sizing: chosen so (on the edit_base rollout) the summed added cost over the many
    # drifted steps is in-range (DRIFT FACTS), i.e. materially penalizes persistent surplus-charging.
    c_surplus = 2.5  # reward-units per (kW-step) of FC->battery charging when SOC is high
    term_fc_surplus_charge = c_surplus * soc_gate * P_fc_to_batt_kw

    soc_cost = term_soc_anchor + term_fc_surplus_charge

    # -----------------------
    # Price-aligned operating-cost proxy terms (unchanged)
    # -----------------------
    h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal
    h2_cost = float(self.w_h2) * float(h2_fcs)

    fcs_soh_cost = float(self.w_fc) * float(self.dSOH_FCS)
    batt_soh_cost = float(self.w_batt) * float(self.dSOH_batt)

    in_bounds = (soc_low < soc < soc_high)
    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost
    reward = float(-objective_cost)

    # -----------------------
    # Required logging (log every catalog term as term_<id>)
    # -----------------------
    self.info.update({
        'EMS_reward': reward,
        'h2_fcs': float(h2_fcs),
        'h2_batt': float(h2_batt),
        'h2_equal': float(h2_equal),

        # catalog terms
        'term_soc_anchor': float(term_soc_anchor),
        'term_fc_surplus_charge': float(term_fc_surplus_charge),

        # aggregated costs
        'soc_cost': float(soc_cost),
        'h2_cost': float(h2_cost),
        'fcs_soh_cost': float(fcs_soh_cost),
        'batt_soh_cost': float(batt_soh_cost),
        'objective_cost': float(objective_cost),

        'soc_in_bounds': int(in_bounds),
    })
    return reward
