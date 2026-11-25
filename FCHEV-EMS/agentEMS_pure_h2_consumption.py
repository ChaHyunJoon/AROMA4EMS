import numpy as np
from FCHEV_SOH import FCHEV_SOH
from Battery import CellModel1


class EMS:
    """ EMS with SOH """
    def __init__(
        self,
        w_soc,
        soc0,
        SOC_MODE,
        abs_spd_MAX,
        abs_acc_MAX,
        w_h2=10.0,        # 전국 수소충전소 평균 단가: 10원/g
        w_fc=4.275e6,     # PEMFC stack 교체비용 [KRW]: DoE 2025 상용차 양산단가 30$(4.5e4원)/kW x 95kW. dSOH_FCS 는 전압 열화 비율(0.01 = 1%)이라 1% 열화당 w_fc/100 KRW
        w_batt=1.116e6,     # 배터리 팩 교체비용 [KRW]: BloombergNEF 2025 Li-ion 팩 평균 1.5e5원/kWh. dSOH_batt 는 용량 손실 비율(0.01 = 1%)이라 1% 손실당 w_batt/100 KRW
        eq_h2_batt_coef=0.0164,
        soc_target=0.6,
        soc_bounds=(0.4, 0.8),
        ramp_limit_kw=0.0,
    ):
        self.time_step = 1.0
        # >0 이면 action 을 P_FCS 절대값이 아니라 **변화량(dP_FCS)** 으로 해석한다:
        #   P_FCS(t) = clip(P_FCS(t-1) + action * ramp_limit_kw, 0, P_FC_max)
        # Fresh SAC samples action only within the feasible FC increment range,
        # using obs[3] = previous applied P_FCS/P_FC_max. The plant clip remains
        # defensive for historical actors and non-SAC callers.
        # reward 는 건드리지 않는다. 0 이면 기존 절대출력 동작 그대로.
        self.ramp_limit_kw = max(0.0, float(ramp_limit_kw))
        self.w_soc = w_soc
        self.w_h2 = w_h2
        self.w_fc = w_fc
        self.w_batt = w_batt
        self.eq_h2_batt_coef = max(0.0, float(eq_h2_batt_coef))
        soc_low, soc_high = soc_bounds
        if soc_low > soc_high:
            soc_low, soc_high = soc_high, soc_low
        self.soc_bounds = (float(soc_low), float(soc_high))
        self.soc_weight_multiplier = 1.0
        self.done = False
        self.info = {}
        self.FCHEV = FCHEV_SOH()
        self.Battery = CellModel1()
        self.obs_num = 7  # soc, soh-batt, soh-fcs, P_FCS(t-1), P_batt, spd, acc
        self.action_num = 1  # P_FCS (t)
        # motor, unit in W
        self.P_mot_max = self.FCHEV.motor_max_power  # 200,000 W
        self.P_mot = 0
        # FCS, unit in kW
        self.h2_fcs = 0
        self.h2_batt = 0
        self.h2_equal = 0
        self.P_FCS = 0
        self.P_FCS_max = self.FCHEV.P_FC_max        # kW
        self.dSOH_FCS = 0
        self.SOH_FCS = 1.0
        # battery unit in W
        self.SOC_init = soc0        # 0.6
        if soc_target is not None:
            self.SOC_target = float(soc_target)
        elif SOC_MODE == 'CD':        # charge-depletion
            self.SOC_target = self.SOC_init - 0.2
        else:                         # charge-sustaining
            self.SOC_target = self.SOC_init
        self.SOC = self.SOC_init
        self.OCV_initial = self.Battery.ocv_func(self.SOC_init)
        self.SOH_batt = 1.0
        self.Tep_a = 20
        self.P_batt = 0     # W
        self.P_batt_max = self.Battery.batt_maxpower    # in W
        self.SOC_delta = 0
        self.dSOH_batt = 0
        self.I_batt = 0
        # paras_list = [SOC, SOH, Voc]
        self.paras_list = [self.SOC, self.SOH_batt, self.OCV_initial]
        self.travel = 0
        self.car_spd = 0
        self.car_acc = 0
        self.abs_spd_MAX = abs_spd_MAX
        self.abs_acc_MAX = abs_acc_MAX
    
    def reset_obs(self):
        self.SOC = self.SOC_init
        self.SOH_batt = 1.0
        self.SOH_FCS = 1.0
        self.dSOH_FCS = 0
        self.Tep_a = 20
        self.P_mot = 0
        self.P_FCS = 0
        self.P_batt = 0
        self.h2_fcs = 0
        self.h2_batt = 0
        self.h2_equal = 0
        self.FCHEV.P_FC_old = 0.0
        self.paras_list = [self.SOC, self.SOH_batt, self.OCV_initial]
        self.done = False
        self.info = {}
        self.travel = 0
        self.car_spd = 0
        self.car_acc = 0
        
        obs = np.zeros(self.obs_num, dtype=np.float32)  # np.array
        # soc, soh-batt, soh-fcs, P_FCS, P_batt, spd, acc
        obs[0] = self.SOC
        obs[1] = self.SOH_batt
        obs[2] = self.SOH_FCS
        obs[3] = self.P_FCS / self.P_FCS_max        # in kW
        obs[4] = self.P_batt / self.P_batt_max   # in W
        obs[5] = self.car_spd / self.abs_spd_MAX
        obs[6] = self.car_acc / self.abs_acc_MAX
        return obs

    def execute(self, action, car_spd, car_acc):
        from power_constraints import execute
        return execute(self, action, car_spd, car_acc)

    def _equivalent_hydrogen_terms(self):
        h2_fcs = float(self.h2_fcs)
        if not np.isfinite(h2_fcs) or h2_fcs < 0.0:
            h2_fcs = 0.0
        p_batt = float(self.P_batt)
        if not np.isfinite(p_batt):
            p_batt = 0.0
        h2_batt = (p_batt / 1000.0) * self.eq_h2_batt_coef
        h2_equal = h2_fcs + h2_batt
        return h2_fcs, h2_batt, h2_equal
    
    def get_reward(self):
        soc = float(self.SOC)
        soc_low, soc_high = self.soc_bounds
        # SOC deviation from target
        soc_err = (np.abs(soc - self.SOC_target))**2
        w_soc = self.w_soc
        w_soc = np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10, self.w_soc)
        soc_cost = w_soc * (soc_err)

        h2_fcs, h2_batt, h2_equal = self._equivalent_hydrogen_terms()
        self.h2_batt = h2_batt
        self.h2_equal = h2_equal
        h2_cost = self.w_h2 * h2_fcs
        # Cost of fuel cell degradation (scaled)
        fcs_soh_cost = self.w_fc * float(self.dSOH_FCS)
        # Cost of battery degradation (scaled)
        batt_soh_cost = self.w_batt * float(self.dSOH_batt)
        
        in_bounds = (soc_low < soc < soc_high)
        objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost
        reward = -objective_cost
        reward = float(reward)

        self.info.update({'EMS_reward': reward,
                          'h2_fcs': float(h2_fcs),
                          'h2_batt': float(h2_batt),
                          'h2_equal': float(h2_equal),
                          'soc_cost': float(soc_cost),
                          'h2_cost': float(h2_cost),
                          'fcs_soh_cost': float(fcs_soh_cost),
                          'batt_soh_cost': float(batt_soh_cost),
                          'objective_cost': float(objective_cost),
                          'soc_in_bounds': int(in_bounds)
})
        return reward

    def get_info(self):
        return self.info

    def get_done(self):
        return self.done
    
