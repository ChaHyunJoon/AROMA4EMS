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
        soc_init = float(self.SOC_init)
        soc_target = float(self.SOC_target)

        # ── soc_anchor (catalog: soc_anchor, symmetric quadratic, unchanged shape from edit base) ──
        soc_err = (soc - soc_target) ** 2
        w_soc_step = np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10.0, self.w_soc)
        term_soc_anchor = float(w_soc_step * soc_err)

        # ── drift_barrier (catalog: drift_barrier, NEW — not in edit base) ──
        # Flat inside |SOC - SOC_init| <= 0.025, quadratic beyond.
        # c=60, d0=0.025, p=2.
        # Sizing: at mean drift 0.06 → 60*(0.06-0.025)^2 = 0.0735/step;
        #         over 2778 steps → ~204 reward units (inside [670.3, 24830] combined with fc_surplus_charge).
        # Checked: zero at |SOC-SOC_init|=0.01 ✓, positive at guard edge 0.05 ✓, nondecreasing ✓.
        c_barrier = 60.0
        d0_barrier = 0.025
        soc_abs_dev = float(np.abs(soc - soc_init))
        barrier_excess = float(np.maximum(0.0, soc_abs_dev - d0_barrier))
        term_drift_barrier = c_barrier * barrier_excess ** 2

        # ── fc_surplus_charge (catalog: fc_surplus_charge, NEW — not in edit base) ──
        # Price FC power flowing into the battery when SOC > SOC_target.
        # g(SOC) = max(0, SOC - SOC_target + 0.05) / 0.05, clamped to [0,1] for interpretability
        #   (ramps 0→1 from SOC=0.55 to SOC=0.65, saturates above).
        # P_fc_to_batt_kw = max(0, min(-P_batt, P_mot - P_batt)) / 1000
        # c=0.8; at mean FC->batt 3.37 kW, g=1: 0.8*3.37=2.70/step;
        #   over ~1000 active steps above target: ~2700 reward units.
        # Combined with drift_barrier ~200: total ~2900, inside [670.3, 24830] ✓.
        # Checked: zero while discharging ✓, zero for pure regen (no FC power) ✓,
        #          zero at SOC_target-0.1=0.50 ✓, positive at SOC_target+0.05=0.65 with FC charging ✓,
        #          nondecreasing in SOC and FC charging power ✓.
        m_surplus = 0.05
        g_surplus = float(np.maximum(0.0, soc - soc_target + m_surplus) / m_surplus)
        # Clamp g to [0, 1] — above SOC_target+m it stays at 1, which is fine (nondecreasing)
        # Actually catalog says g nondecreasing, no upper clamp required; leave unclamped for full signal
        p_batt_w = float(self.P_batt)      # W, + = discharge
        p_mot_w = float(self.P_mot)        # W, motor electrical power
        # FC power into battery (kW): positive only when FC is charging the battery
        p_fc_to_batt_kw = float(np.maximum(0.0, np.minimum(-p_batt_w, p_mot_w - p_batt_w))) / 1000.0
        c_surplus = 0.8
        term_fc_surplus_charge = c_surplus * g_surplus * p_fc_to_batt_kw

        # ── soc_cost = sum of all charge-sustaining terms ──
        soc_cost = term_soc_anchor + term_drift_barrier + term_fc_surplus_charge

        # ── standard price terms (unchanged from edit base) ──
        h2_fcs = self.h2_fcs
        h2_batt = self.h2_batt
        h2_equal = self.h2_equal
        h2_cost = self.w_h2 * float(h2_fcs)
        fcs_soh_cost = self.w_fc * float(self.dSOH_FCS)
        batt_soh_cost = self.w_batt * float(self.dSOH_batt)

        in_bounds = (soc_low < soc < soc_high)
        objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost
        reward = float(-objective_cost)

        self.info.update({
            'EMS_reward':        reward,
            'h2_fcs':            float(h2_fcs),
            'h2_batt':           float(h2_batt),
            'h2_equal':          float(h2_equal),
            'soc_cost':          float(soc_cost),
            'h2_cost':           float(h2_cost),
            'fcs_soh_cost':      float(fcs_soh_cost),
            'batt_soh_cost':     float(batt_soh_cost),
            'objective_cost':    float(objective_cost),
            'soc_in_bounds':     int(in_bounds),
            # catalog term logs (required)
            'term_soc_anchor':        float(term_soc_anchor),
            'term_drift_barrier':     float(term_drift_barrier),
            'term_fc_surplus_charge': float(term_fc_surplus_charge),
        })
        return reward
    