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
    