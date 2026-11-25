import os
"""
this scipt contains two LIB power battery models
an Equivalent circuit model
an electro-thermal-aging model
"""
import math
import pickle
from scipy.interpolate import interp1d

# LFP battery pack model based on Rint model 2015- Tang et al. EMS for HEV Including Battery Life Optimization
class CellModel1:
    def __init__(self):
        self.timestep = 1
        self.batt_maxpower = 40000  # W [40 kW]
        
        # Rint 모델 파라미터
        self.Cn = 6.5    # Ah 240V 기준으로 1.56kWh capacity는 6.5Ah로 계산
        self.soc_min = 0.01
        self.soc_max = 1.0
        # Capacity loss model: 2025 Chang et al. (Automotive Innovation 8:1031-1046) Eq. (8)-(9)
        #   Q_loss = (C1*SOC + C2) * exp((-31700 + 163.3*I_L) / (R_gas*(t_env + 273.15))) * Ah_eff^z
        #   D_li-ion = Q_loss / Q_li-ion
        # C1, C2 는 논문 Table 3 값(31Ah: 1287.6/6356.3, 1385.5/4193.2)이 아니라, 이 차량의
        # 배터리 spec(6.5Ah)에 맞게 직접 interpolation 한 값이다. 논문 값으로 되돌리지 말 것.
        self._loss_soc_split = 0.45         # SOC 기준
        self._loss_c1_low = 2129.4          # SOC <= 0.45 구간의 C1
        self._loss_c2_low = 6991.7          # SOC <= 0.45 구간의 C2
        self._loss_c1_high = 2093.4         # SOC > 0.45 구간의 C1
        self._loss_c2_high = 5249.2         # SOC > 0.45 구간의 C2
        self._loss_z = 0.57                 # Throughput 지수 z (Table 3)
        self._loss_t_env = 20.0             # 환경 온도 t_env [degC] (Table 3)
        # exponential values in Capacity loss calculation 
        self._loss_inv_rt = 1.0 / (8.314 * (self._loss_t_env + 273.15))
        self._loss_mAh_to_Ah = 1e-3         # mAh 단위를 Ah로 변환하기 위한 상수
        
        # OCV 맵핑 함수 2025 Chang et al. 논문 기반으로 배터리 팩의 SoC-OCV 데이터로 보간 함수 생성
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project-data", "Battery_data") + os.sep
        self.ocv_func = pickle.load(open(data_dir+'ocv_new.pkl', 'rb'))
        # R_in 맵핑 함수 (pack scale)
        self.r0_func = pickle.load(open(data_dir+'r_in.pkl', 'rb'))
    
    def power_limits(self, paras_list):
        """Feasible terminal watts for one step of this Rint/SOC model.

        Positive is discharge. These are physical SOC limits, not the EMS's
        charge-sustaining target or soft operating band. No state is advanced.
        """
        soc, _, voc = map(float, paras_list)
        resistance = float(self.r0_func(soc))
        if not all(math.isfinite(v) for v in (soc, voc, resistance)) or voc <= 0 or resistance <= 0:
            raise ValueError("Invalid battery state for power limits")
        if not self.soc_min <= soc <= self.soc_max:
            raise ValueError("Battery SOC outside physical bounds")
        charge_per_step = 3600 * self.Cn / self.timestep
        imin = min(0., (soc - self.soc_max) * charge_per_step)
        imax = min(max(0., (soc - self.soc_min) * charge_per_step), voc / (2 * resistance))
        return (max(-self.batt_maxpower, voc * imin - resistance * imin**2),
                min(self.batt_maxpower, voc * imax - resistance * imax**2))

    def run_battery(self, P_batt, paras_list):
        # 발열 관련 State(Tep_c, Tep_s, Tep_a) 모두 제거
        # paras_list = [SOC, SOH, Voc]
        SOC = paras_list[0]
        SOH = paras_list[1]
        Voc = paras_list[2]
        
        # 배터리 파워 제한
        if P_batt > self.batt_maxpower:
            P_batt = self.batt_maxpower
        if P_batt < -self.batt_maxpower:
            P_batt = -self.batt_maxpower
            
        # Rint 모델 전류 계산
        r0 = float(self.r0_func(SOC))
        delta = Voc**2 - 4 * r0 * P_batt
        if delta < 0: 
            I_batt = Voc / (2 * r0)
        else:
            I_batt = (Voc - math.sqrt(delta)) / (2 * r0)     
        
        # 1. SOC Update
        soc_deriv = self.timestep * (I_batt / 3600 / self.Cn)
        SOC_new = SOC - soc_deriv
        
        # Reaching a physical boundary is feasible if the current satisfied
        # power_limits(). Only movement beyond it needs a physical clamp.
        soc_unclamped = SOC_new
        soc_tolerance = 1e-12
        fail = bool(SOC_new > self.soc_max + soc_tolerance or
                    SOC_new < self.soc_min - soc_tolerance)
        SOC_new = min(self.soc_max, max(self.soc_min, SOC_new))

        #pack 단위 OCV, power 계산
        Voc_new = self.ocv_func(SOC_new)
        Vt_new = Voc_new - r0 * I_batt
        power_out = Vt_new * I_batt

        # 2. Aging Model (Bc 대신 Capacity Loss 적용)
        # 이번 스텝(1초) 동안 흐른 전하량 (Ah)
        current_step_Ah = (abs(I_batt) * self.timestep) / 3600.0
        
        Ic_rate = abs(I_batt) / self.Cn
        if SOC <= self._loss_soc_split:
            c1 = self._loss_c1_low
            c2 = self._loss_c2_low
        else:
            c1 = self._loss_c1_high
            c2 = self._loss_c2_high
        # Capacity Loss 계산 (2025-Chang et al. 논문 기반 공식 사용, 단위 변환 포함)
        q_loss_mAh = (c1 * SOC + c2) * math.exp((-31700.0 + 163.3 * Ic_rate) * self._loss_inv_rt) * (current_step_Ah ** self._loss_z)
        dsoh = (q_loss_mAh * self._loss_mAh_to_Ah) / self.Cn     # 용량 손실 비율 (EOL 환산 없음)
        
        SOH_new = SOH - dsoh

        # 아웃풋 정보 정리
        out_info = {'SOC': SOC_new, 'SOH': SOH_new, 'soc_deriv': soc_deriv,
                    'soc_unclamped': soc_unclamped, 'battery_soc_clamped': int(fail),
                    'pack_OCV': Voc_new, 'pack_Vt': Vt_new,
                    'I': I_batt, 'pack_power_out': power_out/1000,
                    'I_c': Ic_rate, 'P_batt_req': P_batt/1000,
                    'tep_a': self._loss_t_env, 'dsoh': dsoh}
                    
        # State 업데이트 (온도 관련 변수 제거)
        paras_list_new = [SOC_new, SOH_new, Voc_new]
        
        return paras_list_new, dsoh, I_batt, fail, out_info
