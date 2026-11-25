"""Build process/trajectory/preference feedback text from FCEV training artifacts.

1. train_log.log 파싱
2. episode 단위 요약 구조화
3. process / preference / trajectory 피드백 생성
4. 최종 feedback 생성
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import math
import json
import sys
import re
from typing import Dict, Iterable, List, Optional, Tuple

_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
    sys.path.append(_PROJECT_ROOT)
from common.paper_fuel_economy import PAPER_FUEL_BASIS as DETERMINISTIC_FUEL_BASIS

# train log 각 줄 형식을 인식하기 위한 parser
_FLOAT = r"[+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?"

_RE_TRAVEL = re.compile(
    rf"^epi\s+(?P<ep>\d+):\s+travel\s+(?P<travel>{_FLOAT})km,\s+SOC\s+(?P<SOC>{_FLOAT}),\s+"
    rf"(?:(?:FCS-SOH\s+(?P<FCS_SOH>{_FLOAT}),\s+Bat-SOH\s+(?P<BAT_SOH>{_FLOAT}))|"
    rf"(?:Bat-SOH\s+(?P<BAT_SOH_ALT>{_FLOAT}),\s+FCS-SOH\s+(?P<FCS_SOH_ALT>{_FLOAT})))"
)
_RE_OBJ = re.compile(
    rf"^epi\s+(?P<ep>\d+):\s+H2_100km\s+(?P<H2_100>{_FLOAT})g"
    rf"(?:,\s+H2eq_100km\s+(?P<H2EQ_100>{_FLOAT})g\s+\(batt\s+(?P<H2_BATT_100>{_FLOAT})g\))?"
    rf"(?:,\s+g/km\s+{_FLOAT})?"
    rf"(?:,\s+MPG\s+(?P<MPG>{_FLOAT}))?"
    rf"(?:,\s+fuel_eq\s+(?P<FUEL_EQ_GAL>{_FLOAT})\s+USgal)?"
    rf",\s+objective_100km\s+(?P<objective_100>{_FLOAT})"
)
_RE_SOC = re.compile(
    rf"^epi\s+(?P<ep>\d+):\s+SOC\[min/mean/max\]=(?P<SOC_MIN>{_FLOAT})/(?P<SOC_MEAN>{_FLOAT})/(?P<SOC_MAX>{_FLOAT}),\s+in_bounds_rate=(?P<in_bounds>{_FLOAT})%,\s+len=(?P<len>\d+)"
)
_RE_MEAN_COST = re.compile(
    rf"^epi\s+(?P<ep>\d+):\s+mean_cost\s+soc\s+(?P<soc_cost>{_FLOAT}),\s+h2(?:eq)?\s+(?P<h2_cost>{_FLOAT}),\s+fcs\s+(?P<fcs_cost>{_FLOAT}),\s+batt\s+(?P<batt_cost>{_FLOAT}),\s+obj\s+(?P<objective_cost>{_FLOAT})"
)
_RE_POWER = re.compile(
    rf"^epi\s+(?P<ep>\d+):\s+P_fc\s+min/mean/max\s+(?P<pfc_min>{_FLOAT})/(?P<pfc_mean>{_FLOAT})/(?P<pfc_max>{_FLOAT})\s+kW,\s+P_batt_req\s+min/mean/max\s+(?P<pbatt_min>{_FLOAT})/(?P<pbatt_mean>{_FLOAT})/(?P<pbatt_max>{_FLOAT})\s+kW,\s+fce_eff\s+mean\s+(?P<fce_eff>{_FLOAT}),\s+fc_on\s+(?P<fc_on>{_FLOAT})%"
)
_RE_DEGR_CAUSE = re.compile(
    rf"^epi\s+(?P<ep>\d+):\s+fc_degr_causes\s+start_stop\s+(?P<dss>\d+),\s+low_power\s+(?P<dlow>\d+),"
    rf"\s+high_power\s+(?P<dhigh>\d+),\s+load_change\s+(?P<dlc>\d+)"
)
_RE_LOSS = re.compile(
    rf"^epi\s+(?P<ep>\d+):\s+ep_cumulative_r\s+(?P<ep_r>{_FLOAT}),\s+c-loss1\s+(?P<c1>{_FLOAT}),\s+c-loss2\s+(?P<c2>{_FLOAT}),\s+a-loss\s+(?P<a>{_FLOAT}),\s+en-loss\s+(?P<en>{_FLOAT}),\s+alpha\s+(?P<alpha>{_FLOAT})"
)
_RE_LR = re.compile(
    rf"^epi\s+(?P<ep>\d+):\s+lr_critic\s+(?P<lr_critic>{_FLOAT}),\s+lr_actor\s+(?P<lr_actor>{_FLOAT}),\s+lr_alpha\s+(?P<lr_alpha>{_FLOAT})"
)
_RE_BEST = re.compile(
    rf"^best checkpoint updated:\s+ep\s+(?P<ep>\d+),\s+reward\s+(?P<best_reward>{_FLOAT})"
)
# Deterministic eval rollout lines: "epi N [eval]: ..." emitted by the runner.
_RE_EVAL_MAIN = re.compile(
    rf"^epi\s+(?P<ep>\d+)\s+\[eval\]:\s+eval_r\s+(?P<eval_r>{_FLOAT}),\s+H2_100km\s+(?P<eval_h2>{_FLOAT})g,"
    rf"\s+H2eq_100km\s+{_FLOAT}g\s+\(batt\s+{_FLOAT}g\),\s+g/km\s+{_FLOAT},\s+objective_100km\s+(?P<eval_obj>{_FLOAT})"
)
_RE_EVAL_SOC = re.compile(
    rf"^epi\s+(?P<ep>\d+)\s+\[eval\]:\s+SOC\[min/mean/max\]=(?P<smin>{_FLOAT})/(?P<smean>{_FLOAT})/(?P<smax>{_FLOAT}),"
    rf"\s+final\s+(?P<sfinal>{_FLOAT}),\s+in_bounds_rate=(?P<inb>{_FLOAT})%"
)
_RE_EVAL_POWER = re.compile(
    rf"^epi\s+(?P<ep>\d+)\s+\[eval\]:\s+P_fc.*fce_eff\s+mean\s+(?P<eff>{_FLOAT}),\s+fc_on\s+(?P<on>{_FLOAT})%"
)
_RE_EVAL_FUEL = re.compile(
    rf"^epi\s+(?P<ep>\d+)\s+\[eval\]:\s+fuel H2_100km (?P<h2>{_FLOAT})g, "
    rf"H2eq_corr_100km (?P<corr>{_FLOAT})g, travel (?P<travel>{_FLOAT})km, "
    rf"SOC_start (?P<start>{_FLOAT}), SOC_final (?P<end>{_FLOAT}), fce_eff (?P<eff>{_FLOAT})"
)

_RE_EVAL_PAPER_FUEL = re.compile(r"^epi\s+(?P<ep>\d+)\s+\[eval\]:\s+paper_fuel (?P<row>\{.*\})$")


@dataclass
class EpisodeSummary:
    episode: int
    order: int
    raw_lines: List[str] = field(default_factory=list)

    travel_km: Optional[float] = None
    soc_end: Optional[float] = None
    fcs_soh: Optional[float] = None
    batt_soh: Optional[float] = None

    h2_100km: Optional[float] = None
    h2eq_100km: Optional[float] = None
    # dSOC 보정 등가수소: 배터리 순방전/순충전을 상쇄한 '진짜' 연비 지표
    h2eq_corr_100km: Optional[float] = None
    eval_h2eq_corr_100km: Optional[float] = None
    h2_batt_100km: Optional[float] = None
    mpg: Optional[float] = None
    fuel_eq_gal: Optional[float] = None
    objective_100km: Optional[float] = None

    soc_min: Optional[float] = None
    soc_mean: Optional[float] = None
    soc_max: Optional[float] = None
    in_bounds_rate: Optional[float] = None
    ep_len: Optional[int] = None

    mean_soc_cost: Optional[float] = None
    mean_h2_cost: Optional[float] = None
    mean_fcs_cost: Optional[float] = None
    mean_batt_cost: Optional[float] = None
    mean_objective_cost: Optional[float] = None

    pfc_min: Optional[float] = None
    pfc_mean: Optional[float] = None
    pfc_max: Optional[float] = None
    pbatt_min: Optional[float] = None
    pbatt_mean: Optional[float] = None
    pbatt_max: Optional[float] = None
    fce_eff_mean: Optional[float] = None
    fc_on_pct: Optional[float] = None
    # FC 열화 원인별 발생 횟수 (dSOH_FCS 의 분해)
    d_start_stop: Optional[int] = None
    d_low_power: Optional[int] = None
    d_high_power: Optional[int] = None
    d_load_change: Optional[int] = None

    ep_cumulative_r: Optional[float] = None
    c_loss1: Optional[float] = None
    c_loss2: Optional[float] = None
    a_loss: Optional[float] = None
    en_loss: Optional[float] = None
    alpha: Optional[float] = None

    lr_critic: Optional[float] = None
    lr_actor: Optional[float] = None
    lr_alpha: Optional[float] = None

    best_checkpoint_reward: Optional[float] = None

    # deterministic eval rollout (mean action) -- from the runner "[eval]" log lines
    eval_r: Optional[float] = None
    eval_h2_100km: Optional[float] = None
    eval_objective_100km: Optional[float] = None
    eval_soc_min: Optional[float] = None
    eval_soc_max: Optional[float] = None
    eval_soc_final: Optional[float] = None
    eval_in_bounds_rate: Optional[float] = None
    eval_travel_km: Optional[float] = None
    eval_soc_start: Optional[float] = None
    eval_fce_eff_mean: Optional[float] = None
    eval_fc_on_pct: Optional[float] = None
    eval_paper_fuel: Optional[dict] = None


class LogParseError(RuntimeError):
    """Raised when log file cannot be parsed."""


def _new_episode(ep: int, order: int, line: str) -> EpisodeSummary:
    return EpisodeSummary(episode=ep, order=order, raw_lines=[line])


def parse_train_log(log_path: str | Path) -> List[EpisodeSummary]:
    """Parse train_log.log into episode summaries in appearance order."""
    path = Path(log_path)
    if not path.exists():
        raise LogParseError(f"log file not found: {path}")

    episodes: List[EpisodeSummary] = []
    latest_by_ep: Dict[int, EpisodeSummary] = {}

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            # line 단위로 읽음
            line = raw.strip()
            if not line:
                continue

            m = _RE_TRAVEL.match(line)
            if m:
                ep = int(m.group("ep"))
                # _RE_TRAVEL 줄이 나오면 새 episode 시작
                rec = _new_episode(ep, len(episodes), line)
                rec.travel_km = float(m.group("travel"))
                rec.soc_end = float(m.group("SOC"))
                fcs_soh = m.group("FCS_SOH") or m.group("FCS_SOH_ALT")
                batt_soh = m.group("BAT_SOH") or m.group("BAT_SOH_ALT")
                rec.fcs_soh = float(fcs_soh) if fcs_soh is not None else None
                rec.batt_soh = float(batt_soh) if batt_soh is not None else None
                episodes.append(rec)
                latest_by_ep[ep] = rec
                continue

            matched = False
            for regex, handler in (
                (_RE_OBJ, _handle_obj),
                (_RE_SOC, _handle_soc),
                (_RE_MEAN_COST, _handle_mean_cost),
                (_RE_POWER, _handle_power),
                (_RE_DEGR_CAUSE, _handle_degr_cause),
                (_RE_LOSS, _handle_loss),
                (_RE_LR, _handle_lr),
                (_RE_BEST, _handle_best),
                (_RE_EVAL_MAIN, _handle_eval_main),
                (_RE_EVAL_SOC, _handle_eval_soc),
                (_RE_EVAL_POWER, _handle_eval_power),
                (_RE_EVAL_FUEL, _handle_eval_fuel),
                (_RE_EVAL_PAPER_FUEL, _handle_eval_paper_fuel),
            ):
                m = regex.match(line)
                if m:
                    ep = int(m.group("ep"))
                    rec = latest_by_ep.get(ep)
                    if rec is None:
                        rec = _new_episode(ep, len(episodes), line)
                        episodes.append(rec)
                        latest_by_ep[ep] = rec
                    else:
                        rec.raw_lines.append(line)
                    handler(rec, m)
                    matched = True
                    break

            if matched:
                continue

    if not episodes:
        raise LogParseError(f"no episode summaries found in log: {path}")

    return episodes


def _handle_obj(rec: EpisodeSummary, m: re.Match[str]) -> None:
    rec.h2_100km = float(m.group("H2_100"))
    h2eq = m.groupdict().get("H2EQ_100")
    h2_batt = m.groupdict().get("H2_BATT_100")
    mpg = m.groupdict().get("MPG")
    fuel_eq = m.groupdict().get("FUEL_EQ_GAL")
    rec.h2eq_100km = float(h2eq) if h2eq is not None else None
    rec.h2_batt_100km = float(h2_batt) if h2_batt is not None else None
    rec.mpg = float(mpg) if mpg is not None else None
    rec.fuel_eq_gal = float(fuel_eq) if fuel_eq is not None else None
    rec.objective_100km = float(m.group("objective_100"))


def _handle_soc(rec: EpisodeSummary, m: re.Match[str]) -> None:
    rec.soc_min = float(m.group("SOC_MIN"))
    rec.soc_mean = float(m.group("SOC_MEAN"))
    rec.soc_max = float(m.group("SOC_MAX"))
    rec.in_bounds_rate = float(m.group("in_bounds"))
    rec.ep_len = int(m.group("len"))


def _handle_mean_cost(rec: EpisodeSummary, m: re.Match[str]) -> None:
    rec.mean_soc_cost = float(m.group("soc_cost"))
    rec.mean_h2_cost = float(m.group("h2_cost"))
    rec.mean_fcs_cost = float(m.group("fcs_cost"))
    rec.mean_batt_cost = float(m.group("batt_cost"))
    rec.mean_objective_cost = float(m.group("objective_cost"))


def _handle_power(rec: EpisodeSummary, m: re.Match[str]) -> None:
    rec.pfc_min = float(m.group("pfc_min"))
    rec.pfc_mean = float(m.group("pfc_mean"))
    rec.pfc_max = float(m.group("pfc_max"))
    rec.pbatt_min = float(m.group("pbatt_min"))
    rec.pbatt_mean = float(m.group("pbatt_mean"))
    rec.pbatt_max = float(m.group("pbatt_max"))
    rec.fce_eff_mean = float(m.group("fce_eff"))
    rec.fc_on_pct = float(m.group("fc_on"))


def _handle_degr_cause(rec: EpisodeSummary, m: re.Match[str]) -> None:
    rec.d_start_stop = int(m.group("dss"))
    rec.d_low_power = int(m.group("dlow"))
    rec.d_high_power = int(m.group("dhigh"))
    rec.d_load_change = int(m.group("dlc"))


def _handle_loss(rec: EpisodeSummary, m: re.Match[str]) -> None:
    rec.ep_cumulative_r = float(m.group("ep_r"))
    rec.c_loss1 = float(m.group("c1"))
    rec.c_loss2 = float(m.group("c2"))
    rec.a_loss = float(m.group("a"))
    rec.en_loss = float(m.group("en"))
    rec.alpha = float(m.group("alpha"))


def _handle_lr(rec: EpisodeSummary, m: re.Match[str]) -> None:
    rec.lr_critic = float(m.group("lr_critic"))
    rec.lr_actor = float(m.group("lr_actor"))
    rec.lr_alpha = float(m.group("lr_alpha"))


def _handle_best(rec: EpisodeSummary, m: re.Match[str]) -> None:
    rec.best_checkpoint_reward = float(m.group("best_reward"))


def _handle_eval_main(rec: EpisodeSummary, m: re.Match[str]) -> None:
    rec.eval_r = float(m.group("eval_r"))
    rec.eval_h2_100km = float(m.group("eval_h2"))
    rec.eval_objective_100km = float(m.group("eval_obj"))


def _handle_eval_soc(rec: EpisodeSummary, m: re.Match[str]) -> None:
    rec.eval_soc_min = float(m.group("smin"))
    rec.eval_soc_max = float(m.group("smax"))
    rec.eval_soc_final = float(m.group("sfinal"))
    rec.eval_in_bounds_rate = float(m.group("inb"))


def _handle_eval_power(rec: EpisodeSummary, m: re.Match[str]) -> None:
    rec.eval_fce_eff_mean = float(m.group("eff"))
    rec.eval_fc_on_pct = float(m.group("on"))


def _handle_eval_fuel(rec: EpisodeSummary, m: re.Match[str]) -> None:
    rec.eval_h2_100km = float(m.group("h2"))
    rec.eval_h2eq_corr_100km = float(m.group("corr"))
    rec.eval_travel_km = float(m.group("travel"))
    rec.eval_soc_start = float(m.group("start"))
    rec.eval_soc_final = float(m.group("end"))
    rec.eval_fce_eff_mean = float(m.group("eff"))

def _handle_eval_paper_fuel(rec: EpisodeSummary, m: re.Match[str]) -> None:
    rec.eval_paper_fuel = json.loads(m.group("row"))


def _compute_trend_per10(vals: List[float]) -> Optional[float]:
    """Approximate slope per 10 episodes via first-half vs second-half mean comparison."""
    n = len(vals)
    if n < 4:
        return None
    half = n // 2
    first_mean = sum(vals[:half]) / half
    second_mean = sum(vals[half:]) / (n - half)
    return (second_mean - first_mean) / (n / 2) * 10


# 집계 통계(mean/best/trend) + 최근 raw 로그 5개를 보여주는 text를 만듬
def format_process_feedback(episodes: List[EpisodeSummary], num_episodes: int = 10) -> str:
    """Format aggregate statistics with trend analysis and a short raw tail."""
    window = episodes[-max(1, num_episodes):]
    n_window = len(window)
    ep_ids = [ep.episode for ep in window]
    raw_tail_count = min(5, n_window)

    def _row(
        label: str,
        attr: str,
        higher_is_better: Optional[bool],
        unit: str = "",
        fmt: str = ".4g",
    ) -> Optional[str]:
        vals = [v for v in (getattr(ep, attr, None) for ep in window) if v is not None]
        if not vals:
            return None
        n = len(vals)
        mean_v = sum(vals) / n
        best_v = max(vals) if higher_is_better else min(vals)
        slope = _compute_trend_per10(vals)

        mean_str = f"{format(mean_v, fmt)}{unit}"
        best_str = f"{format(best_v, fmt)}{unit}"

        if slope is None:
            trend_str = "n/a"
        elif higher_is_better is None:
            sign = "+" if slope > 0 else ""
            trend_str = f"{sign}{format(slope, fmt)}{unit}/10ep"
        else:
            sign = "+" if slope > 0 else ""
            slope_str = f"{sign}{format(slope, fmt)}{unit}/10ep"
            rel_pct = abs(slope) / (abs(mean_v) + 1e-12) * 100
            if rel_pct < 0.5:
                direction = "→ stable"
            elif (higher_is_better and slope > 0) or (not higher_is_better and slope < 0):
                direction = "↓ improving" if not higher_is_better else "↑ improving"
            else:
                direction = "↑ worsening" if not higher_is_better else "↓ worsening"
            trend_str = f"{slope_str} {direction}"

        return f"  {label:<24s}: mean={mean_str:<13s} best={best_str:<13s} trend={trend_str}"

    stat_rows: List[str] = []
    for row in [
        _row("H2_100km",           "h2_100km",            higher_is_better=False, unit="g",  fmt=".1f"),
        _row("in_bounds_rate",     "in_bounds_rate",      higher_is_better=True,  unit="%",  fmt=".1f"),
        _row("mean_objective_cost","mean_objective_cost", higher_is_better=False,            fmt=".4f"),
        _row("mean_h2_cost",       "mean_h2_cost",        higher_is_better=False,            fmt=".4f"),
        _row("mean_soc_cost",      "mean_soc_cost",       higher_is_better=False,            fmt=".4f"),
        _row("mean_fcs_cost",      "mean_fcs_cost",       higher_is_better=False,            fmt=".5f"),
        _row("mean_batt_cost",     "mean_batt_cost",      higher_is_better=False,            fmt=".5f"),
        _row("fce_eff",            "fce_eff_mean",        higher_is_better=True,             fmt=".4f"),
        _row("ep_cumulative_r",    "ep_cumulative_r",     higher_is_better=True,             fmt=".2f"),
        _row("alpha",              "alpha",               higher_is_better=None,             fmt=".4f"),
    ]:
        if row:
            stat_rows.append(row)

    raw_tail = window[-raw_tail_count:]
    raw_lines: List[str] = [
        f"[Recent {raw_tail_count} episode raw logs]",
        f"Collected episodes: {[ep.episode for ep in raw_tail]}",
    ]
    for rec in raw_tail:
        raw_lines.append("")
        raw_lines.append(f"[Episode {rec.episode}]")
        if rec.raw_lines:
            raw_lines.extend(rec.raw_lines)
        else:
            raw_lines.append(f"epi {rec.episode}: (no parsed lines)")

    return "\n".join([
        f"[Training trend summary — last {n_window} episodes (ep {ep_ids[0]}..{ep_ids[-1]})]",
        "Key metrics (mean, best-in-window, trend per 10 episodes):",
        *stat_rows,
        "",
        *raw_lines,
    ])

def _episode_objective_metric(ep: EpisodeSummary) -> Optional[float]:
    if ep.mean_objective_cost is not None:
        return float(ep.mean_objective_cost)
    if ep.objective_100km is not None:
        return float(ep.objective_100km)
    return None


def _episode_h2_degradation_metric(ep: EpisodeSummary) -> Optional[float]:
    if (
        ep.mean_h2_cost is not None
        and ep.mean_fcs_cost is not None
        and ep.mean_batt_cost is not None
    ):
        return float(ep.mean_h2_cost + ep.mean_fcs_cost + ep.mean_batt_cost)
    return None


def _episode_objective_metric_label(ep: EpisodeSummary) -> str:
    if ep.mean_objective_cost is not None:
        return "mean_objective_cost"
    if ep.objective_100km is not None:
        return "objective_100km"
    return "objective_metric"


def _episode_h2_degradation_metric_label(ep: EpisodeSummary) -> str:
    if (
        ep.mean_h2_cost is not None
        and ep.mean_fcs_cost is not None
        and ep.mean_batt_cost is not None
    ):
        return "h2_plus_degradation_cost"
    return "h2_plus_degradation_metric"


def _preference_key(ep: EpisodeSummary) -> Tuple[float, float, float, int]:
    objective_metric = _episode_objective_metric(ep)
    h2_degradation_metric = _episode_h2_degradation_metric(ep)
    if objective_metric is None or h2_degradation_metric is None or ep.in_bounds_rate is None:
        raise ValueError("episode is missing objective/h2+degradation/in_bounds metrics")
    return (
        float(objective_metric),
        float(h2_degradation_metric),
        -float(ep.in_bounds_rate),
        int(ep.order),
    )


# pair 선택 기준은 reward가 아니라 task metric(SOC gate + objective/h2+degradation ordering)
def select_preference_pair(
    episodes: Iterable[EpisodeSummary],
    min_in_bounds_rate: float = 0.0,
) -> Tuple[Optional[EpisodeSummary], Optional[EpisodeSummary], str]:
    # Preferred/dispreferred are selected from task metrics rather than model reward
    # so the comparison remains meaningful for newly proposed reward functions.
    valid = [
        ep
        for ep in episodes
        if ep.in_bounds_rate is not None
        and _episode_objective_metric(ep) is not None
        and _episode_h2_degradation_metric(ep) is not None
    ]
    if len(valid) < 2:
        return None, None, "not enough episodes with objective_cost, h2+degradation cost and in_bounds_rate"

    safety_floor = max(0.0, float(min_in_bounds_rate))
    safe = [ep for ep in valid if float(ep.in_bounds_rate) >= safety_floor]
    if not safe:
        best_rate = max(float(ep.in_bounds_rate) for ep in valid)
        return (
            None,
            None,
            f"no episode satisfies in_bounds_rate >= {safety_floor:.1f}% (best={best_rate:.1f}%)",
        )

    preferred = min(safe, key=_preference_key)
    dis_pool = [
        ep
        for ep in safe
        if not (ep.episode == preferred.episode and ep.order == preferred.order)
    ]
    if not dis_pool:
        # Only one episode cleared the in_bounds floor, so there is no second
        # candidate to compare against. Return gracefully instead of calling
        # max() on the (now empty) non-preferred set, which would raise
        # ValueError: max() iterable argument is empty.
        return (
            None,
            None,
            "only one episode satisfies in_bounds_rate >= "
            f"{safety_floor:.1f}%; no dispreferred candidate available",
        )

    dispreferred = max(dis_pool, key=_preference_key)
    if preferred.episode == dispreferred.episode and preferred.order == dispreferred.order:
        return None, None, "preferred/dispreferred collapsed to same episode"

    return (
        preferred,
        dispreferred,
        (
            "ok (in_bounds_floor={:.1f}% for both preferred and dispreferred; "
            "selector=min/max(objective_metric, h2_degradation_metric, -in_bounds_rate); "
            "objective_metric=mean_objective_cost fallback objective_100km, "
            "h2_degradation_metric=h2+fcs+batt)"
        ).format(safety_floor),
    )


def _to_1d(mat: dict, key: str) -> np.ndarray:
    np, _ = _require_numeric_deps()
    if key not in mat:
        return np.array([], dtype=np.float64)
    arr = np.asarray(mat[key]).astype(np.float64).squeeze()
    if arr.ndim == 0:
        return np.array([float(arr)], dtype=np.float64)
    return arr.reshape(-1)


def _require_numeric_deps():
    try:
        import numpy as np  # type: ignore
        import scipy.io as scio  # type: ignore
    except ModuleNotFoundError as e:
        raise RuntimeError(
            "numpy/scipy are required for trajectory feedback from .mat files"
        ) from e
    return np, scio

# step-level 요약 텍스트
def _summarize_trajectory(
    episode_id: int,
    mat_path: Path,
    role: str,
    reward_value: Optional[float],
    soc_bounds: Tuple[float, float],
) -> str:
    np, scio = _require_numeric_deps()
    mat = scio.loadmat(str(mat_path))

    soc = _to_1d(mat, "SOC")
    p_fc = _to_1d(mat, "P_fc")
    p_batt = _to_1d(mat, "P_batt_req")
    obj = _to_1d(mat, "objective_cost")
    h2 = _to_1d(mat, "h2_cost")
    fcs = _to_1d(mat, "fcs_soh_cost")
    batt = _to_1d(mat, "batt_soh_cost")
    soc_cost = _to_1d(mat, "soc_cost")

    n = int(max(len(soc), len(obj), len(p_fc), len(p_batt)))
    if n == 0:
        return f"ep {episode_id} ({role}): episode_data empty"

    idxs = sorted({0, n // 2, n - 1})
    reward_txt = f"{reward_value:.3f}" if reward_value is not None else "N/A"
    lines = [f"ep {episode_id} ({role}, ep_cumulative_r={reward_txt}):"]
    for i in idxs:
        soc_v = soc[i] if i < len(soc) else np.nan
        pfc_v = p_fc[i] if i < len(p_fc) else np.nan
        pb_v = p_batt[i] if i < len(p_batt) else np.nan
        obj_v = obj[i] if i < len(obj) else np.nan
        h2_v = h2[i] if i < len(h2) else np.nan
        fcs_v = fcs[i] if i < len(fcs) else np.nan
        batt_v = batt[i] if i < len(batt) else np.nan
        socc_v = soc_cost[i] if i < len(soc_cost) else np.nan
        lines.append(
            "step {s}: SOC {soc:.4f}, P_fc {pfc:.2f} kW, P_batt_req {pb:.2f} kW, "
            "objective_cost {obj:.4f}, h2_cost {h2:.4f}, fcs_soh_cost {fcs:.4f}, "
            "batt_soh_cost {batt:.4f}, soc_cost {socc:.4f}".format(
                s=i + 1,
                soc=soc_v,
                pfc=pfc_v,
                pb=pb_v,
                obj=obj_v,
                h2=h2_v,
                fcs=fcs_v,
                batt=batt_v,
                socc=socc_v,
            )
        )

    soc_low, soc_high = soc_bounds
    boundary_hits = int(np.sum((soc < soc_low) | (soc > soc_high))) if len(soc) else 0
    switch_rate = (
        float(np.mean(np.abs(np.diff(p_fc)) > 5.0) * 100.0) if len(p_fc) > 1 else 0.0
    )
    max_obj = float(np.nanmax(obj)) if len(obj) else float("nan")

    lines.append(
        f"- key observations: soc_out_of_bounds_steps={boundary_hits}/{n}, p_fc_switch_rate(>5kW delta)={switch_rate:.1f}%, max_objective_cost={max_obj:.4f}"
    )
    return "\n".join(lines)

"""
실제 TPE gate와 동일한 preferred / dispreferred pair의
step-level 특징을 보여줌

어떤 trajectory가 task metric 기준으로 선호되어야 하는지와

그 trajectory들의 step-level 특징이 무엇인지 파악하는 데 도움을 줌
"""
def format_trajectory_feedback(
    episodes: List[EpisodeSummary],
    episode_data_dir: Optional[str | Path],
    soc_bounds: Tuple[float, float] = (0.4, 0.8),
    min_in_bounds_rate: float = 0.0,
) -> str:
    if not episode_data_dir:
        return "N/A (episode_data directory not provided for trajectory-level analysis)"

    ep_dir = Path(episode_data_dir)
    if not ep_dir.exists():
        return f"N/A (episode_data directory not found: {ep_dir})"

    try:
        _require_numeric_deps()
    except RuntimeError as e:
        return f"N/A ({e})"

    preferred, dispreferred, status = select_preference_pair(
        episodes,
        min_in_bounds_rate=min_in_bounds_rate,
    )
    if preferred is None or dispreferred is None:
        return f"N/A (trajectory feedback unavailable: {status})"

    preferred_mat = ep_dir / f"data_ep{preferred.episode}.mat"
    dispreferred_mat = ep_dir / f"data_ep{dispreferred.episode}.mat"

    if not preferred_mat.exists() or not dispreferred_mat.exists():
        return (
            "N/A (missing episode_data .mat files for selected episodes: "
            f"{preferred_mat.name if not preferred_mat.exists() else ''} "
            f"{dispreferred_mat.name if not dispreferred_mat.exists() else ''})"
        ).strip()

    parts = [
        "[Preferred/dispreferred trajectory snippets aligned with TPE gate]",
        f"Selection rule: {status}",
        "",
        "[Preferred trajectory snippets]",
    ]
    parts.append(
        _summarize_trajectory(
            preferred.episode,
            preferred_mat,
            "preferred trajectory",
            preferred.ep_cumulative_r,
            soc_bounds,
        )
    )
    parts.append("")
    parts.append("[Dispreferred trajectory snippets]")
    parts.append(
        _summarize_trajectory(
            dispreferred.episode,
            dispreferred_mat,
            "dispreferred trajectory",
            dispreferred.ep_cumulative_r,
            soc_bounds,
        )
    )
    return "\n".join(parts)

# 실제 task metric(objective, h2+degradation, SOC in bound rates) 기반 preferred / dispreferred pair를 골라 비교 설명하는 텍스트
def format_preference_feedback(
    episodes: List[EpisodeSummary],
    min_in_bounds_rate: float = 0.0,
) -> str:
    preferred, dispreferred, status = select_preference_pair(
        episodes,
        min_in_bounds_rate=min_in_bounds_rate,
    )
    if preferred is None or dispreferred is None:
        return f"N/A (preference feedback unavailable: {status})"

    preferred_obj = _episode_objective_metric(preferred)
    preferred_h2_degradation = _episode_h2_degradation_metric(preferred)
    dispreferred_obj = _episode_objective_metric(dispreferred)
    dispreferred_h2_degradation = _episode_h2_degradation_metric(dispreferred)
    preferred_obj_label = _episode_objective_metric_label(preferred)
    preferred_h2_degradation_label = _episode_h2_degradation_metric_label(preferred)
    dispreferred_obj_label = _episode_objective_metric_label(dispreferred)
    dispreferred_h2_degradation_label = _episode_h2_degradation_metric_label(dispreferred)

    preferred_extra = []
    if preferred_obj is not None:
        preferred_extra.append(f"{preferred_obj_label}={preferred_obj:.4f}")
    if preferred_h2_degradation is not None:
        preferred_extra.append(
            f"{preferred_h2_degradation_label}={preferred_h2_degradation:.4f}"
        )
    if preferred.objective_100km is not None and preferred_obj_label != "objective_100km":
        preferred_extra.append(f"objective_100km={preferred.objective_100km:.2f}")
    if preferred.mean_h2_cost is not None:
        preferred_extra.append(f"mean_h2_cost={preferred.mean_h2_cost:.4f}")
    if preferred.mean_fcs_cost is not None:
        preferred_extra.append(f"mean_fcs_cost={preferred.mean_fcs_cost:.4f}")
    if preferred.mean_batt_cost is not None:
        preferred_extra.append(f"mean_batt_cost={preferred.mean_batt_cost:.4f}")

    dispreferred_extra = []
    if dispreferred_obj is not None:
        dispreferred_extra.append(f"{dispreferred_obj_label}={dispreferred_obj:.4f}")
    if dispreferred_h2_degradation is not None:
        dispreferred_extra.append(
            f"{dispreferred_h2_degradation_label}={dispreferred_h2_degradation:.4f}"
        )
    if (
        dispreferred.objective_100km is not None
        and dispreferred_obj_label != "objective_100km"
    ):
        dispreferred_extra.append(f"objective_100km={dispreferred.objective_100km:.2f}")
    if dispreferred.mean_h2_cost is not None:
        dispreferred_extra.append(f"mean_h2_cost={dispreferred.mean_h2_cost:.4f}")
    if dispreferred.mean_fcs_cost is not None:
        dispreferred_extra.append(f"mean_fcs_cost={dispreferred.mean_fcs_cost:.4f}")
    if dispreferred.mean_batt_cost is not None:
        dispreferred_extra.append(f"mean_batt_cost={dispreferred.mean_batt_cost:.4f}")

    safety_floor = max(0.0, float(min_in_bounds_rate))
    lines = [
        "Preferred trajectory characteristics:",
        f"0) same pair selector as TPE gate: {status}",
        f"1) both preferred and dispreferred candidates must satisfy in_bounds_rate >= {safety_floor:.1f}%",
        "2) among SOC-qualified episodes, lower objective_cost is better",
        "3) if objective_cost is similar, lower h2_cost + degradation costs is better",
        "4) lower mean_h2_cost, mean_fcs_cost, and mean_batt_cost support the preference",
        "5) smoother control and fewer harmful oscillations in power split are preferred",
        "",
        "Pairwise comparison from current run:",
        (
            f"- preferred ep {preferred.episode}: in_bounds_rate={preferred.in_bounds_rate:.1f}%"
            + (", " + ", ".join(preferred_extra) if preferred_extra else "")
        ),
        (
            f"- dispreferred ep {dispreferred.episode}: in_bounds_rate={dispreferred.in_bounds_rate:.1f}%"
            + (", " + ", ".join(dispreferred_extra) if dispreferred_extra else "")
        ),
        "",
        "Current violation example:",
        "- reward should assign higher average step reward to the preferred trajectory than to the dispreferred trajectory.",
    ]
    return "\n".join(lines)

"""
parse_train_log()로 episodes 생성 -> 세 종류 피드백 생성 -> dict로 반환
"""
def build_feedback_bundle(
    log_path: str | Path,
    episode_data_dir: Optional[str | Path] = None,
    process_episodes: int = 5,
    soc_bounds: Tuple[float, float] = (0.4, 0.8),
    preference_in_bounds_floor: float = 0.0,
) -> Dict[str, str]:
    episodes = parse_train_log(log_path)
    return {
        "PROCESS_FEEDBACK": format_process_feedback(episodes, num_episodes=process_episodes),
        "TRAJECTORY_FEEDBACK": format_trajectory_feedback(
            episodes,
            episode_data_dir=episode_data_dir,
            soc_bounds=soc_bounds,
            min_in_bounds_rate=preference_in_bounds_floor,
        ),
        "PREFERENCE_FEEDBACK": format_preference_feedback(
            episodes,
            min_in_bounds_rate=preference_in_bounds_floor,
        ),
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parse FCEV train log into LLM feedback sections")
    parser.add_argument("--log-path", required=True)
    parser.add_argument("--episode-data-dir", default=None)
    parser.add_argument("--process-episodes", type=int, default=5)
    parser.add_argument("--soc-low", type=float, default=0.4)
    parser.add_argument("--soc-high", type=float, default=0.8)
    parser.add_argument("--preference-in-bounds-floor", type=float, default=0.0)
    args = parser.parse_args()

    bundle = build_feedback_bundle(
        log_path=args.log_path,
        episode_data_dir=args.episode_data_dir,
        process_episodes=args.process_episodes,
        soc_bounds=(args.soc_low, args.soc_high),
        preference_in_bounds_floor=args.preference_in_bounds_floor,
    )

    print("=== PROCESS_FEEDBACK ===")
    print(bundle["PROCESS_FEEDBACK"])
    print("\n=== TRAJECTORY_FEEDBACK ===")
    print(bundle["TRAJECTORY_FEEDBACK"])
    print("\n=== PREFERENCE_FEEDBACK ===")
    print(bundle["PREFERENCE_FEEDBACK"])


"""
PROCESS_FEEDBACK: 최근 episode 로그를 raw summary처럼 보여줌, 학습 흐름 파악용

PREFERENCE_FEEDBACK: 실제 TPE gate와 동일한 preferred / dispreferred pair 비교, reward가 어떤 방향으로 trajectory를 구분해야 하는지 명시

TRAJECTORY_FEEDBACK: 실제 TPE gate와 동일한 pair의 step-level 특징 비교, reward가 무엇을 더 높게 평가해야 하는지 진단용
"""


# ── h2 품질 점수 헬퍼 (policy_quality 용) ────────────────────────────────────

# Keep old scalar correction logs readable, but never compare them to paper fuel.


def deterministic_h2eq_corr_for_episode(ep, soc0: float = 0.6) -> Optional[float]:
    """Notebook paper fuel in g/100km (100 * equivalent_g_per_km).

    Old logs lack energy-weighted efficiency and the first recorded SOC. They
    must be re-evaluated from checkpoints, not reconstructed using time means.
    """
    row = getattr(ep, "eval_paper_fuel", None) or {}
    if row.get("fuel_metric_basis") != DETERMINISTIC_FUEL_BASIS:
        return None
    start = row.get("rollout_soc0")
    value = row.get("equivalent_g_per_km")
    if start is None or not math.isclose(float(start), float(soc0), abs_tol=1e-9):
        return None
    return 100.0 * float(value) if value is not None and math.isfinite(float(value)) else None


def h2_quality_scores(h2_series, floor_g100km: Optional[float],
                      level_mean: Optional[float] = None) -> Dict[str, Optional[float]]:
    """h2 점수 [0-100]: 레벨(물리 하한 대비) 70% + 일관성(p10/mean) 30% 블렌드.

    - 레벨 = 100 x floor / mean. 분자(floor)는 사이클 수요 x 최적 sfc 로 환경에서
      유도되는 정책 무관 상수라서(env_physics_facts.cycle_h2_floor_g_per_100km),
      점수가 실제 소비량에 단조가 된다 — "한결같이 나쁜" 정책이 p10/mean 일관성
      점수로 ~100 을 받던 눈멀음을 고친다. DP/baseline 해의 정보는 쓰지 않는다.
    - 일관성 = 기존 관례 그대로 sorted[max(0, n//10-1)] / mean.
    - floor 미확보(구 로그/유도 실패) 시 일관성 단독으로 후퇴한다.
    - level_mean: 레벨의 분모. policy_quality 는 수렴 꼬리(마지막 10%) 평균을 넘긴다 (2026-09-17) —
      chunk 평균은 agent 리셋 직후 탐색 구간이 섞여 baseline 자신도 73.4 (< 75) 로 떨어졌다.
      None 이면 series 평균.
    """
    vals = sorted(float(v) for v in h2_series if v is not None)
    if not vals:
        return {"h2_score": None, "h2_level_score": None, "h2_consistency_score": None,
                "h2_mean": None, "h2_p10": None}
    mean = sum(vals) / len(vals)
    p10 = vals[max(0, len(vals) // 10 - 1)]
    consistency = max(0.0, min(100.0, 100.0 * (p10 / mean))) if mean > 0 else 0.0
    level: Optional[float] = None
    level_basis = float(level_mean) if level_mean is not None else mean
    if floor_g100km and float(floor_g100km) > 0.0 and level_basis > 0.0:
        level = max(0.0, min(100.0, 100.0 * (float(floor_g100km) / level_basis)))
    score = (0.7 * level + 0.3 * consistency) if level is not None else consistency
    return {"h2_score": score, "h2_level_score": level, "h2_consistency_score": consistency,
            "h2_mean": mean, "h2_p10": p10}
