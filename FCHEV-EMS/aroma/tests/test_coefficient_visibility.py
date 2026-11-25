"""계수 가시성 + 동작 델타 복구 (2026-09-16).

20260916_074239 run iter_002 진단: 21회 시도 내내
  * `key_weight_changes_attempt_*.json` 이 전부 `{"changes": []}` — 추출기가
    `w_soc_eff = self.w_soc * 0.75` / `float(self.w_h2)` 형태를 못 읽어 중복 탐지·레버 기록·
    스케일 검사가 모두 눈을 감았고 같은 후보가 반복 제출됐다.
  * `semantic_delta_*.json` 이 전부 `{"basis": "signature_fallback", "error": "name 'np' is not defined"}`
    — probe 실행 네임스페이스에 numpy 가 없어 baseline 계열(np.where/np.abs) reward 를 실행할 수
    없었고, "이 후보가 실제로 동작을 바꿨는가" 검증이 통째로 무력화됐다.

요구사항: 두 오류를 없애되 **w_soc 조정은 계속 허용**한다 (OOB 배수는 상한 대상이 아니다).

Run: python3 -m pytest tests/test_coefficient_visibility.py
"""
import glob
import json
import os
import sys
from pathlib import Path


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompt_builder import extract_method_source

_LDRI = Path(__file__).resolve().parents[1]
_RUNS = _LDRI.parent / "ldri_runs"

BASELINE = extract_method_source(str(_LDRI / "agentEMS_val_base.py"),
                                 class_name="EMS", method_name="get_reward")

# 20260916_074239 run iter_002 의 실제 후보 21개 (있을 때만 실데이터 테스트)
_CANDS = sorted(glob.glob(str(_RUNS / "20260916_074239_*" / "iter_002"
                              / "candidate_get_reward_attempt_*.py")))

# iter_002 attempt 21 형태 — 곱셈식으로 w_soc 를 25% 줄이고 OOB 배수는 10x 유지
ATT21 = BASELINE.replace(
    "    w_soc = np.where((soc >= soc_high) | (soc <= soc_low), self.w_soc * 10, self.w_soc)\n",
    "    w_soc_eff = self.w_soc * 0.75\n"
    "    w_soc = np.where((soc >= soc_high) | (soc <= soc_low), w_soc_eff * 10, w_soc_eff)\n",
)
# iter_001 형태 — w_h2 를 리터럴로 하드코딩
HARDCODED_H2 = BASELINE.replace("    h2_cost = self.w_h2 * h2_fcs\n",
                                "    w_h2_eff = 11.5\n    h2_cost = w_h2_eff * h2_fcs\n")


def test_fixtures_differ_from_the_baseline():
    assert ATT21 != BASELINE and HARDCODED_H2 != BASELINE


# ── 1. 계수 추출: 곱셈식 w_soc 조정을 본다 ──────────────────────────────────


# 실제 20260916_074239 iter_002 후보들이 쓴 나머지 두 철자 — 둘 다 읽혀야 한다

IF_ELSE = (
    "def get_reward(self):\n"
    "    soc = float(self.SOC)\n"
    "    soc_low, soc_high = self.soc_bounds\n"
    "    soc_err = (np.abs(soc - self.SOC_target)) ** 2\n"
    "    k_inbounds = 0.75\n"
    "    in_bounds = (soc_low < soc < soc_high)\n"
    "    if in_bounds:\n"
    "        w_soc_eff = self.w_soc * k_inbounds\n"
    "    else:\n"
    "        w_soc_eff = self.w_soc * 10.0\n"
    "    soc_cost = w_soc_eff * soc_err\n"
    "    return -(soc_cost + self.w_h2 * self.h2_fcs)\n"
)
ADDITIVE_OOB = (
    "def get_reward(self):\n"
    "    soc = float(self.SOC)\n"
    "    soc_low, soc_high = self.soc_bounds\n"
    "    soc_err = (soc - float(self.SOC_target)) ** 2\n"
    "    w_soc_eff = self.w_soc * 0.75\n"
    "    oob = float((soc >= soc_high) or (soc <= soc_low))\n"
    "    soc_cost = w_soc_eff * soc_err + oob * self.w_soc * 10.0 * soc_err\n"
    "    return -(soc_cost + self.w_h2 * self.h2_fcs)\n"
)


GATE_BLEND = (
    "def get_reward(self):\n"
    "    soc = float(self.SOC)\n"
    "    soc_low, soc_high = self.soc_bounds\n"
    "    soc_err = (soc - float(self.SOC_target)) ** 2\n"
    "    w_soc_eff = self.w_soc * 0.70\n"
    "    oob = float((soc >= soc_high) or (soc <= soc_low))\n"
    "    w_soc_applied = w_soc_eff * (1.0 + 9.0 * oob)   # 1x in-bounds, 10x OOB\n"
    "    soc_cost = w_soc_applied * soc_err\n"
    "    return -(soc_cost + self.w_h2 * self.h2_fcs)\n"
)


# ── 2. 스케일 검사: 조정은 허용, 과도한 증폭만 차단 ────────────────────────


# ── 3. key_weight_changes: 무엇이 바뀌었는지 기록된다 ───────────────────────


# ── 4. 동작 델타: numpy reward 를 실제로 실행한다 ───────────────────────────


# ── 5. 실데이터: 20260916_074239 run 의 21개 후보 ──────────────────────────
