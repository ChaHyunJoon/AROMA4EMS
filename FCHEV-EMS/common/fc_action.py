"""State-dependent support for normalized FC increments (action = dP / ramp)."""
import math
import warnings

import torch
from torch import nn


class FCActionPolicy(nn.Module):
    def configure_fc_actions(self, args, action_space=None):
        ramp = float(getattr(args, 'ramp_limit_kw', 0.0))
        maximum = float(getattr(args, 'fc_max_power_kw', 95.0))
        if not math.isfinite(ramp) or ramp < 0 or not math.isfinite(maximum) or maximum <= 0:
            raise ValueError('FC action bounds require finite ramp >= 0 and FC maximum > 0')
        if ramp > 0 and (args.obs_dim < 4 or args.action_dim != 1 or action_space is not None):
            raise ValueError('FC increments require obs[3]=P_FC/P_max and one normalized action')
        self._configured_fc_ramp = ramp
        self._configured_fc_max = maximum
        self._bounded_fc_actions = ramp > 0
        # Persist semantics with weights: old actors must not silently acquire a
        # different physical action mapping when evaluated by new code.
        self.register_buffer('_fc_action_spec', torch.tensor(
            [1., ramp, maximum], dtype=torch.float64))

    def fc_action_bounds(self, state):
        """Bounds in normalized dP/ramp units, NOT latent network coordinates."""
        previous = state[..., 3:4].clamp(0., 1.) * self._configured_fc_max
        low = (-previous / self._configured_fc_ramp).clamp(min=-1., max=0.)
        high = ((self._configured_fc_max - previous) / self._configured_fc_ramp).clamp(min=0., max=1.)
        return low, high

    def action_affine(self, state, *, unit_interval=False):
        if not self._bounded_fc_actions:
            return self.action_scale, self.action_bias
        low, high = self.fc_action_bounds(state)
        if unit_interval:
            return high - low, low
        return (high - low) / 2., (high + low) / 2.

    def entropy_target(self, state, base_target):
        """Keep the entropy target relative to the available action interval.

        log_pi is the density of the physical normalized action. A narrowed
        interval changes both its entropy and the target by log(width / 2).
        """
        if not self._bounded_fc_actions:
            return base_target
        low, high = self.fc_action_bounds(state)
        return base_target + torch.log((high - low) / 2.).sum(dim=-1, keepdim=True)

    def _load_from_state_dict(self, state_dict, prefix, local_metadata, strict,
                              missing_keys, unexpected_keys, error_msgs):
        key = prefix + '_fc_action_spec'
        if key not in state_dict:
            state_dict[key] = self._fc_action_spec.new_tensor(
                [0., self._configured_fc_ramp, self._configured_fc_max])
            warnings.warn('Legacy actor checkpoint: preserving fixed action support; '
                          'start fresh training to use state-dependent FC action bounds.',
                          UserWarning, stacklevel=3)
        spec = state_dict[key].detach().cpu()
        if (spec.shape != (3,) or not torch.isfinite(spec).all() or
            float(spec[0]) not in (0., 1.) or float(spec[1]) < 0. or float(spec[2]) <= 0.):
            error_msgs.append('Invalid FC action checkpoint specification')
        elif float(spec[0]) == 1. and (
            not math.isclose(float(spec[1]), self._configured_fc_ramp, rel_tol=1e-7) or
            not math.isclose(float(spec[2]), self._configured_fc_max, rel_tol=1e-7)
        ):
            error_msgs.append('FC action checkpoint ramp/max does not match the environment; '
                              'use matching settings or train a fresh actor')
        else:
            self._bounded_fc_actions = bool(spec[0]) and self._configured_fc_ramp > 0.
        super()._load_from_state_dict(state_dict, prefix, local_metadata, strict,
                                     missing_keys, unexpected_keys, error_msgs)
