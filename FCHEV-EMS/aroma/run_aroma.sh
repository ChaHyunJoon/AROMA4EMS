#!/usr/bin/env bash
# Launch one AROMA4EMS search: iteration 1 trains SAC on the baseline reward, iterations 2-6 are
# LLM-proposed rewards (400 episodes each, ep399 actor evaluated). Settings match the paper runs.
# Usage: bash run_aroma.sh [--print-commands] [--seed N] [extra main_ldri_refine.py args]
#   --agent_type gpt|claude selects the LLM backbone (default claude; later arguments override).
# Outputs go to <repo>/runs/seed<N>_obscur_<timestamp>/. Set PYTHON to choose the interpreter.
set -euo pipefail

run_seed=41
print_commands=false
extra_args=()
while (( $# > 0 )); do
  case "$1" in
    --seed)
      if (( $# < 2 )); then
        printf 'Error: --seed requires an integer.\n' >&2
        exit 2
      fi
      run_seed="$2"
      shift 2
      ;;
    --seed=*)
      run_seed="${1#--seed=}"
      shift
      ;;
    --print-commands)
      print_commands=true
      shift
      ;;
    *)
      extra_args+=("$1")
      shift
      ;;
  esac
done
# NumPy's training RNG accepts seeds in the unsigned 32-bit range.
if [[ ! "$run_seed" =~ ^[0-9]{1,10}$ ]]; then
  printf 'Error: --seed must be an integer between 0 and 4294967295.\n' >&2
  exit 2
fi
run_seed=$((10#$run_seed))
if (( run_seed > 4294967295 )); then
  printf 'Error: --seed must be an integer between 0 and 4294967295.\n' >&2
  exit 2
fi

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
python_bin="${PYTHON:-python3}"
ems_root="$project_root/FCHEV-EMS"
campaign="$project_root/runs/seed${run_seed}_obscur_$(date +%Y%m%d_%H%M%S_%N)"

common=(
  --scenario_name Standard_WLTC_WVUINTER
  --MODE CS --soc0 0.6 --soc_target 0.6 --soc_low 0.4 --soc_high 0.8
  --training_initial_states fixed
  --w_soc 500 --w_h2 10 --w_fc 4275000 --w_batt 1116000
  --eq_h2_batt_coef 0.0164
  --DRL SAC --policy Gaussian --seed "$run_seed" --cuda True
  --load_or_not False --start_episode 0 --max_episodes 500
  --batch_size 256 --buffer_size 500000
  --gamma 0.995 --tau 0.005 --alpha 1 --auto_tune True
  --target_entropy_scale 2 --policy_delay 1
  --lr_critic 3e-4 --lr_critic_min 1e-4
  --lr_actor 1e-4 --lr_actor_min 2e-5
  --lr_alpha 2e-4 --lr_alpha_min 5e-5
  --lr_schedule_episodes 400 --lr_restart_cycles 1 --lr_warmup_ratio 0
  --auto_lr_on_reward_patch False --reset_agent_on_patch True
  --critic_layernorm
  --per --per_alpha 0.6 --per_beta0 0.4 --per_beta_steps 0 --per_eps 1e-6
  --ramp_limit_kw 10
  --obs_norm fixed --obs_speed_scale 40 --obs_acc_scale 4 --obs_timing current
  --failure_cost_per_step 1000 --unserved_cost_per_kw 50
  --reward_module aroma_matched_reward --reward_file "$campaign/aroma_matched_reward.py"
)

search_command=(
  "$python_bin" -u "$ems_root/aroma/main_ldri_refine.py" "${common[@]}"
  --refinement_protocol sequential --search_plan archive
  --agent_type claude --multi_agent_review True
  --baseline_reward_file "$ems_root/aroma/agentEMS_val_base.py"
  --chunk_episodes 400 --ldri_iterations 6 --feedback_process_episodes 50
  --artifact_detail compact --ldri_root "$campaign/search"
  --file_v "seed${run_seed}_obscur_seq_v3_cost_iter6"
)

# Extra arguments are forwarded (e.g. --seed_chunk_dir/--seed_reward_file or --file_v).
search_command+=("${extra_args[@]}")
if [[ "$print_commands" == true ]]; then
  printf '%q ' "${search_command[@]}"
  printf '\n'
  exit 0
fi

# Isolate the mutable reward module from other AROMA runs.
mkdir -p "$campaign"
cp "$ems_root/aroma/agentEMS_for_feedback.py" "$campaign/aroma_matched_reward.py"
export PYTHONPATH="$campaign${PYTHONPATH:+:$PYTHONPATH}"
cd "$ems_root"
printf 'AROMA campaign: %s\n' "$campaign"
"${search_command[@]}"

# Verify the exported reward belongs to the completed search.
"$python_bin" - "$campaign" <<'PY'
import ast
import json
import sys
import textwrap
from pathlib import Path

root = Path(sys.argv[1])
summaries = list((root / 'search').glob('*/run_summary.json'))
if len(summaries) != 1:
    raise SystemExit('Expected exactly one completed AROMA search.')
summary = json.loads(summaries[0].read_text())
if summary.get('workflow_status') != 'completed':
    raise SystemExit('AROMA search did not complete.')
selected = (summaries[0].parent / 'final_reward.py').read_text()
module = ast.parse((root / 'aroma_matched_reward.py').read_text())
cls = next(n for n in module.body if isinstance(n, ast.ClassDef) and n.name == 'EMS')
method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'get_reward')
expected = ast.parse(textwrap.dedent(selected)).body[0]
if ast.dump(method, include_attributes=False) != ast.dump(expected, include_attributes=False):
    raise SystemExit('Installed reward differs from final_reward.py.')
(root / 'selected_reward.py').write_text(selected)
print('Selected reward:', root / 'selected_reward.py')
print('Search final selection:', json.dumps(summary['final_selection'], ensure_ascii=False))
PY

printf 'Six-iteration search artifacts: %s\n' "$campaign/search"
