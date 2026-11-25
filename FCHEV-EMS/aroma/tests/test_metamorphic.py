import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



# append to tests/test_metamorphic.py
from types import SimpleNamespace


def _fake_args():
    return SimpleNamespace(
        w_soc=300.0, w_h2=10.0, w_fc=4.275e6, w_batt=1.116e6,
        soc_target=0.6, soc_low=0.4, soc_high=0.8,
        reward_scale=1.0, eq_h2_batt_coef=0.0164, time_step=1.0,
    )


# append to tests/test_metamorphic.py


def _good_reward(self):
    # monotone-decreasing in every MR cause; used as the "correct" reward
    return -(self.w_h2 * self.h2_fcs
             + self.w_soc * (self.SOC - self.SOC_target) ** 2
             + self.w_fc * self.dSOH_FCS
             + self.w_batt * self.dSOH_batt)


# append to tests/test_metamorphic.py


def _bad_h2_reward(self):
    # WRONG: reward INCREASES with h2_fcs -> must be falsified
    return +self.w_h2 * self.h2_fcs


def _raises_high_h2_reward(self):
    # reward is fine at low h2 but CRASHES in the violating region
    if self.h2_fcs > 0.5:
        raise ValueError("reward blew up")
    return -self.w_h2 * self.h2_fcs


def _inf_high_h2_reward(self):
    # reward explodes upward to +inf in the violating region (reward hacking).
    # NOTE: kept as a guard (finite source, +inf followup) rather than a global
    # `h2**2 * 1e600` so the SOURCE reward stays finite -- an everywhere-inf
    # reward makes every pair's baseline non-finite, which norm_g must skip, so
    # it could never be falsified by this pairwise relation. This form exercises
    # the intended finite-source / +inf-followup falsification path.
    if self.h2_fcs > 0.5:
        return float("inf")
    return -self.w_h2 * self.h2_fcs


# append to tests/test_metamorphic.py


# append to tests/test_metamorphic.py


def _nan_reward(self):
    return float("nan")


# append to tests/test_metamorphic.py


# append to tests/test_metamorphic.py
def test_mt_args_registered(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog"])
    from arguments_ldri import get_ldri_args
    a = get_ldri_args()
    for name in ("aligned_mt_sobol", "aligned_mt_de_maxiter", "aligned_mt_eps_up",
                 "aligned_mt_min_sensitivity_h2", "aligned_mt_min_sensitivity_batt",
                 "aligned_mt_min_sensitivity_fcs", "aligned_mt_envelope_quantile"):
        assert hasattr(a, name), name


# append to tests/test_metamorphic.py
def _soc_quadratic_reward(self):
    # legitimate smooth in-bounds-keeping reward; must NOT be falsified by MR-SOC
    return -self.w_soc * (self.SOC - self.SOC_target) ** 2


def _soc_indifferent_reward(self):
    # ignores SOC entirely -> OOB scores same as target -> MUST be falsified
    return -self.w_h2 * self.h2_fcs
