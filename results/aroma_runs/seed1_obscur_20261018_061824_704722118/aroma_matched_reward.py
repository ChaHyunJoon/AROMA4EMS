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
        # >0 이면 action 을 dP_FCS 로 해석 (agentEMS_pure_h2_consumption.py 와 동일 규약).
        # get_reward 밖이므로 LDRI 의 reward 패치와 충돌하지 않는다.
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
        self.P_batt_loss_kw = 0.0   # battery ohmic loss r0*I^2, kW (>= 0 always)
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
        self.P_batt_loss_kw = 0.0   # battery ohmic loss r0*I^2, kW (>= 0 always)
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
    
    def get_info(self):
        return self.info

    def get_done(self):
        return self.done
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

        soc_cost = float(term_soc_anchor)

        # ---------- Core operating-cost proxy terms (existing) ----------
        h2_fcs, h2_batt, h2_equal = self.h2_fcs, self.h2_batt, self.h2_equal
        h2_cost = float(self.w_h2) * float(h2_fcs)
        fcs_soh_cost = float(self.w_fc) * float(self.dSOH_FCS)
        batt_soh_cost = float(self.w_batt) * float(self.dSOH_batt)

        # ---------- Extra catalog price terms (ADDED): fc_efficiency_gap, batt_ohmic ----------
        # Catalog term: fc_efficiency_gap
        # eta = P_FCS / (120 * h2_fcs) for 1-s step, with 120 kJ/g LHV
        P_fcs_kw = float(self.P_FCS)
        h2_fcs_g = float(h2_fcs)
        eta_ref = 0.602  # peak measured band (10-15 kW) from EFFICIENCY FACTS
        eta = float(P_fcs_kw / (120.0 * h2_fcs_g)) if h2_fcs_g > 0.0 else 0.0
        eta_gap_frac = float(np.maximum(0.0, eta_ref - eta) / eta_ref) if h2_fcs_g > 0.0 else 0.0
        c_eff_gap = 5.0  # reward units per gram-scaled gap; moderate to satisfy deviation check
        term_fc_efficiency_gap = c_eff_gap * h2_fcs_g * eta_gap_frac
        self.info["term_fc_efficiency_gap"] = float(term_fc_efficiency_gap)

        # Catalog term: batt_ohmic
        P_batt_loss_kw = float(self.P_batt_loss_kw)
        c_batt_ohmic = 2.0  # reward units per kW-step; sized to be comparable to baseline mean soc_cost scale
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
    