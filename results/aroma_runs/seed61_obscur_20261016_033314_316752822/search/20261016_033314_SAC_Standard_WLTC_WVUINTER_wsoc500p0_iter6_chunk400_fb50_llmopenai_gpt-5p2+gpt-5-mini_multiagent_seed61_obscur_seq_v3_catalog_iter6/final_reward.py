def get_reward(self):
    soc = float(self.SOC)
    soc_t = float(self.SOC_target)
    soc_low, soc_high = self.soc_bounds

    # -------------------------
    # Charge-sustaining terms (CATALOG): soc_anchor + fc_surplus_charge
    # soc_cost MUST equal the sum of the logged catalog terms.
    # -------------------------

    # (1) soc_anchor (existing; keep the x7 scaling used in edit_base)
    soc_err = (np.abs(soc - soc_t)) ** 2
    w_soc_eff = np.where(
        (soc >= float(soc_high)) | (soc <= float(soc_low)),
        float(self.w_soc) * 10.0,
        float(self.w_soc),
    )
    term_soc_anchor_base = float(w_soc_eff * soc_err)
    term_soc_anchor = 7.0 * term_soc_anchor_base

    # (2) fc_surplus_charge (CATALOG; reshape strength to directly suppress the measured drift mechanism:
    # FC power pushed into the battery while SOC is already high)
    # FC power into the battery: max(0, min(-P_batt, P_mot - P_batt)) / 1000 [kW]
    P_batt_w = float(self.P_batt)   # + = discharge, - = charge
    P_mot_w = float(self.P_mot)
    P_fc_to_batt_w = max(0.0, min(-P_batt_w, P_mot_w - P_batt_w))
    P_fc_to_batt_kw = P_fc_to_batt_w / 1000.0

    # g(SOC): 0 at/below (SOC_target - m), linear ramp to 1 at SOC_target, nondecreasing above
    m = 0.05
    g_soc = max(0.0, soc - soc_t + m) / m

    # Strengthened vs edit_base so that, on the edit_base rollout where FC->battery charging above target
    # is material (reward_id f75cd9... DRIFT FACTS: 0.310 kWh above target), the policy learns to avoid
    # "idle FC -> charge battery" as the way to avoid starts.
    c_surplus = 1.0  # reward-units per (kW-step) * g(SOC)
    term_fc_surplus_charge = float(c_surplus * g_soc * P_fc_to_batt_kw)

    soc_cost = float(term_soc_anchor + term_fc_surplus_charge)

    # -------------------------
    # Price / wear terms
    # -------------------------
    h2_fcs = float(self.h2_fcs)
    h2_batt = float(self.h2_batt)
    h2_equal = float(self.h2_equal)

    h2_cost = float(self.w_h2) * h2_fcs

    # fcs_soh_cost (RESHAPED): convex-in-dSOH_FCS to heavily discourage the start-driven spikes
    # seen in edit_base (reward_id f75cd9...: fc_start_stop_soh_loss ~= fc_loss ~= 0.001079).
    dsoh_fcs = float(self.dSOH_FCS)
    s = 1.96e-05  # one start SOH loss scale from the model facts (reward_id 17afbf8... FC DEGRADATION)
    alpha = 1.35  # mild convexity; equals linear at dsoh_fcs == s, >linear for start-heavy steps
    x = dsoh_fcs / s
    fcs_soh_cost = float(self.w_fc) * (s * (x ** alpha))

    batt_soh_cost = float(self.w_batt) * float(self.dSOH_batt)

    in_bounds = (float(soc_low) < soc < float(soc_high))

    objective_cost = float(soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost)
    reward = float(-objective_cost)

    # -------------------------
    # Logging (required + every catalog term)
    # -------------------------
    self.info.update({
        'EMS_reward': reward,
        'h2_fcs': h2_fcs,
        'h2_batt': h2_batt,
        'h2_equal': h2_equal,

        # Catalog term logs (plain values used in soc_cost sum)
        'term_soc_anchor': float(term_soc_anchor),
        'term_fc_surplus_charge': float(term_fc_surplus_charge),

        'soc_cost': float(soc_cost),
        'h2_cost': float(h2_cost),
        'fcs_soh_cost': float(fcs_soh_cost),
        'batt_soh_cost': float(batt_soh_cost),
        'objective_cost': float(objective_cost),
        'soc_in_bounds': int(in_bounds),
    })
    return reward
