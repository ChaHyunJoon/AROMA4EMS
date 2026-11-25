import numpy as np


class RuleBasedFCEMS:
    """Fig. 11-inspired rule-based controller.

    The controller follows the paper-style logic shown in the attached figure:
    - `P_req < 0`: fuel cell off during braking/deceleration
    - start from stop: fuel cell provides route-average power `P_avg`
    - steady driving: fuel cell stays near `P_avg`, battery handles transients
    - low SOC: fuel cell output rises above `P_req` to recover battery charge

    A few practical details are added for this codebase:
    - `P_avg` is estimated from the driving cycle power profile
    - equality checks against `P_avg` use a tolerance band
    - previous SOC / previous FC power are tracked explicitly
    """

    MODE_REGEN_OFF = 0
    MODE_BATTERY_ONLY = 1
    MODE_START_AVERAGE = 2
    MODE_STEADY_AVERAGE = 3
    MODE_RECOVERY_CHARGE = 4
    MODE_DEEP_CHARGE = 5

    MODE_NAMES = {
        MODE_REGEN_OFF: "regen_off",
        MODE_BATTERY_ONLY: "battery_only",
        MODE_START_AVERAGE: "start_average",
        MODE_STEADY_AVERAGE: "steady_average",
        MODE_RECOVERY_CHARGE: "recovery_charge",
        MODE_DEEP_CHARGE: "deep_charge",
    }

    def __init__(
        self,
        fchev,
        speed_list=None,
        acc_list=None,
        soc_target=0.6,
        soc_turn_on=0.57,
        soc_turn_off=0.605,
        soc_force_charge=0.54,
        demand_turn_on_kw=18.0,
        demand_turn_off_kw=8.0,
        min_fc_on_kw=10.0,
        ramp_up_kw_per_s=8.0,
        ramp_down_kw_per_s=10.0,
        min_on_steps=15,
        min_off_steps=5,
        reserve_kw=4.0,
        charge_bias_gain_kw_per_soc=220.0,
        auto_calibrate=True,
        soc_initial=None,
        soc_deep_charge=0.30,
        soc_recovery_floor=0.30,
        soc_recovery_ceiling=0.45,
        average_power_floor_kw=8.0,
        average_power_quantile=0.50,
        average_hold_tolerance_kw=1.0,
        p_avg_scale=1.0,
        soc_balance_offset=0.0,
        stop_speed_mps=0.3,
        soc_eps=1e-4,
        ramp_limit_kw=0.0,
    ):
        self.fchev = fchev
        self.dt = float(getattr(self.fchev, "simtime", 1.0))

        # Compatibility fields from the previous baseline interface.
        self.soc_target = float(soc_target)
        self.soc_turn_on = float(soc_turn_on)
        self.soc_turn_off = float(soc_turn_off)
        self.soc_force_charge = float(soc_force_charge)
        self.demand_turn_on_kw = float(demand_turn_on_kw)
        self.demand_turn_off_kw = float(demand_turn_off_kw)
        self.min_fc_on_kw = float(min_fc_on_kw)
        self.ramp_up_kw_per_s = float(ramp_up_kw_per_s)
        self.ramp_down_kw_per_s = float(ramp_down_kw_per_s)
        self.min_on_steps = int(min_on_steps)
        self.min_off_steps = int(min_off_steps)
        self.reserve_kw = float(reserve_kw)
        self.charge_bias_gain_kw_per_soc = float(charge_bias_gain_kw_per_soc)

        # Fig. 11 parameters.
        self.soc_deep_charge = float(soc_deep_charge)
        self.soc_recovery_floor = float(soc_recovery_floor)
        self.soc_recovery_ceiling = float(soc_recovery_ceiling)
        self.average_power_floor_kw = float(average_power_floor_kw)
        self.average_power_quantile = float(average_power_quantile)
        self.average_hold_tolerance_kw = float(average_hold_tolerance_kw)
        # Single scalar knob used to charge-balance the baseline on a given cycle.
        # It scales the route-average FC reference, which sets how much surplus
        # power goes to the battery, so the final SOC can be tuned to `soc_target`.
        self.p_avg_scale = float(p_avg_scale)
        # Second single-scalar charge-balance knob: shifts the SOC set-point that the
        # battery-only / recovery-charge logic switches on. Negative values make the
        # controller stop charging earlier, so the cycle ends lower.
        self.soc_balance_offset = float(soc_balance_offset)
        self.stop_speed_mps = float(stop_speed_mps)
        self.soc_eps = float(soc_eps)
        # Plant FC ramp limit (kW per step), the one SAC/AROMA/DP run under. 0: the
        # plant takes absolute FC power and the rule output is applied unramped.
        # >0: the rule output is a target the FC moves toward by at most this much
        # per step, and `select_action` emits the plant's increment action.
        self.ramp_limit_kw = max(0.0, float(ramp_limit_kw))
        self.soc_initial_default = None if soc_initial is None else float(soc_initial)

        self.p_avg_base_kw = max(self.average_power_floor_kw, self.min_fc_on_kw)
        self.p_req0_kw = 0.0
        if auto_calibrate:
            self._auto_calibrate_route_average(speed_list, acc_list)
        self._apply_p_avg_scale()

        self.reset()

    def _apply_p_avg_scale(self):
        self.p_avg_kw = float(
            np.clip(self.p_avg_scale * self.p_avg_base_kw, 0.0, float(self.fchev.P_FC_max))
        )

    def set_p_avg_scale(self, p_avg_scale):
        """Re-scale the average-power reference without re-running route calibration."""
        self.p_avg_scale = float(p_avg_scale)
        self._apply_p_avg_scale()

    def set_soc_balance_offset(self, soc_balance_offset):
        """Shift the SOC set-point the charge / discharge logic balances around."""
        self.soc_balance_offset = float(soc_balance_offset)

    def _soc_balance_reference(self, soc):
        soc_init = self.soc_init if self.soc_init is not None else soc
        return float(soc_init) + self.soc_balance_offset

    def reset(self):
        self.last_p_fc_cmd_kw = 0.0
        self.last_mode_id = self.MODE_REGEN_OFF
        self.prev_soc = None
        self.prev_speed = 0.0
        self.soc_init = self.soc_initial_default

    def _auto_calibrate_route_average(self, speed_list, acc_list):
        if speed_list is None or acc_list is None:
            return

        speed_arr = np.asarray(speed_list, dtype=np.float64).reshape(-1)
        acc_arr = np.asarray(acc_list, dtype=np.float64).reshape(-1)
        if speed_arr.size == 0 or acc_arr.size == 0:
            return

        demands = []
        for car_spd, car_acc in zip(speed_arr, acc_arr):
            p_dem_kw = self.estimate_motor_power_kw(float(car_spd), float(car_acc))
            if np.isfinite(p_dem_kw):
                demands.append(float(p_dem_kw))
        if not demands:
            return

        demand_arr = np.asarray(demands, dtype=np.float64)
        positive_demands = demand_arr[demand_arr > 0.0]
        if positive_demands.size == 0:
            return

        self.p_req0_kw = float(max(0.0, demand_arr[0]))
        positive_mean_kw = float(np.mean(positive_demands))
        positive_quantile_kw = float(
            np.quantile(positive_demands, np.clip(self.average_power_quantile, 0.0, 1.0))
        )

        # Keep the average-power reference route-informed but outside the FC-off / low-load corner.
        self.p_avg_base_kw = float(
            np.clip(
                max(self.average_power_floor_kw, positive_mean_kw, 0.7 * positive_quantile_kw),
                self.min_fc_on_kw,
                float(self.fchev.P_FC_max),
            )
        )

    def estimate_motor_power_kw(self, car_spd, car_acc):
        t_axle, w_axle, p_axle = self.fchev.T_W_axle(float(car_spd), float(car_acc))
        _, _, _, p_mot_w = self.fchev.run_motor(t_axle, w_axle, p_axle)
        return float(p_mot_w) / 1000.0

    def _fc_is_off(self, p_fc_kw):
        return float(p_fc_kw) <= float(getattr(self.fchev, "P_FC_off", 0.0))

    def _fc_is_at_average(self, p_fc_kw):
        return abs(float(p_fc_kw) - float(self.p_avg_kw)) <= self.average_hold_tolerance_kw

    def _clip_fc_power(self, p_fc_kw):
        return float(np.clip(float(p_fc_kw), 0.0, float(self.fchev.P_FC_max)))

    def _battery_only_allowed(self, soc, p_req_kw, starting_from_stop, fc_was_off):
        if starting_from_stop or not fc_was_off:
            return False
        soc_ref = self._soc_balance_reference(soc)
        return bool(
            soc >= max(soc_ref - self.soc_eps, self.soc_recovery_ceiling)
            and p_req_kw <= self.p_avg_kw + self.average_hold_tolerance_kw
        )

    def _needs_recovery_charge(self, soc):
        soc_ref = self._soc_balance_reference(soc)
        below_initial = soc < soc_ref - self.soc_eps
        in_recovery_band = self.soc_recovery_floor + self.soc_eps < soc < self.soc_recovery_ceiling - self.soc_eps
        return bool(below_initial or in_recovery_band)

    def select_power_command_kw(self, soc, car_spd, car_acc):
        soc = float(soc)
        car_spd = float(car_spd)
        car_acc = float(car_acc)

        if self.soc_init is None:
            self.soc_init = soc
        if self.prev_soc is None:
            self.prev_soc = soc

        p_req_kw = self.estimate_motor_power_kw(car_spd, car_acc)
        p_req_pos_kw = max(0.0, float(p_req_kw))
        fc_was_off = self._fc_is_off(self.last_p_fc_cmd_kw)
        fc_was_avg = self._fc_is_at_average(self.last_p_fc_cmd_kw)
        starting_from_stop = (
            self.prev_speed <= self.stop_speed_mps
            and car_spd > self.stop_speed_mps
            and p_req_pos_kw > 0.0
        )
        soc_descending = soc < self.prev_soc - self.soc_eps

        mode_id = self.MODE_STEADY_AVERAGE
        target_kw = self.p_avg_kw

        if p_req_kw <= 0.0:
            target_kw = 0.0
            mode_id = self.MODE_REGEN_OFF
        elif self._battery_only_allowed(soc, p_req_pos_kw, starting_from_stop, fc_was_off):
            target_kw = 0.0
            mode_id = self.MODE_BATTERY_ONLY
        elif starting_from_stop:
            target_kw = self.p_avg_kw
            mode_id = self.MODE_START_AVERAGE
        elif soc <= self.soc_deep_charge + self.soc_eps:
            # Deep low-SOC mode: cover traction demand and add route-average surplus
            # to push SOC back toward the 45% recovery band.
            target_kw = p_req_pos_kw + self.p_avg_kw
            mode_id = self.MODE_DEEP_CHARGE
        elif self._needs_recovery_charge(soc) and (fc_was_off or not fc_was_avg or soc_descending):
            target_kw = p_req_pos_kw + self.p_avg_kw
            mode_id = self.MODE_RECOVERY_CHARGE
        else:
            target_kw = self.p_avg_kw
            mode_id = self.MODE_STEADY_AVERAGE

        p_fc_prev_kw = float(self.last_p_fc_cmd_kw)
        p_fc_cmd_kw = self._clip_fc_power(target_kw)
        if self.ramp_limit_kw > 0.0:
            p_fc_cmd_kw = float(np.clip(p_fc_cmd_kw, p_fc_prev_kw - self.ramp_limit_kw,
                                        p_fc_prev_kw + self.ramp_limit_kw))
        self.last_p_fc_cmd_kw = p_fc_cmd_kw
        self.last_mode_id = int(mode_id)
        self.prev_soc = soc
        self.prev_speed = car_spd

        debug = {
            "rb_mode_id": int(mode_id),
            "rb_fc_on": int(not self._fc_is_off(p_fc_cmd_kw)),
            "rb_p_dem": float(p_req_kw),
            "rb_p_fc_target": float(target_kw),
            "rb_p_fc_cmd": float(p_fc_cmd_kw),
            "rb_p_fc_prev": p_fc_prev_kw,
            "rb_p_avg": float(self.p_avg_kw),
            "rb_soc_init": float(self.soc_init),
            "rb_soc_descending": int(soc_descending),
            "rb_starting_from_stop": int(starting_from_stop),
        }
        return float(p_fc_cmd_kw), debug

    def select_action(self, soc, car_spd, car_acc):
        p_fc_cmd_kw, debug = self.select_power_command_kw(soc, car_spd, car_acc)
        if self.ramp_limit_kw > 0.0:
            # float64 so the plant's P_FCS stays equal to the tracked command
            action = (p_fc_cmd_kw - debug["rb_p_fc_prev"]) / self.ramp_limit_kw
            return np.asarray([np.clip(action, -1.0, 1.0)], dtype=np.float64), debug
        action = 2.0 * (p_fc_cmd_kw / float(self.fchev.P_FC_max)) - 1.0
        action = float(np.clip(action, -1.0, 1.0))
        return np.asarray([action], dtype=np.float32), debug

    def get_calibration(self):
        return {
            "p_avg_kw": float(self.p_avg_kw),
            "p_avg_base_kw": float(self.p_avg_base_kw),
            "p_avg_scale": float(self.p_avg_scale),
            "soc_balance_offset": float(self.soc_balance_offset),
            "p_req0_kw": float(self.p_req0_kw),
            "soc_init": None if self.soc_init is None else float(self.soc_init),
            "soc_deep_charge": float(self.soc_deep_charge),
            "soc_recovery_floor": float(self.soc_recovery_floor),
            "soc_recovery_ceiling": float(self.soc_recovery_ceiling),
            "average_power_floor_kw": float(self.average_power_floor_kw),
            "average_power_quantile": float(self.average_power_quantile),
            "average_hold_tolerance_kw": float(self.average_hold_tolerance_kw),
            "soc_target": float(self.soc_target),
            "ramp_limit_kw": float(self.ramp_limit_kw),
            "stop_speed_mps": float(self.stop_speed_mps),
            "mode_names": self.MODE_NAMES,
        }


class EfficientBandRuleEMS:
    """Efficient-band power follower after Liu et al. (2020), Energy 118212.

    Liu's rule for a 62 kW FC: FC off below a 5 kW demand, FC follows the demand
    inside its high-efficiency band (5-17 kW), FC held constant above the band
    while the battery covers the rest. Adapted here:
    - the band is read from this plant's FC system efficiency (stack, BOP and
      DC/DC): the powers whose efficiency is within `band_eff_ratio` of the peak;
      `p_off_kw` is the off threshold and also the lower end of the followed band
    - the FC follows the bus demand (motor power plus a proportional SOC term)
      through the inverse of the DC/DC output map, so following is charge neutral
    - `min_off_s`: once off, the FC stays off at least this long unless the battery
      cannot carry the demand or SOC falls `soc_force_on_band` below its initial
      value. This bounds the start count, which dominates the plant's FC wear.
      The force-on floor is fixed to the initial SOC, not to the balanced reference,
      so the charge-balance knob does not move it
    - `soc_balance_offset` shifts the SOC reference, the single knob
      `rule_based_calibrate.solve_soc_balance` solves for charge balance
    """

    MODE_OFF = 0
    MODE_HOLD_OFF = 1
    MODE_FOLLOW = 2
    MODE_HIGH_HOLD = 3
    MODE_FORCED_ON = 4

    # Charge-balance search range of `soc_balance_offset`: wider than the Fig. 11
    # baseline's because a long minimum off time drains the battery between starts.
    SOC_BALANCE_BOUNDS = (-0.25, 0.30)

    MODE_NAMES = {
        MODE_OFF: "off_low_demand",
        MODE_HOLD_OFF: "min_off_hold",
        MODE_FOLLOW: "follow_band",
        MODE_HIGH_HOLD: "band_upper_hold",
        MODE_FORCED_ON: "forced_on",
    }

    def __init__(
        self,
        fchev,
        p_off_kw=7.7,
        min_off_s=0.0,
        band_eff_ratio=0.95,
        p_band_hi_kw=None,
        soc_gain_kw_per_soc=200.0,
        soc_force_on_band=0.08,
        batt_limit_kw=40.0,
        batt_margin_kw=5.0,
        soc_initial=0.6,
        soc_balance_offset=0.0,
        ramp_limit_kw=0.0,
    ):
        self.fchev = fchev
        self.dt = float(getattr(self.fchev, "simtime", 1.0))
        self.p_fc_max = float(self.fchev.P_FC_max)
        self.p_off_kw = float(p_off_kw)
        self.min_off_s = float(min_off_s)
        self.band_eff_ratio = float(band_eff_ratio)
        self.soc_gain_kw_per_soc = float(soc_gain_kw_per_soc)
        self.soc_force_on_band = float(soc_force_on_band)
        self.batt_limit_kw = float(batt_limit_kw)
        self.batt_margin_kw = float(batt_margin_kw)
        self.soc_initial_default = None if soc_initial is None else float(soc_initial)
        self.soc_balance_offset = float(soc_balance_offset)
        self.ramp_limit_kw = max(0.0, float(ramp_limit_kw))

        # FC stack power -> DC bus power map; the bus side is what the demand is in.
        grid = np.linspace(float(self.fchev.P_FC_off), self.p_fc_max, 2000)
        p_bus, h2, _ = self.fchev.run_fuel_cell(grid)
        p_bus = np.asarray(p_bus, dtype=np.float64)
        sys_eff = p_bus / (np.asarray(h2, dtype=np.float64) * float(self.fchev.H2_LHV_kJ_per_g))
        self._grid_fc = grid
        self._grid_bus = np.maximum.accumulate(p_bus)
        in_band = grid[sys_eff >= self.band_eff_ratio * np.max(sys_eff)]
        self.p_band_lo_eff_kw = float(in_band.min())
        self.p_band_hi_kw = float(in_band.max()) if p_band_hi_kw is None else float(p_band_hi_kw)
        self.reset()

    def reset(self):
        self.last_p_fc_cmd_kw = 0.0
        self.off_time_s = np.inf     # the FC starts cold; the first start is not held back
        self.soc_init = self.soc_initial_default

    def set_soc_balance_offset(self, soc_balance_offset):
        self.soc_balance_offset = float(soc_balance_offset)

    def estimate_motor_power_kw(self, car_spd, car_acc):
        t_axle, w_axle, p_axle = self.fchev.T_W_axle(float(car_spd), float(car_acc))
        _, _, _, p_mot_w = self.fchev.run_motor(t_axle, w_axle, p_axle)
        return float(p_mot_w) / 1000.0

    def fc_power_for_bus_kw(self, p_bus_kw):
        """Stack power whose DC/DC output equals `p_bus_kw` (clipped to the FC range)."""
        return float(np.interp(float(p_bus_kw), self._grid_bus, self._grid_fc))

    def _fc_is_off(self, p_fc_kw):
        return float(p_fc_kw) < float(self.fchev.P_FC_off)

    def select_power_command_kw(self, soc, car_spd, car_acc):
        soc = float(soc)
        if self.soc_init is None:
            self.soc_init = soc
        soc_ref = self.soc_init + self.soc_balance_offset
        p_dem_kw = self.estimate_motor_power_kw(car_spd, car_acc)
        p_bus_kw = p_dem_kw + self.soc_gain_kw_per_soc * (soc_ref - soc)

        fc_was_off = self._fc_is_off(self.last_p_fc_cmd_kw)
        battery_short = p_dem_kw > self.batt_limit_kw - self.batt_margin_kw
        soc_low = soc < self.soc_init - self.soc_force_on_band
        override = battery_short or soc_low
        hold_off = fc_was_off and self.off_time_s < self.min_off_s

        if hold_off and not override:
            target_kw, mode_id = 0.0, self.MODE_HOLD_OFF
        elif p_dem_kw < self.p_off_kw and not soc_low:
            target_kw, mode_id = 0.0, self.MODE_OFF
        else:
            # Followed band: demand plus SOC term, kept inside [p_off, band upper end],
            # raised only as far as the battery limit requires.
            target_kw = float(np.clip(self.fc_power_for_bus_kw(p_bus_kw), self.p_off_kw, self.p_band_hi_kw))
            mode_id = self.MODE_HIGH_HOLD if p_bus_kw > self.fc_power_for_bus_kw(self.p_band_hi_kw) else self.MODE_FOLLOW
            p_need_kw = self.fc_power_for_bus_kw(p_dem_kw - self.batt_limit_kw + self.batt_margin_kw)
            if p_dem_kw - self.batt_limit_kw + self.batt_margin_kw > 0.0 and p_need_kw > target_kw:
                target_kw = p_need_kw
            if hold_off or (soc_low and p_dem_kw < self.p_off_kw):
                mode_id = self.MODE_FORCED_ON
        target_kw = float(np.clip(target_kw, 0.0, self.p_fc_max))

        p_fc_prev_kw = float(self.last_p_fc_cmd_kw)
        p_fc_cmd_kw = target_kw
        if self.ramp_limit_kw > 0.0:
            p_fc_cmd_kw = float(np.clip(p_fc_cmd_kw, p_fc_prev_kw - self.ramp_limit_kw,
                                        p_fc_prev_kw + self.ramp_limit_kw))
        if self._fc_is_off(p_fc_cmd_kw):
            self.off_time_s = (self.off_time_s + self.dt) if fc_was_off else self.dt
        self.last_p_fc_cmd_kw = p_fc_cmd_kw

        debug = {
            "rb_mode_id": int(mode_id),
            "rb_fc_on": int(not self._fc_is_off(p_fc_cmd_kw)),
            "rb_p_dem": float(p_dem_kw),
            "rb_p_fc_target": float(target_kw),
            "rb_p_fc_cmd": float(p_fc_cmd_kw),
            "rb_p_fc_prev": p_fc_prev_kw,
            "rb_soc_init": float(self.soc_init),
            "rb_override": int(override),
        }
        return float(p_fc_cmd_kw), debug

    def select_action(self, soc, car_spd, car_acc):
        p_fc_cmd_kw, debug = self.select_power_command_kw(soc, car_spd, car_acc)
        if self.ramp_limit_kw > 0.0:
            action = (p_fc_cmd_kw - debug["rb_p_fc_prev"]) / self.ramp_limit_kw
            return np.asarray([np.clip(action, -1.0, 1.0)], dtype=np.float64), debug
        action = float(np.clip(2.0 * (p_fc_cmd_kw / self.p_fc_max) - 1.0, -1.0, 1.0))
        return np.asarray([action], dtype=np.float32), debug

    def get_calibration(self):
        return {
            "policy": "efficient_band",
            "p_off_kw": self.p_off_kw,
            "min_off_s": self.min_off_s,
            "band_eff_ratio": self.band_eff_ratio,
            "p_band_lo_eff_kw": self.p_band_lo_eff_kw,
            "p_band_hi_kw": self.p_band_hi_kw,
            "soc_gain_kw_per_soc": self.soc_gain_kw_per_soc,
            "soc_force_on_band": self.soc_force_on_band,
            "batt_limit_kw": self.batt_limit_kw,
            "batt_margin_kw": self.batt_margin_kw,
            "soc_balance_offset": self.soc_balance_offset,
            "soc_init": None if self.soc_init is None else float(self.soc_init),
            "ramp_limit_kw": self.ramp_limit_kw,
            "mode_names": self.MODE_NAMES,
        }
