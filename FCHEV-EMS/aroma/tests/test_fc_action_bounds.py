"""Physical FC action support, SAC densities, replay and checkpoint semantics."""
import io
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch
from torch.distributions import Normal, Beta, TransformedDistribution, TanhTransform, AffineTransform

sys.path[:0] = [str(Path(__file__).resolve().parents[2]), str(Path(__file__).resolve().parents[1])]
from common.network import GaussianPolicy, BetaPolicy


def config(ramp=10., maximum=95.):
    return SimpleNamespace(obs_dim=7, action_dim=1, ramp_limit_kw=ramp, fc_max_power_kw=maximum)


def states(powers, maximum=95.):
    s = torch.zeros(len(powers), 7)
    s[:, 0] = .6
    s[:, 3] = torch.as_tensor(powers) / maximum
    return s


@pytest.mark.parametrize('policy', [GaussianPolicy, BetaPolicy])
@pytest.mark.parametrize('ramp', [10., 19., 120.])
def test_samples_and_deterministic_actions_are_feasible_without_output_clipping(policy, ramp):
    torch.manual_seed(7)
    actor = policy(config(ramp))
    p = torch.tensor([0., 3., 50., 92., 95.]).repeat(80)
    s = states(p)
    sampled, log_pi, mean = actor.get_action(s)
    torch.testing.assert_close(mean, actor.deterministic_action(s))
    for a in (sampled, mean):
        next_power = p[:, None] + ramp * a
        assert torch.all(next_power >= -1e-5)
        assert torch.all(next_power <= 95. + 1e-5)
        assert torch.all(a[p == 0] >= 0.)
        assert torch.all(a[p == 95] <= 0.)
        assert torch.all(a.abs() <= 1.)
    assert torch.isfinite(log_pi).all()
    loss = (log_pi - sampled).mean()
    loss.backward()
    assert all(torch.isfinite(p.grad).all() for p in actor.parameters() if p.grad is not None)
    assert sum(p.grad.abs().sum() for p in actor.parameters() if p.grad is not None) > 0


@pytest.mark.parametrize('policy', [GaussianPolicy, BetaPolicy])
def test_log_density_includes_state_dependent_affine_jacobian(policy):
    torch.manual_seed(12)
    actor = policy(config())
    s = states([0., 3., 50., 92., 95.])
    a, actual_log_pi, _ = actor.get_action(s)
    # Independently evaluate the full distribution using PyTorch transforms.
    lo = torch.tensor([[0.], [-.3], [-1.], [-1.], [-1.]])
    hi = torch.tensor([[1.], [1.], [1.], [.3], [0.]])
    if policy is GaussianPolicy:
        mean, log_std = actor.forward(s)
        distribution = TransformedDistribution(Normal(mean, log_std.exp()),
            [TanhTransform(), AffineTransform((lo+hi)/2, (hi-lo)/2)])
    else:
        alpha, beta = actor.forward(s)
        distribution = TransformedDistribution(Beta(alpha, beta), [AffineTransform(lo, hi-lo)])
    torch.testing.assert_close(actual_log_pi, distribution.log_prob(a), atol=2e-5, rtol=2e-5)
    target = actor.entropy_target(s, -1.)
    torch.testing.assert_close(target, -1. + torch.log((hi-lo)/2))


@pytest.mark.parametrize('policy', [GaussianPolicy, BetaPolicy])
def test_new_checkpoint_roundtrip_and_legacy_action_mapping(policy):
    actor = policy(config())
    for p in actor.parameters():
        torch.nn.init.zeros_(p)
    s = states([0., 50., 95.])
    blob = io.BytesIO()
    torch.save(actor.state_dict(), blob)
    blob.seek(0)
    saved = torch.load(blob, weights_only=True)
    restored = policy(config())
    restored.load_state_dict(saved)
    torch.testing.assert_close(restored.deterministic_action(s), torch.tensor([[.5], [0.], [-.5]]))
    legacy = {k: v for k, v in saved.items() if k != '_fc_action_spec'}
    with pytest.warns(UserWarning, match='Legacy actor'):
        restored.load_state_dict(legacy)
    torch.testing.assert_close(restored.deterministic_action(s), torch.zeros(3, 1))
    assert restored.entropy_target(s, -1.) == -1.
    # Re-saving a legacy actor must continue to preserve its old interpretation.
    again = policy(config())
    again.load_state_dict(restored.state_dict())
    torch.testing.assert_close(again.deterministic_action(s), torch.zeros(3, 1))
    # Loading fresh weights back into the same object restores bounded behavior.
    restored.load_state_dict(saved)
    torch.testing.assert_close(restored.deterministic_action(s), actor.deterministic_action(s))


@pytest.mark.parametrize('ramp,maximum', [(19., 95.), (0., 95.), (10., 100.)])
def test_new_checkpoint_rejects_different_physical_mapping(ramp, maximum):
    actor = GaussianPolicy(config())
    with pytest.raises(RuntimeError, match='ramp/max does not match'):
        GaussianPolicy(config(ramp, maximum)).load_state_dict(actor.state_dict())


@pytest.mark.parametrize('policy', [GaussianPolicy, BetaPolicy])
def test_absolute_power_mode_keeps_fixed_support(policy):
    actor = policy(config(0.))
    for p in actor.parameters():
        torch.nn.init.zeros_(p)
    s = states([0., 95.])
    torch.testing.assert_close(actor.deterministic_action(s), torch.zeros(2, 1))
    assert actor.entropy_target(s, -1.) == -1.
    restored = policy(config(0.))
    restored.load_state_dict(actor.state_dict())
    torch.testing.assert_close(restored.deterministic_action(s), torch.zeros(2, 1))
    with pytest.raises(RuntimeError, match='ramp/max does not match'):
        policy(config(10.)).load_state_dict(actor.state_dict())


@pytest.mark.parametrize('policy_name', ['Gaussian', 'Beta'])
def test_real_environment_replay_and_sac_update_share_feasible_normalized_action(monkeypatch, tmp_path, policy_name):
    from arguments_ldri import get_ldri_args
    from env_ldri import make_env_ldri
    from common.memory import MemoryBuffer
    from sac import SAC
    monkeypatch.setattr(sys, 'argv', ['test'])
    args = get_ldri_args()
    args.cuda, args.ramp_limit_kw, args.policy = False, 10., policy_name
    args.save_dir, args.batch_size, args.buffer_size = str(tmp_path), 4, 4
    args.auto_tune, args.const_lr = True, True
    env, args = make_env_ldri(args)
    env.speed_list, env.acc_list = np.zeros(4), np.zeros(4)
    sac, replay = SAC(args), MemoryBuffer(args)
    s = env.reset()
    for i in range(4):
        previous = env.agent.P_FCS
        a = sac.select_action(s)
        next_s, r, done, info = env.step(a, i)
        assert info['fc_requested_kw'] == pytest.approx(previous + 10 * float(a[0]), abs=1e-5)
        assert info['fc_applied_kw'] == pytest.approx(info['fc_requested_kw'], abs=1e-5)
        replay.store(s, a, r, next_s, done or i == 3)
        np.testing.assert_array_equal(replay._action[i], a)
        s = next_s
    assert replay._action[0, 0] >= 0
    transition = replay.random_sample()
    before = [p.detach().clone() for p in sac.actor.parameters()]
    targets = []
    original = sac.actor.entropy_target
    def capture(state, base):
        result = original(state, base)
        targets.append(result)
        return result
    monkeypatch.setattr(sac.actor, 'entropy_target', capture)
    losses = sac.learn(transition)
    assert np.isfinite(losses).all()
    assert len(targets) == 1 and torch.isfinite(targets[0]).all()
    assert any(not torch.equal(old, new) for old, new in zip(before, sac.actor.parameters()))
