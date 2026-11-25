import datetime
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import scipy.io as scio
import torch
import sys
from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.paper_fuel_economy import paper_fuel_economy
from common.memory import make_buffer
from common.utils import summarize_fc_efficiency
from sac import SAC
from policy_evidence import rollout_physics


H2_LHV_KWH_PER_KG = 33.33
BATTERY_CAPACITY_KWH = 1.56
FC_EFFICIENCY = 0.50


def _action_mode_line(args) -> str:
    """학습 로그 헤더용 action mode 한 줄 (스펙 A2: confound 재발 방지)."""
    ramp = float(getattr(args, "ramp_limit_kw", 0.0) or 0.0)
    mode = f"delta (R={ramp:.1f} kW/s)" if ramp > 0 else "absolute"
    per = "on" if getattr(args, "per", False) else "off"
    return f"action mode: {mode}, PER: {per}"


def _as_1d_float(values):
    arr = np.asarray(values, dtype=np.float64).reshape(-1)
    if arr.size == 0:
        return np.zeros((0,), dtype=np.float64)
    return np.where(np.isfinite(arr), arr, 0.0)


def compute_paper_style_gkm(travel_m, h2_fcs_gps, soc_series, dt_s=1.0):
    """SAE J2572 Method A: charge-sustaining equivalent H2 (g/km) with fuel-only SOC correction.

    h2_eq = h2_fcs + (soc_i - soc_f) * E_batt / (eta_fc * LHV_H2) * 1000
    g/km  = h2_eq / drive_km   (drive distance is fixed; no mileage correction)
    """
    travel_m = float(travel_m)
    if not np.isfinite(travel_m) or travel_m <= 1e-12:
        return np.nan

    h2_gps = _as_1d_float(h2_fcs_gps)
    if h2_gps.size == 0:
        return np.nan

    drive_mileage_km = travel_m / 1000.0
    fuel_cell_h2_g = float(np.sum(h2_gps) * float(dt_s))

    soc_arr = _as_1d_float(soc_series)
    finite_soc = soc_arr[np.isfinite(soc_arr)]
    if finite_soc.size >= 2:
        delta_soc = float(finite_soc[0]) - float(finite_soc[-1])
        batt_eq_h2_g = (delta_soc * BATTERY_CAPACITY_KWH) / (H2_LHV_KWH_PER_KG * FC_EFFICIENCY) * 1000.0
    else:
        batt_eq_h2_g = 0.0

    equivalent_fuel_g = fuel_cell_h2_g + batt_eq_h2_g

    if not np.isfinite(drive_mileage_km) or drive_mileage_km <= 1e-12:
        return np.nan
    if not np.isfinite(equivalent_fuel_g):
        return np.nan
    return equivalent_fuel_g / drive_mileage_km


@dataclass
class ChunkResult:
    iteration: int
    start_episode: int
    end_episode: int
    log_path: str
    episode_data_dir: str
    model_dir: str
    chunk_dir: str
    best_episode: Optional[int]
    best_reward: Optional[float]


class RunnerLDRI:
    """AROMA-style runner: train chunk episodes, then allow outer-loop reward refinement."""

    def __init__(self, args, env, run_root):
        self.args = args
        self.env = env
        self.run_root = Path(run_root)
        self.run_root.mkdir(parents=True, exist_ok=True)
        self.model_root = Path(self.args.save_dir).resolve()
        self.model_root.mkdir(parents=True, exist_ok=True)

        self.seed = self._resolve_seed()
        self._apply_seed()
        self.buffer = make_buffer(args)
        self.SAC_agent = SAC(args)

        self.current_episode = int(getattr(args, "start_episode", 0))
        self.episode_step = int(args.episode_steps)
        self.DONE = {}

        self.best_reward = -float("inf")
        self.best_episode = None

    def _resolve_seed(self):
        if getattr(self.args, "seed", None) is not None:
            return int(self.args.seed)
        if getattr(self.args, "random_seed", True):
            return int(np.random.randint(10000))
        return 93

    def _apply_seed(self):
        np.random.seed(self.seed)
        torch.manual_seed(self.seed)
        torch.cuda.manual_seed_all(self.seed)

    @staticmethod
    def _episode_info_template():
        return {
            "T_mot": [],
            "W_mot": [],
            "mot_eff": [],
            "P_mot": [],
            "P_fc": [],
            "P_fce": [],
            "fce_eff": [],
            "FCS_SOH": [],
            "P_dcdc": [],
            "dcdc_eff": [],
            "FCS_De": [],
            "travel": [],
            "d_s_s": [],
            "d_low": [],
            "d_high": [],
            "d_l_c": [],
            "EMS_reward": [],
            "soc_cost": [],
            "h2_fcs": [],
            "h2_batt": [],
            "h2_equal": [],
            "objective_cost": [],
            "h2_cost": [],
            "batt_soh_cost": [],
            "fcs_soh_cost": [],
            "SOC": [],
            "SOH": [],
            "I": [],
            "I_c": [],
            "pack_OCV": [],
            "pack_Vt": [],
            "pack_power_out": [],
            "P_batt_req": [],
            "P_batt_loss_kw": [],
            "tep_a": [],
            "dsoh": [],
            "soc_in_bounds": [],
        }

    @staticmethod
    def _append_info(episode_info, info):
        from power_constraints import TRACE_KEYS
        for key in TRACE_KEYS:
            if key in info and key not in episode_info:
                episode_info[key] = []
        for key in episode_info.keys():
            episode_info[key].append(info.get(key, np.nan))

    def _open_chunk_log(self, chunk_dir: Path):
        chunk_dir.mkdir(parents=True, exist_ok=True)
        log_path = chunk_dir / "train_log.log"
        return log_path, log_path.open("w", encoding="utf-8")

    # model을 저장할 directory 생성
    def _configure_model_dir(self, iteration: int) -> Path:
        iter_save_dir = self.model_root / f"iter_{int(iteration):03d}"
        model_dir = iter_save_dir / self.args.scenario_name / "net_params"
        model_dir.mkdir(parents=True, exist_ok=True)
        ckpt_prefix = f"iter{int(iteration):03d}"

        # Keep args and agents aligned so checkpoints are written per AROMA iteration.
        self.args.save_dir = str(iter_save_dir)
        self.args.checkpoint_prefix = ckpt_prefix
        self.SAC_agent.model_path = str(model_dir)
        self.SAC_agent.set_checkpoint_prefix(ckpt_prefix)
        return model_dir

    @staticmethod
    def _log(log_file, msg):
        print(msg)
        log_file.write(msg + "\n")
        log_file.flush()

    @staticmethod
    def _fmt_hms(seconds):
        seconds = max(0, int(seconds))
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def _finalize_episode_metrics(self, episode_info, info, episode_reward):
        travel_m = float(info["travel"])
        travel = travel_m / 1000.0
        h2 = float(np.sum(episode_info["h2_fcs"]))
        h2_100 = h2 / travel * 100.0 if travel > 1e-9 else np.nan
        h2_batt = float(np.nansum(np.asarray(episode_info.get("h2_batt", []), dtype=np.float64)))
        h2_batt_100 = h2_batt / travel * 100.0 if travel > 1e-9 else np.nan
        h2_equal = float(np.nansum(np.asarray(episode_info.get("h2_equal", []), dtype=np.float64)))
        h2_equal_100 = h2_equal / travel * 100.0 if travel > 1e-9 else np.nan
        g_per_km = compute_paper_style_gkm(
            travel_m=travel_m,
            h2_fcs_gps=episode_info["h2_fcs"],
            soc_series=episode_info["SOC"],
            dt_s=float(getattr(self.env.agent.FCHEV, "simtime", 1.0)),
        )

        objective_cost = float(np.sum(episode_info["objective_cost"]))
        objective_100 = objective_cost / travel * 100.0 if travel > 1e-9 else np.nan

        soc_arr = np.asarray(episode_info["SOC"], dtype=np.float64)
        soc_min = float(np.min(soc_arr))
        soc_max = float(np.max(soc_arr))
        soc_mean = float(np.mean(soc_arr))

        soc_in_bounds = np.asarray(episode_info["soc_in_bounds"], dtype=np.float64)
        soc_in_bounds_rate = float(np.mean(soc_in_bounds)) * 100.0

        mean_soc_cost = float(np.mean(episode_info["soc_cost"]))
        mean_h2_cost = float(np.mean(episode_info["h2_cost"]))
        mean_fcs_cost = float(np.mean(episode_info["fcs_soh_cost"]))
        mean_batt_cost = float(np.mean(episode_info["batt_soh_cost"]))
        mean_objective = float(np.mean(episode_info["objective_cost"]))

        p_fc = np.asarray(episode_info["P_fc"], dtype=np.float64)
        p_batt = np.asarray(episode_info["P_batt_req"], dtype=np.float64)
        min_p_fc = float(np.min(p_fc))
        mean_p_fc = float(np.mean(p_fc))
        max_p_fc = float(np.max(p_fc))
        min_p_batt = float(np.min(p_batt))
        mean_p_batt = float(np.mean(p_batt))
        max_p_batt = float(np.max(p_batt))

        mean_fce_eff, pct_fc_on = summarize_fc_efficiency(
            p_fc,
            episode_info["fce_eff"],
            on_threshold=self.env.agent.FCHEV.P_FC_off,
        )

        # FC 열화 원인별 이벤트 카운트: run_FC_SOH 의 d_* 는 발동 스텝에서만 양수이고
        # env_physics_facts 의 단가가 "이벤트 1회" 기준이라, 양수 스텝 수 == 이벤트 수.
        def _count_events(key):
            vals = np.nan_to_num(
                np.asarray(episode_info.get(key, []), dtype=np.float64), nan=0.0)
            return int(np.sum(vals > 0.0))

        d_start_stop = _count_events("d_s_s")
        d_low_power = _count_events("d_low")
        d_high_power = _count_events("d_high")
        d_load_change = _count_events("d_l_c")

        ep_len = len(episode_reward)
        ep_r = float(np.sum(episode_reward)) if episode_reward else 0.0
        # Judge the whole drive: a mid-drive shortfall followed by feasible steps
        # still means requested work was not done, so no comparable fuel result.
        from power_constraints import shortfall_steps, summarize_power_violations
        power_violations = summarize_power_violations(
            episode_info, dt_s=float(getattr(self.env.agent.FCHEV, "simtime", 1.0)))
        shortfall = shortfall_steps(power_violations)
        if shortfall is not None:
            delivered = not shortfall
            failure_reason = next(iter(shortfall), "")
        else:  # plant without the per-step trace: only the last step is observable
            delivered = not bool(info.get("power_constraint_failed", False))
            failure_reason = info.get("power_failure_reason", "")
        tracking_success = ep_len == self.episode_step and delivered
        paper_fuel = paper_fuel_economy(
            episode_info, dt_s=float(getattr(self.env.agent.FCHEV, "simtime", 1.0)))
        if not tracking_success:
            # Partial trajectories remain available for diagnostics, never as
            # a fuel result comparable to a completed drive.
            paper_fuel["equivalent_g_per_km"] = np.nan
            h2_100 = h2_batt_100 = h2_equal_100 = g_per_km = objective_100 = np.nan

        return {
            "tracking_success": tracking_success,
            "failure_reason": failure_reason or info.get("power_failure_reason", ""),
            "power_violations": power_violations,
            "paper_fuel": paper_fuel,
            "travel": travel,
            "h2_100": h2_100,
            "h2_batt_100": h2_batt_100,
            "h2_equal_100": h2_equal_100,
            "g_per_km": g_per_km,
            "objective_100": objective_100,
            "soc_min": soc_min,
            "soc_mean": soc_mean,
            "soc_max": soc_max,
            "soc_in_bounds_rate": soc_in_bounds_rate,
            "mean_soc_cost": mean_soc_cost,
            "mean_h2_cost": mean_h2_cost,
            "mean_fcs_cost": mean_fcs_cost,
            "mean_batt_cost": mean_batt_cost,
            "mean_objective": mean_objective,
            "min_p_fc": min_p_fc,
            "mean_p_fc": mean_p_fc,
            "max_p_fc": max_p_fc,
            "min_p_batt": min_p_batt,
            "mean_p_batt": mean_p_batt,
            "max_p_batt": max_p_batt,
            "mean_fce_eff": mean_fce_eff,
            "pct_fc_on": pct_fc_on,
            "d_start_stop": d_start_stop,
            "d_low_power": d_low_power,
            "d_high_power": d_high_power,
            "d_load_change": d_load_change,
            "ep_len": ep_len,
            "ep_r": ep_r,
            "soc": float(info["SOC"]),
            "fcs_soh": float(info["FCS_SOH"]),
            "bat_soh": float(info["SOH"]),
        }

    def _save_episode_data(self, episode_idx, episode_info, episode_data_dir: Path):
        if "alpha" not in episode_info:
            episode_info["alpha"] = []
        datadir = episode_data_dir / f"data_ep{episode_idx}.mat"
        scio.savemat(str(datadir), mdict=episode_info)

    def _retain_episode_artifacts(self, episode_idx):
        compact = (getattr(self.args, "refinement_protocol", "") == "sequential"
                   and getattr(self.args, "artifact_detail", "compact") == "compact")
        return not compact or episode_idx == self.args.chunk_episodes - 1

    def _run_one_episode_sac(self, episode_idx, episode_data_dir):
        state = (self.env.reset_training(episode_idx) if hasattr(self.env, "reset_training")
                 else self.env.reset())
        if hasattr(self.env, "reset_training"):
            import json
            with (self.run_root / "training_initial_states.jsonl").open("a") as stream:
                stream.write(json.dumps({"episode": episode_idx, "initial_soc": float(self.env.agent.SOC),
                                         "initial_fc_kw": float(self.env.agent.P_FCS),
                                         "target_soc": float(self.env.agent.SOC_target)}) + "\n")
        episode_reward = []
        c_loss_1_one_ep = []
        c_loss_2_one_ep = []
        a_loss_one_ep = []
        en_loss_one_ep = []
        alpha_value_ep = []
        episode_info = self._episode_info_template()

        for episode_step in range(self.episode_step):
            with torch.no_grad():
                action = self.SAC_agent.select_action(state, evaluate=False)
            state_next, step_reward, done, info = self.env.step(action, episode_step)
            self.buffer.store(state, action, step_reward, state_next,
                              done or episode_step + 1 == self.episode_step)
            state = state_next

            self._append_info(episode_info, info)
            episode_reward.append(step_reward)

            if self.buffer.currentSize >= 10 * self.args.batch_size:
                if hasattr(self.buffer, "sample_prioritized"):
                    transition, per_idx, per_w, _ = self.buffer.sample_prioritized()
                    c1, c2, a, en, alpha = self.SAC_agent.learn(transition, is_weights=per_w)
                    self.buffer.update_priorities(per_idx, self.SAC_agent.last_abs_td)
                else:
                    transition = self.buffer.random_sample()
                    c1, c2, a, en, alpha = self.SAC_agent.learn(transition)
                c_loss_1_one_ep.append(c1)
                c_loss_2_one_ep.append(c2)
                a_loss_one_ep.append(a)
                en_loss_one_ep.append(en)
                alpha_value_ep.append(alpha)

            if done and episode_idx not in self.DONE:
                self.DONE[episode_idx] = episode_step
            if done:
                break

        episode_info["alpha"] = alpha_value_ep
        if self._retain_episode_artifacts(episode_idx):
            self.SAC_agent.save_net(episode_idx)
            self._save_episode_data(episode_idx, episode_info, episode_data_dir)

        lrcr, lrac, lral = self.SAC_agent.get_lrs()
        metrics = self._finalize_episode_metrics(episode_info, info, episode_reward)

        ep_c1 = float(np.mean(c_loss_1_one_ep)) if c_loss_1_one_ep else 0.0
        ep_c2 = float(np.mean(c_loss_2_one_ep)) if c_loss_2_one_ep else 0.0
        ep_a = float(np.mean(a_loss_one_ep)) if a_loss_one_ep else 0.0
        ep_en = float(np.mean(en_loss_one_ep)) if en_loss_one_ep else 0.0
        ep_alpha = float(np.mean(alpha_value_ep)) if alpha_value_ep else float(self.SAC_agent.alpha)

        metrics.update(
            {
                "ep_c1": ep_c1,
                "ep_c2": ep_c2,
                "ep_a": ep_a,
                "ep_en": ep_en,
                "ep_alpha": ep_alpha,
                "lrcr": lrcr,
                "lrac": lrac,
                "lral": lral,
            }
        )
        if self.SAC_agent is not None:
            self.SAC_agent.step_lr_schedulers()
        return metrics

    def _evaluate_policy_sac(self):
        """Deterministic rollout (mean action, no exploration, no learning) used to
        log the policy's true evaluation/deployment behavior -- mirrors the
        deterministic eval in common/runner.py. Nothing is written to the buffer and
        no learning step is taken; the torch/numpy RNG state is saved and restored so
        training reproducibility is unaffected (get_action calls rsample internally
        even in eval mode). Metrics reuse _finalize_episode_metrics for parity with
        the stochastic episode breakdown."""
        torch_state = torch.get_rng_state()
        cuda_state = torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None
        np_state = np.random.get_state()
        try:
            state = self.env.reset()
            episode_reward = []
            episode_info = self._episode_info_template()
            actions = []
            info = {}
            for episode_step in range(self.episode_step):
                with torch.no_grad():
                    action = self.SAC_agent.select_action(state, evaluate=True)
                actions.append(float(np.asarray(action).reshape(-1)[0]))
                state_next, step_reward, done, info = self.env.step(action, episode_step)
                state = state_next
                self._append_info(episode_info, info)
                episode_reward.append(step_reward)
                if done:
                    break
            metrics = self._finalize_episode_metrics(episode_info, info, episode_reward)
            if getattr(self, "validation_eval_hook", None) is not None:
                episode_info["policy_action"] = actions
                episode_info["speed_m_s"] = self.env.speed_list[:len(actions)]
                episode_info["acceleration_m_s2"] = self.env.acc_list[:len(actions)]
                plant = self.env.agent
                metrics["physical_evidence"] = rollout_physics(
                    episode_info, soc0=self.args.soc0, soc_target=self.args.soc_target,
                    soc_bounds=plant.soc_bounds, dt_s=float(plant.FCHEV.simtime),
                    fc_off_kw=plant.FCHEV.P_FC_off,
                    ramp_threshold_kw_s=plant.FCHEV.P_FC_load_change_rate_thresh)
                # Consumed by the validation hook with the exact checkpoint episode id.
                self.last_validation_rollout = episode_info
            return metrics
        finally:
            np.random.set_state(np_state)
            torch.set_rng_state(torch_state)
            if cuda_state is not None:
                torch.cuda.set_rng_state_all(cuda_state)

    def _log_deterministic_fuel(self, log_file, episode_idx, metrics, strict=True):
        """Persist the exact notebook-compatible row, including its assumptions.

        strict=False is the per-episode training log: an early, untrained policy
        may legitimately fail to complete the drive, which must not abort
        training. Consumers that need tail fuel (backfill, validation tail
        aggregation) still reject a missing row."""
        import json
        row = dict(metrics["paper_fuel"], rollout_soc0=float(self.args.soc0))
        if not np.isfinite(row["equivalent_g_per_km"]):
            if strict:
                raise ValueError("No valid paper-style deterministic fuel economy data")
            self._log(log_file, f"epi {episode_idx} [eval]: incomplete drive, len {metrics['ep_len']}/"
                      f"{self.episode_step}, reason {metrics.get('failure_reason') or 'terminated'}")
            return
        self._log(log_file, f"epi {episode_idx} [eval]: paper_fuel "
                  + json.dumps(row, allow_nan=False, sort_keys=True))

    def _maybe_update_best(self, episode_idx, ep_reward):
        if ep_reward > self.best_reward:
            self.best_reward = float(ep_reward)
            self.best_episode = int(episode_idx)
            if self.SAC_agent is not None and self._retain_episode_artifacts(episode_idx):
                self.SAC_agent.save_best(episode_idx, ep_reward)
            return True
        return False

    def train_chunk(self, iteration, chunk_episodes):
        chunk_episodes = int(chunk_episodes)
        chunk_dir = self.run_root / f"iter_{int(iteration):03d}"
        episode_data_dir = chunk_dir / "episode_data"
        episode_data_dir.mkdir(parents=True, exist_ok=True)
        model_dir = self._configure_model_dir(iteration)
        log_path, log_file = self._open_chunk_log(chunk_dir)

        self._log(log_file, f"AROMA chunk iteration: {iteration}")
        self._log(log_file, f"time: {datetime.datetime.now().isoformat()}")
        self._log(log_file, f"DRL: {self.args.DRL}, seed: {self.seed}")
        self._log(log_file, _action_mode_line(self.args))
        self._log(log_file, f"obs_norm: {getattr(self.args, 'obs_norm', 'fixed')} "
                            f"(speed/{self.args.abs_spd_MAX:.3f} m/s, acc/{self.args.abs_acc_MAX:.3f} m/s2), "
                            f"unserved_cost_per_kw: {getattr(self.args, 'unserved_cost_per_kw', 50.0)}, "
                            f"obs_timing: {getattr(self.args, 'obs_timing', 'current')}")
        self._log(log_file, f"model_dir: {model_dir}")
        self._log(log_file, f"chunk_episodes: {chunk_episodes}, episode_steps: {self.episode_step}")

        start_episode = self.current_episode
        chunk_start_time = time.time()
        with tqdm(total=chunk_episodes, desc=f"AROMA iter {int(iteration):03d}", unit="ep") as pbar:
            for ep_i in range(chunk_episodes):
                episode_idx = self.current_episode

                m = self._run_one_episode_sac(episode_idx, episode_data_dir)
                self._log(
                    log_file,
                    "\nepi %d: travel %.3fkm, SOC %.4f, FCS-SOH %.6f, Bat-SOH %.6f"
                    % (episode_idx, m["travel"], m["soc"], m["fcs_soh"], m["bat_soh"]),
                )
                self._log(
                    log_file,
                    "epi %d: H2_100km %.1fg, H2eq_100km %.1fg (batt %.1fg), g/km %.3f, objective_100km %.2f"
                    % (episode_idx, m["h2_100"], m["h2_equal_100"], m["h2_batt_100"], m["g_per_km"], m["objective_100"]),
                )
                self._log(
                    log_file,
                    "epi %d: SOC[min/mean/max]=%.3f/%.3f/%.3f, in_bounds_rate=%.1f%%, len=%d"
                    % (
                        episode_idx,
                        m["soc_min"],
                        m["soc_mean"],
                        m["soc_max"],
                        m["soc_in_bounds_rate"],
                        m["ep_len"],
                    ),
                )
                self._log(
                    log_file,
                    "epi %d: mean_cost soc %.3f, h2 %.3f, fcs %.3f, batt %.3f, obj %.3f"
                    % (
                        episode_idx,
                        m["mean_soc_cost"],
                        m["mean_h2_cost"],
                        m["mean_fcs_cost"],
                        m["mean_batt_cost"],
                        m["mean_objective"],
                    ),
                )
                self._log(
                    log_file,
                    "epi %d: P_fc min/mean/max %.2f/%.2f/%.2f kW, P_batt_req min/mean/max %.2f/%.2f/%.2f kW, fce_eff mean %.3f, fc_on %.1f%%"
                    % (
                        episode_idx,
                        m["min_p_fc"],
                        m["mean_p_fc"],
                        m["max_p_fc"],
                        m["min_p_batt"],
                        m["mean_p_batt"],
                        m["max_p_batt"],
                        m["mean_fce_eff"],
                        m["pct_fc_on"],
                    ),
                )
                self._log(
                    log_file,
                    "epi %d: fc_degr_causes start_stop %d, low_power %d, high_power %d, load_change %d"
                    % (
                        episode_idx,
                        m["d_start_stop"],
                        m["d_low_power"],
                        m["d_high_power"],
                        m["d_load_change"],
                    ),
                )
                self._log(
                    log_file,
                    "epi %d: ep_cumulative_r %.3f, c-loss1 %.4f, c-loss2 %.4f, a-loss %.4f, en-loss %.4f, alpha %.6f"
                    % (
                        episode_idx,
                        m["ep_r"],
                        m["ep_c1"],
                        m["ep_c2"],
                        m["ep_a"],
                        m["ep_en"],
                        m["ep_alpha"],
                    ),
                )
                self._log(
                    log_file,
                    "epi %d: lr_critic %.4e, lr_actor %.4e, lr_alpha %.4e"
                    % (episode_idx, m["lrcr"], m["lrac"], m["lral"]),
                )

                em = self._evaluate_policy_sac()
                self._log(
                    log_file,
                    "epi %d [eval]: eval_r %.3f, H2_100km %.1fg, H2eq_100km %.1fg (batt %.1fg), g/km %.3f, objective_100km %.2f (deterministic)"
                    % (episode_idx, em["ep_r"], em["h2_100"], em["h2_equal_100"], em["h2_batt_100"], em["g_per_km"], em["objective_100"]),
                )
                self._log(
                    log_file,
                    "epi %d [eval]: SOC[min/mean/max]=%.3f/%.3f/%.3f, final %.3f, in_bounds_rate=%.1f%%"
                    % (episode_idx, em["soc_min"], em["soc_mean"], em["soc_max"], em["soc"], em["soc_in_bounds_rate"]),
                )
                self._log(
                    log_file,
                    "epi %d [eval]: mean_cost soc %.3f, h2 %.3f, fcs %.3f, batt %.3f, obj %.3f"
                    % (episode_idx, em["mean_soc_cost"], em["mean_h2_cost"], em["mean_fcs_cost"], em["mean_batt_cost"], em["mean_objective"]),
                )
                self._log(
                    log_file,
                    "epi %d [eval]: P_fc min/mean/max %.2f/%.2f/%.2f kW, fce_eff mean %.3f, fc_on %.1f%%"
                    % (episode_idx, em["min_p_fc"], em["mean_p_fc"], em["max_p_fc"], em["mean_fce_eff"], em["pct_fc_on"]),
                )
                self._log_deterministic_fuel(log_file, episode_idx, em, strict=False)
                if getattr(self, "validation_eval_hook", None) is not None:
                    self.validation_eval_hook(episode_idx, em)

                # best checkpoint is judged on the DETERMINISTIC eval return (mean
                # action), which is the policy actually used at deployment -- the
                # stochastic training return is too noisy and tends to freeze "best"
                # on a lucky early episode. (matches common/runner.py)
                if self._maybe_update_best(episode_idx, em["ep_r"]):
                    self._log(log_file, f"best checkpoint updated: ep {episode_idx}, reward {em['ep_r']:.3f}")

                self.current_episode += 1
                pbar.update(1)
                pbar.set_postfix(ep=episode_idx, r=f"{m['ep_r']:.1f}", obj100=f"{m['objective_100']:.1f}", gkm=f"{m['g_per_km']:.2f}")

                elapsed = time.time() - chunk_start_time
                done_eps = ep_i + 1
                avg_sec = elapsed / done_eps if done_eps > 0 else 0.0
                remaining_eps = chunk_episodes - done_eps
                eta_sec = avg_sec * remaining_eps
                self._log(
                    log_file,
                    "chunk_progress: %d/%d, elapsed=%s, eta=%s, avg_sec_per_ep=%.1f"
                    % (
                        done_eps,
                        chunk_episodes,
                        self._fmt_hms(elapsed),
                        self._fmt_hms(eta_sec),
                        avg_sec,
                    ),
                )

        end_episode = self.current_episode - 1
        self._log(log_file, f"chunk finished: episodes {start_episode}..{end_episode}")
        self._log(log_file, f"buffer current size: {self.buffer.currentSize}, counter: {self.buffer.counter}")
        log_file.close()

        return ChunkResult(
            iteration=int(iteration),
            start_episode=int(start_episode),
            end_episode=int(end_episode),
            log_path=str(log_path),
            episode_data_dir=str(episode_data_dir),
            model_dir=str(model_dir),
            chunk_dir=str(chunk_dir),
            best_episode=self.best_episode,
            best_reward=(None if self.best_reward == -float("inf") else self.best_reward),
        )
