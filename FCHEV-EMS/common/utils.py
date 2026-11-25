import os
import sys
import numpy as np
import scipy.io as scio

CYCLE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "project-data",
                         "standard_driving_cycles", "mat-data") + os.sep

def get_driving_cycle(cycle_name):
    cycle_dir = CYCLE_DIR
    filename = cycle_dir + cycle_name + '.mat'     
    data = scio.loadmat(filename)
    speed_list = data['speed_vector'][0]            # class <ndarray>
    return speed_list

def get_driving_cycle_v2(cycle_name):
    cycle_dir = CYCLE_DIR
    filename = cycle_dir + cycle_name
    import xlrd  # only for legacy .xls cycles
    data_sheet = xlrd.open_workbook(filename + '.xls')
    table = data_sheet.sheets()[0] 
    speed_list = table.col_values(0)  # class <list>        # speed list of leading car, be observed by rear car
    return speed_list

def get_acc_limit(speed_list, output_max_min=False):
    num = len(speed_list)
    acc_list = []
    for i in range(1, num):
        acc_list.append(speed_list[i]-speed_list[i-1])
    acc_list.append(0)
    if output_max_min:
        max_acc = max(acc_list)
        min_acc = min(acc_list)
        return acc_list, max_acc, min_acc
    else:
        return acc_list


# Fixed observation scales (2026-09-25). Scaling speed/acceleration by each
# cycle's own maximum made the same physical acceleration look half as large on
# LA92_US06 (3.93 m/s2 max) as on the training cycle (1.86 m/s2). Both scales
# bound every standard cycle (max 36.5 m/s, 3.93 m/s2).
OBS_SPEED_SCALE_MPS = 40.0
OBS_ACC_SCALE_MPS2 = 4.0


def observation_scales(args, speed_list, acc_list):
    """(speed, acceleration) divisors for obs[5], obs[6]; 'cycle' is the legacy per-cycle maximum."""
    mode = getattr(args, "obs_norm", "fixed")
    if mode == "cycle":
        return float(max(abs(speed_list))), float(max(abs(max(acc_list)), abs(min(acc_list))))
    if mode != "fixed":
        raise ValueError(f"obs_norm must be 'fixed' or 'cycle', got {mode!r}")
    scales = (float(getattr(args, "obs_speed_scale", OBS_SPEED_SCALE_MPS)),
              float(getattr(args, "obs_acc_scale", OBS_ACC_SCALE_MPS2)))
    if not all(np.isfinite(v) and v > 0 for v in scales):
        raise ValueError(f"observation scales must be finite and positive, got {scales}")
    return scales


# Observation timing (2026-09-25). The plant serves step t's demand from
# (v[t], a[t]), but obs[5], obs[6] used to carry (v[t-1], a[t-1]): the policy
# answered a demand it had not seen. 'current' gives the policy the speed and
# acceleration of the step its action serves, as rule-based and DP already do.
# 'lagged' reproduces actors trained before 2026-09-25.
OBS_TIMINGS = ("current", "lagged")


def observation_timing(args):
    timing = getattr(args, "obs_timing", "current")
    if timing not in OBS_TIMINGS:
        raise ValueError(f"obs_timing must be one of {OBS_TIMINGS}, got {timing!r}")
    return timing


def set_drive_observation(obs, speed, acc, abs_spd_max, abs_acc_max):
    """Write the speed/acceleration of the step the next action serves into obs[5], obs[6]."""
    obs[5] = speed / abs_spd_max
    obs[6] = acc / abs_acc_max
    return obs


def summarize_fc_efficiency(p_fc, fce_eff, on_threshold=0.0):
    p_fc_arr = np.asarray(p_fc, dtype=np.float64).reshape(-1)
    fce_eff_arr = np.asarray(fce_eff, dtype=np.float64).reshape(-1)

    if p_fc_arr.size == 0:
        return 0.0, 0.0

    fc_on_mask = np.isfinite(p_fc_arr) & (p_fc_arr >= float(on_threshold))
    pct_fc_on = float(np.mean(fc_on_mask)) * 100.0
    if not np.any(fc_on_mask):
        return 0.0, pct_fc_on

    fce_eff_on = fce_eff_arr[fc_on_mask]
    fce_eff_on = fce_eff_on[np.isfinite(fce_eff_on)]
    if fce_eff_on.size == 0:
        return 0.0, pct_fc_on

    return float(np.mean(fce_eff_on)), pct_fc_on

class Logger:
    """
    save log automaticly
    """
    
    def __init__(self, filepath, filename, stream=sys.stdout):
        self.terminal = stream
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        
        # create a note.txt
        notename = filepath+'note.txt'
        if not os.path.exists(notename):
            file = open(filepath+'note.txt', 'w')
            file.write('-----Configuration note-----'+'\n')
            file.close()
        
        self.log = open(filepath+filename, 'a') 
    
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        # flush() 가 no-op 이면 인터프리터 종료 시 sys.stdout.flush() 가 아무것도 안 하고,
        # 파이썬이 self.log 를 닫아주지 않아 버퍼(8KB) 를 못 채운 짧은 실행은 로그가
        # 통째로 사라진다. 실제로 모든 evaluate_log.log 가 0 바이트였던 원인.
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()
