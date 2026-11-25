def get_reward(self):
    soc = float(self.SOC)
    soc_t = float(self.SOC_target)
    soc_i = float(self.SOC_init)
    soc_low, soc_high = self.soc_bounds

    # -------------------------
    # Charge-sustaining terms (CATALOG): soc_anchor + drift_barrier
    # soc_cost MUST equal the sum of the logged catalog terms.
    # -------------------------

    # (1) soc_anchor (RESHAPED): asymmetric quadratic anchor
    # Penalize SOC deficit (below target) more than surplus to discourage deep discharge
    # that tends to lead to longer FC-off periods and then costly restarts.
    p = 2.0
    c_up = float(self.w_soc) * 0.75    # SOC above target (surplus) price
    c_down = float(self.w_soc) * 2.25  # SOC below target (deficit) price (stronger)

    soc_above = max(0.0, soc - soc_t)
    soc_below = max(0.0, soc_t - soc)

    term_soc_anchor = c_up * (soc_above ** p) + c_down * (soc_below ** p)

    # Optional multiplier outside SOC operating bounds (baseline behavior k=10)
    if (soc >= float(soc_high)) or (soc <= float(soc_low)):
        term_soc_anchor *= 10.0

    # (2) drift_barrier (ADDED): flat near SOC_init, steep beyond a deadband
    # This makes sustained drift expensive per-step (not terminal-only),
    # preventing the learned "FC idles into battery" drift mode from being attractive.
    d0 = 0.03  # deadband (< soc_drift_abs_max=0.05)
    drift = abs(soc - soc_i)
    drift_excess = max(0.0, drift - d0)

    # Sized to be a meaningful lever on the baseline rollout over the 1191 steps with |drift|>0.025:
    # if typical drift_excess ~ O(0.01), then per-step term ~ c_drift * 1e-4;
    # with c_drift=1e5 this is ~10 per step, or ~1.2e4 over 1191 steps (inside the stated 2.0e3..5.0e4 range).
    c_drift = 1.0e5
    term_drift_barrier = c_drift * (drift_excess ** 2.0)

    soc_cost = float(term_soc_anchor + term_drift_barrier)

    # -------------------------
    # Price / wear terms (unchanged)
    # -------------------------
    h2_fcs = float(self.h2_fcs)
    h2_batt = float(self.h2_batt)
    h2_equal = float(self.h2_equal)

    h2_cost = float(self.w_h2) * h2_fcs
    fcs_soh_cost = float(self.w_fc) * float(self.dSOH_FCS)
    batt_soh_cost = float(self.w_batt) * float(self.dSOH_batt)

    in_bounds = (float(soc_low) < soc < float(soc_high))

    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost
    reward = float(-objective_cost)

    # -------------------------
    # Logging (required + every catalog term as self.info['term_<id>'])
    # -------------------------
    self.info.update({
        'EMS_reward': reward,
        'h2_fcs': h2_fcs,
        'h2_batt': h2_batt,
        'h2_equal': h2_equal,

        # Catalog term logs (plain values used in soc_cost sum)
        'term_soc_anchor': float(term_soc_anchor),
        'term_drift_barrier': float(term_drift_barrier),

        'soc_cost': float(soc_cost),
        'h2_cost': float(h2_cost),
        'fcs_soh_cost': float(fcs_soh_cost),
        'batt_soh_cost': float(batt_soh_cost),
        'objective_cost': float(objective_cost),
        'soc_in_bounds': int(in_bounds),
    })
    return reward
