import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# These tests only exercise AST fingerprinting. Some local dev environments do
# not have the numeric stack needed by the full training pipeline imports.
try:
    import numpy  # noqa: F401
except ImportError:
    sys.modules["numpy"] = types.ModuleType("numpy")

try:
    import scipy.io  # noqa: F401
except ImportError:
    scipy_stub = types.ModuleType("scipy")
    scipy_io_stub = types.ModuleType("scipy.io")
    scipy_stub.io = scipy_io_stub
    sys.modules["scipy"] = scipy_stub
    sys.modules["scipy.io"] = scipy_io_stub

import ems_tools


BASE_REWARD = """
def get_reward(self):
    \"\"\"iter_001 trace text\"\"\"
    k_oob = 3.75
    dist_low = max(0.0, self.soc_bounds[0] - self.SOC)
    soc_cost = self.w_soc * (self.SOC - self.SOC_target) ** 2
    soc_cost += self.w_soc * k_oob * dist_low ** 2
    h2_cost = self.w_h2 * self.h2_fcs
    reward = -(soc_cost + h2_cost)
    self.info.update({"EMS_reward": reward})
    return reward
"""


DOCSTRING_AND_COMMENT_ONLY = """
def get_reward(self):
    \"\"\"iter_002 trace text; no executable reward change\"\"\"
    k_oob = 3.75
    dist_low = max(0.0, self.soc_bounds[0] - self.SOC)
    # comment changed, but reward arithmetic is identical
    soc_cost = self.w_soc * (self.SOC - self.SOC_target) ** 2
    soc_cost += self.w_soc * k_oob * dist_low ** 2
    h2_cost = self.w_h2 * self.h2_fcs
    reward = -(soc_cost + h2_cost)
    self.info.update({"EMS_reward": reward})
    return reward
"""


EXECUTABLE_CHANGE = """
def get_reward(self):
    \"\"\"iter_002 trace text\"\"\"
    k_oob = 4.0
    dist_low = max(0.0, self.soc_bounds[0] - self.SOC)
    soc_cost = self.w_soc * (self.SOC - self.SOC_target) ** 2
    soc_cost += self.w_soc * k_oob * dist_low ** 2
    h2_cost = self.w_h2 * self.h2_fcs
    reward = -(soc_cost + h2_cost)
    self.info.update({"EMS_reward": reward})
    return reward
"""


LOGGING_ONLY_CHANGE = """
def get_reward(self):
    k_oob = 3.75
    dist_low = max(0.0, self.soc_bounds[0] - self.SOC)
    soc_cost = self.w_soc * (self.SOC - self.SOC_target) ** 2
    soc_cost += self.w_soc * k_oob * dist_low ** 2
    h2_cost = self.w_h2 * self.h2_fcs
    reward = -(soc_cost + h2_cost)
    self.info.update({"EMS_reward": reward, "trace_only": 1.0})
    return reward
"""


UNUSED_DEAD_CODE_CHANGE = """
def get_reward(self):
    k_oob = 3.75
    unused_h2_probe = self.w_h2 * self.h2_fcs * 99.0
    dist_low = max(0.0, self.soc_bounds[0] - self.SOC)
    soc_cost = self.w_soc * (self.SOC - self.SOC_target) ** 2
    soc_cost += self.w_soc * k_oob * dist_low ** 2
    h2_cost = self.w_h2 * self.h2_fcs
    reward = -(soc_cost + h2_cost)
    self.info.update({"EMS_reward": reward})
    return reward
"""


def test_diff_tool_fingerprint_matches_signature_semantics():
    assert (
        ems_tools._executable_method_fingerprint(BASE_REWARD)
        == ems_tools._executable_method_fingerprint(DOCSTRING_AND_COMMENT_ONLY)
    )
    assert (
        ems_tools._executable_method_fingerprint(BASE_REWARD)
        != ems_tools._executable_method_fingerprint(EXECUTABLE_CHANGE)
    )
