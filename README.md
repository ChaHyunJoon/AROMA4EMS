# AROMA4EMS

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24525205.svg)](https://doi.org/10.5281/zenodo.24525205)

Code, data and run records for **AROMA4EMS: Autonomous Reward Optimization via Multi-Agent Review for Energy
Management Systems in Fuel Cell Electric Vehicles** (H. J. Cha, S. W. Cha, J. Landay; manuscript submitted to
IEEE Transactions on Transportation Electrification).

AROMA4EMS edits the reward function of a soft actor-critic (SAC) energy management system for a fuel cell electric
vehicle. Four LLM reviewers analyse rollouts of the trained policies, an orchestrator merges their hypotheses into one
edit, and a proposer writes it as reward code from a catalog of interpretable cost terms. Each proposal is verified,
retrained from scratch, and adopted only if it lowers the total operating cost while hydrogen consumption, battery
degradation and final SOC stay within guard limits around the baseline.

> The method was called **LDRI** in early versions of this code. Some file names (`main_ldri_refine.py`,
> `arguments_ldri.py`, ...), CLI options (`--ldri_iterations`, `--ldri_root`) and class names (`RunnerLDRI`) still
> carry that name. They are the same method.

## Repository layout

```
FCHEV-EMS/                     simulation, RL, benchmarks
  FCHEV_SOH.py                 vehicle, motor, fuel-cell system and FC degradation model      (Sec. II-A/B, eqs. 1-9)
  Battery.py                   battery equivalent circuit and capacity-loss model              (Sec. II-C, eqs. 10-15)
  power_constraints.py         battery power clamp, unserved / unaccepted power                (eq. 20)
  common/env.py                environment used by SAC, DP replay and the rule-based EMS
  agentEMS_pure_h2_consumption.py   baseline EMS reward                                        (eqs. 21-23)
  sac.py, common/fc_action.py  SAC with the state-dependent action interval                    (Sec. III-B, eqs. 24-26)
  common/paper_fuel_economy.py equivalent hydrogen consumption                                 (eqs. 30-31)
  main.py                      standalone SAC training
  dp_main_interp_2d.py         dynamic-programming benchmark (+ DP_EMS_agent_new.py, DP_env.py) (Sec. IV-D)
  rule_based_eval.py           efficient-band rule-based EMS (+ rule_based_controller.py)       (Sec. IV-D)
  eval_actor_cycles.py         deterministic evaluation of a saved actor on any cycle
  aroma/                       AROMA4EMS workflow                                               (Sec. III-C)
    run_aroma.sh               launcher with the paper settings
    main_ldri_refine.py        entry point
    sequential_workflow.py     iteration loop, adoption gate (eq. 28), archive and edit base (eq. 29)
    multi_agent_review.py      reviewer agents and orchestrator
    reward_terms.py            reward-term catalog and its checks
    candidate_validation.py    pre-training verification, incl. the cost-scale check (eq. 27)
    operating_cost.py          operating cost per 100 km (eqs. 32-33)
    agentEMS_val_base.py       baseline reward as the editable reward module
    tests/                     unit tests
project-data/                  component maps (FCHEV_data, Battery_data) and driving cycles (.mat)
results/
  aroma_runs/                  the eight searches of the paper (configs, LLM reviews, proposed rewards, decisions)
  evaluation_runs/             evaluation tables of the paper and the scripts that produced them
visualization/
  paper_figs_multi_seed.ipynb      Fig. 4, Supplementary Tables S3/S6, Figs. S1-S4 (four seeds)
  paper_figs_seed1_gpt_iter3.ipynb Figs. 3, 5-8, Supplementary Table S4 (seed 1, GPT)
```

## Installation

Python 3.12.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd FCHEV-EMS && python -m pytest aroma/tests -q
```

## Results bundle

Rollout traces (`.mat`) are not stored in git. `aroma4ems-results.tar.gz` (GitHub release) holds the 16 traces
plotted in Figs. 5-8: DP, rule-based EMS, baseline SAC and AROMA-SAC (seed 1, GPT, iteration 3) on UDDS, WVUSUB,
LA92 and HWFET. Unpack it at the repository root, which places the files at the paths referenced by the tables in
`results/`:

```bash
tar -xzf aroma4ems-results.tar.gz      # from the repository root
```

All other figures and tables of the paper are built from files already in git.

## Reproducing the paper

### Figures and tables

```bash
cd visualization
jupyter execute paper_figs_seed1_gpt_iter3.ipynb   # Fig. 3, Figs. 5-8 (needs the results bundle)
jupyter execute paper_figs_multi_seed.ipynb        # Fig. 4 and the four-seed tables
```

Outputs are written to `visualization/paper_figures/`:

| Paper | Output file (`paper_figures/pdf/`) |
|---|---|
| Fig. 3 | `seed1_gpt_iter3__fig06_training.pdf` |
| Fig. 4 | `multi_seed_v3cat__driving_cost_hydrogen_degradation.pdf` (deployed policies); the best-iteration version is `multi_seed_v3cat_heldout_best__driving_cost_hydrogen_degradation.pdf` |
| Figs. 5-8 | `seed1_gpt_iter3__fig09_timeseries_UDDS.pdf` ... `fig12_timeseries_HWFET.pdf` |

The seed-41 operating-point figures in `paper_figs_multi_seed.ipynb` are not part of the paper. Their traces are
not distributed, so those cells print a skip message.

### Benchmarks

Run from `FCHEV-EMS/`, once per cycle (`Standard_UDDS`, `Standard_WVUSUB`, `Standard_LA92`, `Standard_HWFET`):

```bash
# dynamic programming
python -u dp_main_interp_2d.py --scenario_name Standard_UDDS --w_soc 500 --ramp_limit_kw 10 \
  --soc0 0.6 --soc_target 0.6 --MODE CS --gamma 0.995 --file_v fc_eff_remap --w_terminal 1000000 \
  --unserved_cost_per_kw 50 --dp_soc_increment 0.0001 \
  --plant_conditions ../results/evaluation_runs/20261013_motor_efficiency_ramp10/plant_conditions.json

# efficient-band rule-based EMS (p_off 0.95 kW, minimum off time 90 s)
python -u rule_based_eval.py --scenario_name Standard_UDDS --w_soc 500 --ramp_limit_kw 10 \
  --soc0 0.6 --soc_target 0.6 --MODE CS --gamma 0.995 --rb_auto_soc_balance 1 \
  --rb_policy efficient_band --rb_p_off_kw 0.95 --rb_min_off_s 90 \
  --rb_save_dir ./eva_rule_based --rb_name efficient_band
```

### AROMA4EMS search

A search trains one SAC policy per iteration (400 episodes each, six iterations) and calls the LLM API from
iteration 2 on. Set the API key of the chosen backbone first.

```bash
export OPENAI_API_KEY=...        # --agent_type gpt    (gpt-5.2 + gpt-5-mini)
export ANTHROPIC_API_KEY=...     # --agent_type claude (Claude Sonnet 4.6 + Claude Haiku 4.5)
bash FCHEV-EMS/aroma/run_aroma.sh --seed 1 --agent_type gpt
```

The launcher fixes every training setting used in the paper. Use it rather than calling `main_ldri_refine.py`
directly, because some parser defaults in `arguments_ldri.py` differ from the paper settings. Outputs go to
`runs/`. LLM responses are not deterministic, so a new search does not repeat the proposals of the paper. The
recorded searches are in `results/aroma_runs/`.

### Evaluating a trained policy

`results/evaluation_runs/*/manifest.json` lists every evaluated actor with its checkpoint path and SHA-256, and
`results/evaluation_runs/<run>/evaluate_all_iters.py` is the script that produced the rollouts. Network
checkpoints are not distributed. To evaluate an actor from a new search:

```bash
cd FCHEV-EMS
python eval_actor_cycles.py --eva_root ../runs/eval --label aroma --cycles Standard_UDDS \
  --actor ../runs/<search>/search/<run>/trials/<trial>/models/iter_001/Standard_WLTC_WVUINTER/net_params/actor_iter001_ep399.pkl
```

## The eight searches

| Backbone | Seed | Directory in `results/aroma_runs/` |
|---|---|---|
| GPT | 1 | `seed1_obscur_20261018_061824_704722118` |
| Claude | 1 | `seed1_obscur_20261018_113049_381984490` |
| GPT | 41 / 61 / 81 | `seed{41,61,81}_obscur_20261016_*` |
| Claude | 41 / 61 / 81 | `seed{41,61,81}_obscur_20261017_*` |

Each search directory contains `run_config.json` (all settings), `summary.md` and `run_summary.json` (decision of
every iteration), and per iteration `review.json` (reviewer and orchestrator outputs), `candidate.py` (the proposed
reward), `result.json` and `llm_usage.json`. `trials/<id>/reward.py` is the reward each policy was trained with.
The Claude and GPT searches of the same seed share iteration 1 (the baseline SAC). For seeds 41/61/81 it was trained
in a separate baseline run and reused through `--fork_from_run_root`. The tables in
`results/evaluation_runs/20261019_*` also contain seed 21, which is not part of the paper. Its searches are not
included.

### Code version of the recorded searches

The code in this repository is the version that ran the two seed-1 searches. The searches of seeds 41/61/81 ran
on an earlier revision of `aroma/candidate_validation.py`, `aroma/reward_terms.py` and
`aroma/sequential_workflow.py`. The plant, SAC, benchmark and evaluation code is the same for all eight. Re-running
the evaluated policies, the rule-based EMS and DP with this code reproduces the stored rollouts exactly.

## Citation

```bibtex
@article{cha_aroma4ems,
  title   = {AROMA4EMS: Autonomous Reward Optimization via Multi-Agent Review for Energy Management Systems
             in Fuel Cell Electric Vehicles},
  author  = {Cha, Hyun Joon and Cha, Suk Won and Landay, James},
  journal = {IEEE Transactions on Transportation Electrification},
  note    = {submitted}
}
```

Code and data (all versions): [doi:10.5281/zenodo.24525205](https://doi.org/10.5281/zenodo.24525205)

```bibtex
@software{cha_aroma4ems_code,
  title   = {{AROMA4EMS}: Code and Data for Autonomous Reward Optimization via Multi-Agent Review for Energy
             Management Systems in Fuel Cell Electric Vehicles},
  author  = {Cha, Hyun Joon and Cha, Suk Won and Landay, James},
  doi     = {10.5281/zenodo.24525205},
  url     = {https://github.com/ChaHyunJoon/AROMA4EMS}
}
```
