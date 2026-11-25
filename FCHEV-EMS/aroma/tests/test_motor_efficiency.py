"""Regression and energy-balance checks for the shared motor plant."""

import math
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from FCHEV_SOH import FCHEV_SOH


@pytest.fixture
def plant():
    return FCHEV_SOH()


@pytest.mark.parametrize('acceleration', [0.5, -0.5])
def test_road_load_includes_driveline_and_motor_losses_once(plant, acceleration):
    speed = 15.0
    road_force = 1900 * acceleration + 1900 * 9.81 * .012 + .5 * 1.226 * 2.5 * .32 * speed**2
    wheel_power = road_force * speed
    torque, rpm, shaft_request = plant.T_W_axle(speed, acceleration)
    tm, wm, efficiency, electrical = plant.run_motor(torque, rpm, shaft_request)
    assert tm == pytest.approx(torque)  # operating point is within torque limits
    assert shaft_request == pytest.approx(tm * wm * 2 * math.pi / 60)
    if wheel_power > 0:
        assert shaft_request == pytest.approx(wheel_power / .98)
        assert electrical == pytest.approx(wheel_power / (.98 * efficiency))
        assert electrical > shaft_request > wheel_power
    else:
        assert shaft_request == pytest.approx(wheel_power * .95)
        assert electrical == pytest.approx(wheel_power * .95 * efficiency)
        assert wheel_power < shaft_request < electrical < 0


def test_standstill_has_finite_torque_and_zero_power(plant):
    torque, rpm, shaft_request = plant.T_W_axle(0., 0.5)
    assert np.isfinite(torque) and torque > 0
    assert rpm == shaft_request == 0
    assert plant.run_motor(torque, rpm, shaft_request)[3] == 0


def test_la92_regen_does_not_extrapolate_negative_torque(plant):
    torque, rpm = -292.28783, 2840.4295
    mechanical = torque * rpm * 2 * math.pi / 60
    tm, wm, efficiency, electrical = plant.run_motor(torque, rpm, mechanical)
    assert tm == torque and wm == rpm
    assert efficiency == pytest.approx(.925766314, abs=1e-7)
    assert electrical / 1000 == pytest.approx(-80.486815, abs=1e-4)
    assert mechanical < electrical < 0


@pytest.mark.parametrize('rpm', [-6000., 0., 3000., 6000.])
def test_lookup_uses_torque_magnitude_and_retains_speed(plant, rpm):
    expected = float(plant._mot_eff_interp((100., rpm)))
    assert plant.mot_eff_map(rpm, -100.) == expected
    assert plant.mot_eff_map(rpm, 100.) == expected


@pytest.mark.parametrize('torque,rpm', [(100., 3000.), (-100., 3000.),
                                        (0., 3000.), (100., 0.), (-100., 0.),
                                        (1000., 6000.), (-1000., 6000.)])
def test_signed_power_has_nonnegative_motor_loss_after_torque_limits(plant, torque, rpm):
    # A conflicting P_axle must not invert conversion at the actual shaft.
    tm, wm, efficiency, electrical = plant.run_motor(torque, rpm, -torque)
    mechanical = tm * wm * 2 * math.pi / 60
    assert 0 < efficiency <= 1
    assert electrical - mechanical >= 0
    if mechanical < 0:
        assert mechanical <= electrical < 0
    elif mechanical > 0:
        assert electrical == pytest.approx(mechanical / efficiency)
    else:
        assert electrical == 0


@pytest.mark.parametrize('rpm,torque', [(14001., 100.), (-14001., 100.),
                                       (3000., 396.), (3000., -396.),
                                       (np.nan, 100.), (3000., np.inf)])
def test_lookup_rejects_invalid_inputs_instead_of_clipping(plant, rpm, torque):
    with pytest.raises(ValueError):
        plant.mot_eff_map(rpm, torque)


@pytest.mark.parametrize('efficiency', [0., -.1, 1.01, np.nan, np.inf])
def test_invalid_interpolated_efficiency_is_rejected(plant, monkeypatch, efficiency):
    monkeypatch.setattr(plant, '_mot_eff_interp', lambda point: efficiency)
    with pytest.raises(ValueError, match='efficiency'):
        plant.run_motor(-100., 3000., -1.)


def test_invalid_source_map_is_rejected(monkeypatch):
    import FCHEV_SOH as module

    original = module.scio.loadmat

    def loadmat(path):
        data = original(path)
        if str(path).endswith('/mot_eff_nexo.mat'):
            data['mot_eff_nexo'][0, 0] = 1.1
        return data

    monkeypatch.setattr(module.scio, 'loadmat', loadmat)
    with pytest.raises(ValueError, match='efficiency map'):
        FCHEV_SOH()
