def get_reward(self):
    soc = float(self.SOC)
    soc_low, soc_high = self.soc_bounds
    # SOC deviation from target
    soc_err = (np.abs(soc - self.SOC_target)) ** 2
    w_soc = np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10, self.w_soc)
    soc_cost = w_soc * soc_err

    h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal
    h2_cost = self.w_h2 * h2_fcs
    # Cost of fuel cell degradation (scaled)
    fcs_soh_cost = self.w_fc * float(self.dSOH_FCS)
    # Cost of battery degradation (scaled)
    batt_soh_cost = self.w_batt * float(self.dSOH_batt)

    in_bounds = (soc_low < soc < soc_high)
    objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost
    reward = float(-objective_cost)

    self.info.update({'EMS_reward': reward,
                      'h2_fcs': float(h2_fcs),
                      'h2_batt': float(h2_batt),
                      'h2_equal': float(h2_equal),
                      'soc_cost': float(soc_cost),
                      'h2_cost': float(h2_cost),
                      'fcs_soh_cost': float(fcs_soh_cost),
                      'batt_soh_cost': float(batt_soh_cost),
                      'objective_cost': float(objective_cost),
                      'soc_in_bounds': int(in_bounds)})
    return reward
