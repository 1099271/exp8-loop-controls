# exp8-loop-controls

Independent reproduction of, and control evaluations for, Experiment 8 ("Weight-Space Programming") of
[RikiyaT/lm_understand-logs](https://github.com/RikiyaT/lm_understand-logs) (commit `4d09ba6`): the `p50c` edit of
Qwen3.5-0.8B (64 columns of `mlp.down_proj` in layers 15 and 19, 131,072 weights), reported to raise MATH-500 from
7.9 % to 48.1 %.

**Status: in progress.** Runs are still going on one local RTX 4090; results are committed as they finish, so the
git history is the timeline. Numbers below are as of 2026-11-03.

## Question

The published scores use thinking mode (protocol `think35`). In that mode the unedited 0.8B model loops: 93 % of its
MATH-500 answers hit the 32,768-token cap. So is the gain

- **A**: a special direction that makes the model better at math, or
- **B**: anything that stops the looping would do?

The decision criteria were fixed in [`PLAN.md`](PLAN.md) (commit `2ebd527`) before any E1b–E5 result existed.
Results already known at that time are listed there separately and are not treated as pre-registered.

## Results so far

MATH-500 / GSM8K, 4 samples per problem, accuracy with a 95 % problem-level bootstrap interval. `cut` = share of
samples that hit `max_tokens`. "pub" = the authors' published runs.

| Config | Model | Protocol | MATH-500 acc | cut | mean tok | GSM8K acc | Problems |
|---|---|---|---|---|---|---|---|
| pub | base | think35 | 7.9 [6.0, 9.8] | 93.0 | 30,868 | 13.8 | 500 / 1319 |
| pub | p50c | think35 | 48.1 [44.3, 51.8] | 33.1 | 22,037 | 67.1 | 500 / 1319 |
| Stage 1 | base | think35 | 5.0 (pub same shard 7.0) | 95.5 (95.0) | 31,463 | – | 50 |
| Stage 1 | p50c | think35 | 43.0 (pub same shard 37.0) | 34.0 (31.0) | 23,564 | – | 50 |
| **E1** | base | nothink35 | **44.5 [41.2, 48.1]** | 30.4 | 3,661 | **56.9 [54.7, 59.2]** | 500 / 1319 |
| **E1** | p50c | nothink35 | **44.3 [40.9, 47.7]** | 32.0 | 3,836 | **54.4 [52.2, 56.6]** | 500 / 1319 |
| ref: akhaliq re-run | p50c (HF, same sha256) | think35, seed 0, H200 | 51.0 (paired vs pub +2.9 [+1.0, +4.8]) | 31.6 | 21,704 | – | 500 |
| **E1b** | base | nothink35_32k | **49.9 [46.5, 53.3]** | 11.7 | 7,697 | – | 500 |
| **E1b** | p50c | nothink35_32k | **50.1 [46.9, 53.4]** | 0.4 | 6,219 | – | 500 |
| E1b (GSM8K, post hoc) | base / p50c | nothink35_32k | – | – | – | 56.9 [54.6, 59.2] / 54.9 [52.6, 57.1] | 1319 |
| E5 (partial) | rand0 | think35 | 24.9 [21.8, 28.3] | 73.7 | 26,516 | – | 400 |
| E3 (partial) | base | think35_rp110 | 24.5 [21.2, 27.9] | 73.8 | 26,840 | – | 400 |
| E3 (partial) | p50c | think35_rp110 | 43.3 [38.7, 47.8] | 40.9 | 22,472 | – | 300 |
| E2 (partial) | p50c | think35_t10 | 29.8 [25.9, 33.6] | 65.2 | 26,832 | – | 400 |
| E2 (partial) | base | think35_t10 | 18.9 [15.8, 22.2] | 80.4 | 29,366 | – | 400 |

Key observations so far:

- Stage 1 matches the published pipeline (the base model loops about 95 % of the time; p50c about a third).
- **E1:** the *unedited* model in non-thinking mode, which is the model card's default for 0.8B, already scores
  44.5 % on MATH-500, 3.6-6.5 points below p50c in thinking mode (48.1 % published by the authors, 51.0 % in
  akhaliq's independent re-run of the same weights; that +2.9 gap with identical weights, protocol and seed is the
  run-to-run variance from hardware and batching). In non-thinking mode the edit
  changes nothing (paired difference −0.2, 95 % CI [−2.2, +1.8]).
- **E1b:** with the same 32,768-token budget as the thinking runs, the *unedited* model in non-thinking mode scores
  **49.9 %**, inside p50c's thinking range (48.1-51.0). Paired over 500 problems: published p50c minus base
  non-thinking 32k = −1.8 [−4.4, +0.9]; akhaliq's p50c re-run minus it = +1.1 [−1.6, +3.9]. The 3.6-6.5 point gap in
  E1 was the 8,192-token cap, not the edit. In non-thinking mode the edit does stop the remaining loops (cut 11.7 %
  → 0.4 %) but does not change accuracy (+0.3 [−1.9, +2.5]).
- **GSM8K stays open after E1b** (post-hoc supplement, amendment 2): the 32k budget does not move base non-thinking
  (56.9 → 56.9), so p50c in thinking mode is **+10.2 [+8.1, +12.3]** above it (paired, 1,319 problems). On GSM8K a
  thinking mode that terminates is worth something that non-thinking mode does not give.
- **E2 on p50c (first 100 problems):** at temperature 1.0 (the model card's thinking setting) p50c loops again: 70.0 %
  of answers hit the cap and it scores 25.8 %, against 45.0 % (published) / 49.0 % (akhaliq) at temperature 0.6 on the
  same problems (paired −19.2 [−25.8, −13.0] vs published). The edit's loop-breaking depends on the sampling it was
  found with (Astra's practice passes used the evaluation's temperature 0.6). At 1.0 it is still +10.5 [+5.8, +15.5]
  above the base model at 1.0 (15.2 %).
- **E3 (first 100 problems):** repetition_penalty 1.1 does not stop the base model's loops (cut 77.8 %, 20.8 %;
  +14.5 [+9.5, +20.0] over published base, p50c published is +24.2 [+18.8, +30.0] above it). On p50c it costs little
  (41.5 %, −3.5 [−8.8, +1.8] vs published). Per the pre-set rule (amendment 1), E3b (1.05) is therefore run.
- **E5 (first 100 problems):** the random-direction control (same 64 columns, same norm, rank-1) scores 20.2 %
  (cut 77.8 %): above the base model on the same problems (6.2 %, +14.0 [+10.0, +18.2]) but far below p50c
  (45.0 % published / 49.0 % akhaliq; p50c − rand0 = +24.8 [+19.0, +30.5]). So far the direction matters for how
  well the loop is broken.
- Earlier note, GSM8K: p50c in thinking mode (67.1 %) is about 10 points above the base model in non-thinking mode
  (56.9 %). E2–E5 test whether other ways of stopping the loop also recover that.
- E2 (temperature 1.0, model-card thinking setting), first 100 problems: the base model goes from 6.2 % (published
  think35, same problems) to 15.2 %, but 84.5 % of its answers still hit the cap; p50c's published score on the same
  problems is 45.0 %.

Still running (see [`queues/stage2f.txt`](queues/stage2f.txt), amendment 3 in `PLAN.md`; order changed by amendment 1 in `PLAN.md`: E5 first in each round, E3b conditional on E3, E4 last):

| Name | Model | Change vs. think35 |
|---|---|---|
| E2 | base, p50c | temperature 1.0 |
| E3 | base, p50c | repetition_penalty 1.1 |
| E4 | p50c | seed 1000; also the only full p50c think35 run on this machine (same-hardware reference for E1b) |
| E5b | rand1 | second random direction (seed 1, \|cos\| with rand0 = 0.0066), think35 |
| E3b | base | repetition_penalty 1.05, one shard only (amendment 3) |
| E5 | rand0 | same 64 columns, same norm, rank-1, random output direction orthogonal to p50c's |

The final write-up will be `report.md` (Chinese).

## Layout

| Path | Contents |
|---|---|
| `PLAN.md` | question, configurations, pre-fixed decision criteria (Chinese) |
| `CHANGES.md` | every change made to the authors' code, and why (Chinese) |
| `code/` | copy of `exp8_math/code/` from the source repo, plus `make_random_control.py` and `summarize.py` |
| `tools/` | job queue runner, queue swap script, vLLM smoke test (`run_queue.sh` at the root is the same file, used by the running queue) |
| `queues/` | the exact job lists that were run |
| `external/hf_akhaliq_eval/` | akhaliq's re-run scores of p50c from the authors' HF repo (Apache-2.0), with source and hashes |
| `eval/<model>__<protocol>/` | results in the source repo's format: `parts/<set>_s<i>of<k>/{scores.json, *_per_problem.json, *_first_samples.jsonl}`, `merged.json` |
| `eval/summary.json` | output of `code/summarize.py` (merged scores and bootstrap intervals) |
| `logs/` | full stdout/stderr of every run |
| `provenance/` | OS/driver/CUDA/package versions, `pip freeze`, sha256 of every weight file and benchmark file, build logs of p50c and rand0 |

Not committed (rebuildable and hash-checked via `provenance/hashes.txt`): model weights, the venv, caches, and the
benchmark files under `bench/`.

## Reproducing

Hardware: one RTX 4090 24 GB (WSL2, Ubuntu 24.04). Software: Python 3.12, vllm 0.33.0 (bundled torch 2.14.0+cu130),
math-verify 0.9.0. Exact versions are in `provenance/`.

```bash
uv venv .venv --python 3.12 && source .venv/bin/activate
uv pip install vllm==0.33.0 transformers datasets math-verify==0.9.0 numpy
hf download Qwen/Qwen3.5-0.8B --revision 2fc06364715b967f1860aea9cf38778875588b17 --local-dir models/base

# p50c: apply the published edit (checks sha256 of both tensors)
F=model.safetensors-00001-of-00001.safetensors
cp -r models/base models/p50c
python code/apply_edit.py models/base/$F <source repo>/exp8_math/runs/p50c/edit models/p50c/$F
# rand0: random-direction control (E5)
cp -r models/base models/rand0
python code/make_random_control.py models/base models/p50c models/rand0 0   # seed 0; see provenance/make_rand0.log

python code/evaluate.py prepare        # builds bench/ (ROOT is set in code/evaluate.py, see CHANGES.md)
# one job, e.g. E1 base on MATH-500 shard 0/5:
python code/evaluate.py run models/base eval/base__nothink35/parts/math500_s0of5 \
    --sets math500 --protocol nothink35 --shard 0/5
tools/run_queue.sh queues/stage2b.txt  # runs a whole queue; finished jobs are skipped
python code/summarize.py eval <source repo>/exp8_math/eval   # writes eval/summary.json
```

Check weights and benchmark files with `sha256sum` against `provenance/hashes.txt`.

## License and attribution

- `code/` is derived from the MIT-licensed scripts of RikiyaT/lm_understand-logs; those scripts and the new ones here
  are under the MIT License (see `LICENSE`, which keeps the original copyright notice).
- Results, logs and documents are derived from CC BY 4.0 material of the same repository (commit `4d09ba6`) and are
  released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- Problem texts quoted in `*_first_samples.jsonl` come from MATH (MIT) and GSM8K (MIT) and stay under their licenses.
- Model: [Qwen/Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B) (Apache-2.0); no weights are redistributed.
