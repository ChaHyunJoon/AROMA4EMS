import datetime
import os
import numpy as np
import scipy.io as scio
import torch
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm
from common.memory import make_buffer
from common.utils import summarize_fc_efficiency
from sac import SAC


class Runner:
    def __init__(self, args, env):
        self.args = args
        self.env = env
        # Resolve and apply the seed before SAC is constructed so actor/critic
        # initialization is reproducible, not only the later action sampling.
        self.seed = self._resolve_seed()
        self._apply_seed()
        self.buffer = make_buffer(args)
        self.SAC_agent = SAC(args)
        # configuration
        self.episode_num = args.max_episodes
        self.episode_step = args.episode_steps
        self.start_episode = max(0, int(getattr(args, "start_episode", 0)))
        self.DONE = {}
        self.save_path = self.args.save_dir+'/'+self.args.scenario_name
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)
        self.save_path_episode = self.save_path+'/episode_data'
        if not os.path.exists(self.save_path_episode):
            os.makedirs(self.save_path_episode)
        # tensorboard
        fileinfo = args.scenario_name
        self.writer = SummaryWriter(args.log_dir+'/{}_{}_{}_seed{}'.format
                                    (datetime.datetime.now().strftime("%m-%d_%H-%M"),
                                     fileinfo, self.args.DRL, self.seed))

    def _resolve_seed(self):
        if getattr(self.args, "seed", None) is not None:
            return int(self.args.seed)
        elif self.args.random_seed:
            return int(np.random.randint(100))
        else:
            return 93

    def _apply_seed(self):
        np.random.seed(self.seed)
        torch.manual_seed(self.seed)
        torch.cuda.manual_seed_all(self.seed)

    def set_seed(self):
        self._apply_seed()
        print("Random seeds have been set to %d !\n"%self.seed)

    def _evaluate_policy(self):
        """Deterministic rollout (mean action, no exploration) used only to score
        the current policy for best-checkpoint selection. This is the policy that
        is actually used at evaluation/deployment time, so it is the fair signal to
        compare checkpoints on -- unlike the noisy stochastic training return.

        The replay buffer is NOT written to and NO learning step is taken, so the
        agent is unaffected. The torch/numpy RNG state is saved and restored around
        the rollout as a guard, so training reproducibility is bit-identical to a
        run without evaluation.
        """
        torch_state = torch.get_rng_state()
        cuda_state = torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None
        np_state = np.random.get_state()
        try:
            state = self.env.reset()
            eval_reward = 0.0
            objective_cost = 0.0
            travel_m = None
            # collect per-step info so the deterministic rollout can be summarized
            # with the same breakdown (mean_cost / P_fc / H2_100km / SOC) as the
            # stochastic training episode print below.
            ec = {k: [] for k in ('soc_cost', 'h2_cost', 'fcs_soh_cost', 'batt_soh_cost',
                                   'objective_cost', 'h2_fcs', 'h2_batt', 'h2_equal',
                                   'P_fc', 'fce_eff', 'SOC', 'soc_in_bounds')}
            for episode_step in range(self.episode_step):
                with torch.no_grad():
                    action = self.SAC_agent.select_action(state, evaluate=True)
                state_next, step_reward, done, info = self.env.step(action, episode_step)
                state = state_next
                eval_reward += float(step_reward)
                objective_cost += float(info.get('objective_cost', np.nan))
                travel_m = info.get('travel', travel_m)
                for k in ec:
                    ec[k].append(info.get(k, np.nan))
                if done:
                    break
            if travel_m:
                eval_objective_100 = objective_cost / (travel_m / 1000.0) * 100.0
            else:
                eval_objective_100 = float('nan')
            eval_metrics = self._summarize_eval(ec, travel_m)
            eval_metrics['tracking_success'] = not done
            if done:
                eval_objective_100 = np.nan
                for key in ('h2_100', 'h2_equal_100', 'h2_batt_100'):
                    eval_metrics[key] = np.nan
            return eval_reward, eval_objective_100, eval_metrics
        finally:
            np.random.set_state(np_state)
            torch.set_rng_state(torch_state)
            if cuda_state is not None:
                torch.cuda.set_rng_state_all(cuda_state)

    def _summarize_eval(self, ec, travel_m):
        """Summarize a deterministic rollout into the same fields printed for the
        stochastic training episode (mean_cost / P_fc / H2_100km / SOC)."""
        travel_km = (travel_m / 1000.0) if travel_m else float('nan')
        p_fc = np.asarray(ec['P_fc'], dtype=np.float64)
        soc_arr = np.asarray(ec['SOC'], dtype=np.float64)
        mean_fce_eff, pct_fc_on = summarize_fc_efficiency(
            p_fc, ec['fce_eff'], on_threshold=self.env.agent.FCHEV.P_FC_off,
        )
        return {
            'h2_100': np.nansum(ec['h2_fcs']) / travel_km * 100.0,
            'h2_equal_100': np.nansum(ec['h2_equal']) / travel_km * 100.0,
            'h2_batt_100': np.nansum(ec['h2_batt']) / travel_km * 100.0,
            'mean_soc_cost': float(np.nanmean(ec['soc_cost'])),
            'mean_h2_cost': float(np.nanmean(ec['h2_cost'])),
            'mean_fcs_cost': float(np.nanmean(ec['fcs_soh_cost'])),
            'mean_batt_cost': float(np.nanmean(ec['batt_soh_cost'])),
            'mean_objective': float(np.nanmean(ec['objective_cost'])),
            'soc_min': float(np.nanmin(soc_arr)),
            'soc_mean': float(np.nanmean(soc_arr)),
            'soc_max': float(np.nanmax(soc_arr)),
            'soc_final': float(soc_arr[-1]),
            'in_bounds_rate': float(np.nanmean(ec['soc_in_bounds'])) * 100.0,
            'p_fc_min': float(np.nanmin(p_fc)),
            'p_fc_mean': float(np.nanmean(p_fc)),
            'p_fc_max': float(np.nanmax(p_fc)),
            'mean_fce_eff': mean_fce_eff,
            'pct_fc_on': pct_fc_on,
        }

    def run_SAC(self):
        reward = []  # reward of each episode
        c_loss_1 = []
        c_loss_2 = []
        a_loss = []
        en_loss = []
        h2_100_list = []
        h2_batt_100_list = []
        h2_equal_100_list = []
        objective_100_list = []  # objective cost per 100 km
        FCS_SoH = []
        Batt_SoH = []
        SOC = []
        lr_recorder = {'lrcr': [], 'lrac': [], 'lral': []}
        updates = 0  # for tensorboard counter
        best_reward = -float("inf")
        save_best_enabled = getattr(self.args, "save_best", True)
        episode = self.start_episode
        episodes_done = 0
        with tqdm(total=self.episode_num) as pbar:
            while episodes_done < self.episode_num:
                state = self.env.reset()  # reset the environment
                episode_steps = self.episode_step
                episode_reward = []
                c_loss_1_one_ep = []
                c_loss_2_one_ep = []
                a_loss_one_ep = []
                en_loss_one_ep = []
                alpha_value_ep = []
                info = []
                # data being saved in .mat
                episode_info = {'T_mot': [], 'W_mot': [], 'mot_eff': [], 'P_mot': [],
                                'P_fc': [], 'P_fce': [], 'fce_eff': [], 'FCS_SOH': [],
                                'P_dcdc': [], 'dcdc_eff': [], 'FCS_De': [], 'travel': [],
                                'd_s_s': [], 'd_low': [], 'd_high': [], 'd_l_c': [],
                                'EMS_reward': [], 'soc_cost': [], 'h2_fcs': [], 'h2_batt': [], 'h2_equal': [],
                                'objective_cost': [], 'h2_cost': [],
                                'batt_soh_cost': [], 'fcs_soh_cost': [],
                                'SOC': [], 'SOH': [], 'I': [], 'I_c': [],
                                'pack_OCV': [], 'pack_Vt': [], 'pack_power_out': [],
                                'P_batt_req': [], 'tep_a': [], 'dsoh': [],
                                'soc_in_bounds': []}

                for episode_step in range(episode_steps):
                    with torch.no_grad():
                        action = self.SAC_agent.select_action(state, evaluate=False)
                    state_next, step_reward, done, info = self.env.step(action, episode_step)
                    # when done is True: unsafe, stop
                    self.buffer.store(state, action, step_reward, state_next,
                                      done or episode_step + 1 == episode_steps)
                    state = state_next
                    # save data
                    from power_constraints import TRACE_KEYS
                    for key in TRACE_KEYS:
                        if key in info and key not in episode_info:
                            episode_info[key] = []
                    for key in episode_info.keys():
                        episode_info[key].append(info.get(key, np.nan))
                    episode_reward.append(step_reward)
                    # learn
                    if self.buffer.currentSize >= 10*self.args.batch_size:
                        if hasattr(self.buffer, "sample_prioritized"):
                            transition, per_idx, per_w, per_beta = self.buffer.sample_prioritized()
                            critic_loss_1, critic_loss_2, actor_loss, alpha_loss, alpha = \
                                self.SAC_agent.learn(transition, is_weights=per_w)
                            self.buffer.update_priorities(per_idx, self.SAC_agent.last_abs_td)
                            self.writer.add_scalar('per/beta', per_beta, updates)
                            self.writer.add_scalar('per/weight_min', float(per_w.min()), updates)
                        else:
                            transition = self.buffer.random_sample()
                            critic_loss_1, critic_loss_2, actor_loss, alpha_loss, alpha = self.SAC_agent.learn(transition)
                        # save to tensorboard
                        self.writer.add_scalar('loss/critic_1', critic_loss_1, updates)
                        self.writer.add_scalar('loss/critic_2', critic_loss_2, updates)
                        self.writer.add_scalar('loss/actor', actor_loss, updates)
                        self.writer.add_scalar('loss/alpha_loss', alpha_loss, updates)
                        self.writer.add_scalar('entropy/alpha_value', alpha, updates)
                        self.writer.add_scalar('reward/step_reward', step_reward, updates)
                        updates += 1
                        # save in .mat
                        c_loss_1_one_ep.append(critic_loss_1)
                        c_loss_2_one_ep.append(critic_loss_2)
                        a_loss_one_ep.append(actor_loss)
                        en_loss_one_ep.append(alpha_loss)
                        alpha_value_ep.append(alpha)
                    if done and episode not in self.DONE.keys():
                        print('\nfailure in step %d of episode %d'%(episode_step, episode))
                        self.DONE.update({episode: episode_step})
                    if done:
                        # save data in .mat on early termination
                        episode_info.update({'alpha': alpha_value_ep})
                        self.SAC_agent.save_net(episode)
                        datadir = self.save_path_episode+'/data_ep%d.mat'%episode
                        scio.savemat(datadir, mdict=episode_info)
                        break
                    # save data in .mat
                    # if episode_step+1 == self.episode_step:
                    if episode_step+1 == episode_steps:
                        # only save the last 10 episode
                        # save alpha value of each time step in each episode
                        episode_info.update({'alpha': alpha_value_ep})
                        # save network parameters
                        self.SAC_agent.save_net(episode)
                        # save all data in one episode info
                        datadir = self.save_path_episode+'/data_ep%d.mat'%episode
                        scio.savemat(datadir, mdict=episode_info)
                # record current optimizer learning rates
                lrcr, lrac, lral = self.SAC_agent.get_lrs()
                lr_recorder['lrcr'].append(lrcr)
                lr_recorder['lrac'].append(lrac)
                lr_recorder['lral'].append(lral)
                # show episode data
                travel = info['travel']/1000  # km
                h2 = sum(episode_info['h2_fcs'])  # g
                h2_100 = h2/travel*100 if travel > 0 and not done else np.nan
                h2_100_list.append(h2_100)
                h2_batt = sum(episode_info['h2_batt'])  # g
                h2_batt_100 = h2_batt/travel*100 if travel > 0 and not done else np.nan
                h2_batt_100_list.append(h2_batt_100)
                h2_equal = sum(episode_info['h2_equal'])  # g
                h2_equal_100 = h2_equal/travel*100 if travel > 0 and not done else np.nan
                h2_equal_100_list.append(h2_equal_100)
                objective_cost = sum(episode_info['objective_cost'])
                objective_100 = objective_cost/travel*100 if travel > 0 and not done else np.nan
                objective_100_list.append(objective_100)
                soc_arr = np.asarray(episode_info['SOC'], dtype=np.float64)
                soc_min = float(np.min(soc_arr))
                soc_max = float(np.max(soc_arr))
                soc_mean = float(np.mean(soc_arr))
                soc_in_bounds = np.asarray(episode_info['soc_in_bounds'], dtype=np.float64)
                soc_in_bounds_rate = float(np.mean(soc_in_bounds)) * 100.0

                mean_soc_cost = float(np.mean(episode_info['soc_cost']))
                mean_h2_cost = float(np.mean(episode_info['h2_cost']))
                mean_fcs_cost = float(np.mean(episode_info['fcs_soh_cost']))
                mean_batt_cost = float(np.mean(episode_info['batt_soh_cost']))
                mean_objective = float(np.mean(episode_info['objective_cost']))
                p_fc = np.asarray(episode_info['P_fc'], dtype=np.float64)
                p_batt = np.asarray(episode_info['P_batt_req'], dtype=np.float64)
                min_p_fc = float(np.min(p_fc))
                min_p_batt = float(np.min(p_batt))
                mean_p_fc = float(np.mean(p_fc))
                mean_p_batt = float(np.mean(p_batt))
                max_p_fc = float(np.max(p_fc))
                max_p_batt = float(np.max(p_batt))
                mean_fce_eff, pct_fc_on = summarize_fc_efficiency(
                    p_fc,
                    episode_info['fce_eff'],
                    on_threshold=self.env.agent.FCHEV.P_FC_off,
                )
                ep_len = len(episode_reward)
                # print
                soc = info['SOC']
                fcs_soh = info['FCS_SOH']
                bat_soh = info['SOH']
                print('\nepi %d: travel %.3fkm, SOC %.4f, FCS-SOH %.6f, Bat-SOH %.6f'
                      % (episode, travel, soc, fcs_soh, bat_soh))
                print('epi %d: H2_100km %.1fg, H2eq_100km %.1fg (batt %.1fg), objective_100km %.2f'%
                      (episode, h2_100, h2_equal_100, h2_batt_100, objective_100))
                print('epi %d: SOC[min/mean/max]=%.3f/%.3f/%.3f, in_bounds_rate=%.1f%%, len=%d'
                      % (episode, soc_min, soc_mean, soc_max, soc_in_bounds_rate, ep_len))
                print('epi %d: mean_cost soc %.3f, h2eq %.3f, fcs %.3f, batt %.3f, obj %.3f'
                      % (episode, mean_soc_cost, mean_h2_cost, mean_fcs_cost, mean_batt_cost,
                         mean_objective))
                print('epi %d: P_fc min/mean/max %.2f/%.2f/%.2f kW, P_batt_req min/mean/max %.2f/%.2f/%.2f kW, fce_eff mean %.3f, fc_on %.1f%%'
                      % (episode, min_p_fc, mean_p_fc, max_p_fc, min_p_batt, mean_p_batt, max_p_batt, mean_fce_eff, pct_fc_on))
                # FC 열화의 원인별 카운트. dSOH_FCS 는 네 원인이 합산된 값이라, 이 분해가 없으면
                # "어느 메커니즘이 열화를 만들었는지"를 로그만 보고는 알 수 없다.
                dcause = {k: int(np.count_nonzero(np.nan_to_num(
                    np.asarray(episode_info[k], dtype=np.float64)))) for k in
                    ('d_s_s', 'd_low', 'd_high', 'd_l_c')}
                print('epi %d: fc_degr_causes start_stop %d, low_power %d, high_power %d, load_change %d'
                      % (episode, dcause['d_s_s'], dcause['d_low'], dcause['d_high'], dcause['d_l_c']))
                # cumulative reward over the episode and average losses
                ep_r = float(np.sum(episode_reward)) if episode_reward else 0.0
                ep_c1 = np.mean(c_loss_1_one_ep)
                ep_c2 = np.mean(c_loss_2_one_ep)
                ep_a = np.mean(a_loss_one_ep)
                ep_en = np.mean(en_loss_one_ep)
                if alpha_value_ep:
                    ep_alpha = float(np.mean(alpha_value_ep))
                else:
                    ep_alpha = float(self.SAC_agent.alpha) if self.SAC_agent is not None else 0.0
                print('epi %d: ep_cumulative_r %.3f, c-loss1 %.4f, c-loss2 %.4f, a-loss %.4f, en-loss %.4f, alpha %.6f'
                      % (episode, ep_r, ep_c1, ep_c2, ep_a, ep_en, ep_alpha))
                print('epi %d: lr_critic %.4e, lr_actor %.4e, lr_alpha %.4e' % (episode, lrcr, lrac, lral))
                self.writer.add_scalar('episode/length', ep_len, episode)
                self.writer.add_scalar('episode/soc_min', soc_min, episode)
                self.writer.add_scalar('episode/soc_mean', soc_mean, episode)
                self.writer.add_scalar('episode/soc_max', soc_max, episode)
                self.writer.add_scalar('episode/soc_in_bounds_rate', soc_in_bounds_rate, episode)
                self.writer.add_scalar('episode/mean_soc_cost', mean_soc_cost, episode)
                self.writer.add_scalar('episode/mean_h2_cost', mean_h2_cost, episode)
                self.writer.add_scalar('episode/mean_fcs_soh_cost', mean_fcs_cost, episode)
                self.writer.add_scalar('episode/mean_batt_soh_cost', mean_batt_cost, episode)
                self.writer.add_scalar('episode/mean_objective_cost', mean_objective, episode)
                self.writer.add_scalar('episode/h2_100km', h2_100, episode)
                self.writer.add_scalar('episode/h2_batt_100km', h2_batt_100, episode)
                self.writer.add_scalar('episode/h2_equal_100km', h2_equal_100, episode)
                self.writer.add_scalar('episode/mean_alpha', ep_alpha, episode)
                self.writer.add_scalar('episode/min_p_fc', min_p_fc, episode)
                self.writer.add_scalar('episode/mean_p_fc', mean_p_fc, episode)
                self.writer.add_scalar('episode/max_p_fc', max_p_fc, episode)
                self.writer.add_scalar('episode/min_p_batt', min_p_batt, episode)
                self.writer.add_scalar('episode/mean_p_batt', mean_p_batt, episode)
                self.writer.add_scalar('episode/max_p_batt', max_p_batt, episode)
                self.writer.add_scalar('episode/mean_fce_eff', mean_fce_eff, episode)
                self.writer.add_scalar('episode/pct_fc_on', pct_fc_on, episode)
                # save best checkpoint -- judged on the DETERMINISTIC policy (mean
                # action), which is what is actually used at evaluation/deployment.
                # The stochastic training return (ep_r) is too noisy to compare
                # checkpoints fairly: its episode-to-episode swing is dominated by
                # Gaussian exploration noise, so "best" tends to freeze on a single
                # lucky early episode instead of tracking real policy improvement.
                eval_interval = max(1, int(getattr(self.args, "eval_interval", 1)))
                do_eval = (episode % eval_interval == 0) or (episodes_done + 1 == self.episode_num)
                if do_eval:
                    eval_r, eval_obj_100, em = self._evaluate_policy()
                    self.writer.add_scalar('episode/eval_reward', eval_r, episode)
                    self.writer.add_scalar('episode/eval_objective_100km', eval_obj_100, episode)
                    print('epi %d: eval_reward %.3f, eval_objective_100km %.2f (deterministic)'
                          % (episode, eval_r, eval_obj_100))
                    print('epi %d [eval]: H2_100km %.1fg, H2eq_100km %.1fg (batt %.1fg)'
                          % (episode, em['h2_100'], em['h2_equal_100'], em['h2_batt_100']))
                    print('epi %d [eval]: SOC[min/mean/max]=%.3f/%.3f/%.3f, final %.3f, in_bounds_rate=%.1f%%'
                          % (episode, em['soc_min'], em['soc_mean'], em['soc_max'], em['soc_final'], em['in_bounds_rate']))
                    print('epi %d [eval]: mean_cost soc %.3f, h2 %.3f, fcs %.3f, batt %.3f, obj %.3f'
                          % (episode, em['mean_soc_cost'], em['mean_h2_cost'], em['mean_fcs_cost'],
                             em['mean_batt_cost'], em['mean_objective']))
                    print('epi %d [eval]: P_fc min/mean/max %.2f/%.2f/%.2f kW, fce_eff mean %.3f, fc_on %.1f%%'
                          % (episode, em['p_fc_min'], em['p_fc_mean'], em['p_fc_max'], em['mean_fce_eff'], em['pct_fc_on']))
                    self.writer.add_scalar('episode/eval_mean_soc_cost', em['mean_soc_cost'], episode)
                    self.writer.add_scalar('episode/eval_mean_h2_cost', em['mean_h2_cost'], episode)
                    self.writer.add_scalar('episode/eval_mean_fcs_soh_cost', em['mean_fcs_cost'], episode)
                    self.writer.add_scalar('episode/eval_mean_batt_soh_cost', em['mean_batt_cost'], episode)
                    self.writer.add_scalar('episode/eval_h2_100km', em['h2_100'], episode)
                    self.writer.add_scalar('episode/eval_soc_final', em['soc_final'], episode)
                    self.writer.add_scalar('episode/eval_mean_p_fc', em['p_fc_mean'], episode)
                    if eval_r > best_reward:
                        best_reward = eval_r
                        if save_best_enabled:
                            self.SAC_agent.save_best(episode, eval_r)
                            print(f'best checkpoint updated: ep {episode}, eval_reward {eval_r:.3f}')
                if self.SAC_agent is not None:
                    self.SAC_agent.step_lr_schedulers()
                reward.append(ep_r)
                c_loss_1.append(ep_c1)
                c_loss_2.append(ep_c2)
                a_loss.append(ep_a)
                en_loss.append(ep_en)
                FCS_SoH.append(fcs_soh)
                Batt_SoH.append(bat_soh)
                SOC.append(soc)
                episodes_done += 1
                pbar.update(1)
                episode += 1
        
        scio.savemat(self.save_path+'/reward.mat', mdict={'reward': reward})
        scio.savemat(self.save_path+'/critic_loss.mat', mdict={'c_loss_1': c_loss_1, 'c_loss_2': c_loss_2})
        scio.savemat(self.save_path+'/actor_loss.mat', mdict={'a_loss': a_loss})
        scio.savemat(self.save_path+'/entropy_loss.mat', mdict={'en_loss': en_loss})
        scio.savemat(self.save_path+'/lr_recorder.mat', mdict=lr_recorder)
        scio.savemat(self.save_path+'/h2.mat', mdict={'h2': h2_100_list})
        scio.savemat(self.save_path+'/h2_batt.mat', mdict={'h2_batt': h2_batt_100_list})
        scio.savemat(self.save_path+'/h2_equal.mat', mdict={'h2_equal': h2_equal_100_list})
        scio.savemat(self.save_path+'/objective.mat', mdict={'objective_100': objective_100_list})
        scio.savemat(self.save_path+'/FCS_SOH.mat', mdict={'FCS_SOH': FCS_SoH})
        scio.savemat(self.save_path+'/Batt_SOH.mat', mdict={'Batt_SOH': Batt_SoH})
        scio.savemat(self.save_path+'/SOC.mat', mdict={'SOC': SOC})

    def memory_info(self):
        print('\nbuffer counter:', self.buffer.counter)
        print('buffer current size:', self.buffer.currentSize)
        print('replay ratio: %.3f'%(self.buffer.counter/self.buffer.currentSize))
        print('failure:', self.DONE)
