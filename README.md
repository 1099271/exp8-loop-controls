# exp8-loop-controls

Independent reproduction of, and control evaluations for, Experiment 8 ("Weight-Space Programming") of
[RikiyaT/lm_understand-logs](https://github.com/RikiyaT/lm_understand-logs) (commit `4d09ba6`): the `p50c` edit of
Qwen3.5-0.8B (64 columns of `mlp.down_proj` in layers 15 and 19, 131,072 weights), reported to raise MATH-500 from
7.9 % to 48.1 %.

**Status: complete (MATH-500 and GSM8K 2026-11-05; IFEval, E6, 2026-11-09).** All runs finished on one local RTX 4090; results were committed as they finished, so
the git history is the timeline. The write-up is [`report.md`](report.md) (Chinese).

## Question

The published scores use thinking mode (protocol `think35`). In that mode the unedited 0.8B model loops: 93 % of its
MATH-500 answers hit the 32,768-token cap. So is the gain

- **A**: a special direction that makes the model better at math, or
- **B**: anything that stops the looping would do?

The decision criteria were fixed in [`PLAN.md`](PLAN.md) (commit `2ebd527`) before any E1b–E5 result existed.
Results already known at that time are listed there separately and are not treated as pre-registered.

## What the authors already say

The [blog post](https://rikiyat.github.io/blog/weight-space-programming/) attributes the gain to loops, in its own words:
"Fixing loops, however, is not the same as making a model better at math: it lets the model finish answers it could
already work out." Its Gemma follow-up reports that Astra could not improve a model that rarely loops. The post does not
mention non-thinking mode (no occurrence of "non-thinking", "thinking mode" or "default" in the page text, 2026-11-04). The authors' published code does record the non-thinking case: in `exp8_math/code/profiles.py` the `qwen35` profile has
`"thinking": False` with the comment "with thinking on, the 0.8B looped ... and 92 % of MATH-500 answers hit 32,768 tokens
(MATH-500 9.3 %); the model card: "Qwen3.5-0.8B operates in non-thinking mode by default"", and another comment notes
"the unedited model read 55.5 % and 50.8 % in two 128-answer passes" (practice problems; mode not stated, but the unedited
model reads about 10 % on practice problems with thinking on). The post's runs use the separate `qwen35think` profile, and
no non-thinking row is in the published results. This
repository adds measurements to that account; it does not dispute it.

## Results

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
| **E4** | p50c | think35_s1000 (this machine) | **51.3 [47.8, 54.9]** | 32.4 | 22,011 | – | 500 |
| **E5** | rand0 | think35 | **23.3 [20.5, 26.2]** | 75.4 | 26,978 | – | 500 |
| **E5b** | rand1 | think35 | **10.7 [8.9, 12.6]** | 89.2 | 30,362 | – | 500 |
| E3b (one shard) | base | think35_rp105 | 14.5 [9.5, 20.2] | 85.2 | 29,372 | – | 100 |
| **E3** | base | think35_rp110 | **23.3 [20.4, 26.3]** | 75.0 | 27,112 | – | 500 |
| **E3** | p50c | think35_rp110 | **42.8 [39.3, 46.2]** | 42.3 | 22,825 | – | 500 |
| **E2** | p50c | think35_t10 | **28.0 [24.6, 31.4]** | 67.5 | 27,220 | – | 500 |
| **E2** | base | think35_t10 | **18.1 [15.4, 21.0]** | 81.2 | 29,472 | – | 500 |

Key observations (paired differences are over the same 500 problems unless noted):

- **Pipeline check.** Stage 1 matches the published numbers on the same shard.
- **E1 / E1b, non-thinking mode.** The unedited model, in the mode the model card describes as the 0.8B default, scores
  44.5 % at 8,192 tokens and **49.9 %** at 32,768 tokens, level with p50c in thinking mode: published p50c − base
  nothink 32k = −1.8 [−4.4, +0.9]; akhaliq's re-run − base nothink 32k = +1.1 [−1.6, +3.9]. These compare two different
  modes on two different machines, so they say the two scores are level, not that the two models are the same.
- **E4, same machine.** p50c in thinking mode (seed 1000) scores 51.3 % (cut 32.4 %). Same-machine comparison:
  p50c think − base nothink 32k = +1.5 [−1.3, +4.2], still level. E4 − akhaliq = +0.3 [−1.6, +2.2], but E4 − published =
  +3.2 [+1.3, +5.1]: both re-runs (vLLM 0.33.0, full release) sit about 3 points above the published 48.1, and the authors'
  text-only export and vLLM version may be why; this experiment cannot separate those causes. Against E4, the other
  thinking configs are: rand0 +28.0 [+25.2, +30.9], base rp1.1 +28.0 [+25.2, +30.6], base t1.0 +33.1 [+30.1, +36.1].
- **The edit in non-thinking mode** stops the remaining loops (cut 11.7 % → 0.4 %) with no change in MATH-500 accuracy
  (+0.3 [−1.9, +2.5]) and slightly lower GSM8K (54.9 vs 56.9).
- **GSM8K is different.** p50c in thinking mode (67.1 %, published) is +10.2 [+8.1, +12.3] above base non-thinking at
  32k (56.9 %). The token budget does not explain this gap. No no-edit method here stops the loops in thinking mode,
  so this data cannot say whether another loop-breaker would earn the same gain.
- **E2, temperature 1.0.** Base 18.1 % (cut 81.2 %). p50c 28.0 % (cut 67.5 %), which is −20.2 [−22.9, −17.4] against its
  published 48.1 % and +9.8 [+7.8, +11.8] against base at the same temperature. Both temperatures come from the model
  card: 0.6 is the setting of its thinking-mode benchmark table (the one the authors used, see the comment in
  `code/evaluate.py`), 1.0 is its general recommendation for thinking-mode text tasks. Astra's practice passes used 0.6;
  that p50c's sensitivity is caused by this is a hypothesis, not something tested here.
- **E3, repetition_penalty 1.1.** Base 23.3 % (cut 75.0 %). p50c 42.8 % (cut 42.3 %), −5.3 [−7.4, −3.2] against published.
- **E5, random direction** (same 64 columns, same norm, rank-1). 23.3 % (cut 75.4 %): +15.4 [+13.3, +17.5] over published
  base, with published p50c +24.8 [+22.1, +27.5] above it. **E5b (complete):** a second random direction scores 10.7 % with 89.2 % cut: +2.8 [+1.2, +4.4] over published base,
  −12.6 [−14.8, −10.4] against rand0, and E4 is +40.6 [+37.5, +43.7] above it. Same-size random directions range from barely
  any effect to about a third of the gain; two draws cannot say what is typical, but both are far below p50c. rand1 meets
  criterion 4's "close to base" (acc < 15 %, cut > 80 %).
- **Against the criteria fixed in `PLAN.md`.** No no-edit method and no random direction reaches cut < 50 %, so criterion
  1 (B) is not met and criterion 2 does not apply. Temperature 1.0 (cut 81.2 %) falls under criterion 3 (not a
  loop-breaker). Repetition penalty and rand0 (cut about 75 %) fall between the thresholds, which the criteria did not
  anticipate. rand0 (23.3 %, 75.4 %) meets neither side of criterion 4: above "close to base" (acc < 15 %, cut > 80 %) and
  far from p50c.

**E3b (rp 1.05, first 100 problems).** Weaker than rp 1.1: 14.5 % with 85.2 % cut, −6.2 [−10.0, −2.8] against rp 1.1 on the same
problems.

**E6, IFEval (amendment 4 in `PLAN.md`, added after the main runs, criteria committed before any IFEval generation).**
The abstract says the edit "generalizes out of the box to instruction following, raising IFEval by 3x" (21.0 → 62.3,
thinking mode; 74.9 % of base answers hit the cap, and an answer without `</think>` is graded as empty). The authors did
not publish their IFEval grader, so this uses Google's official `instruction_following_eval` (google-research `0eebfd40`,
unmodified). Re-grading all 400 published IFEval first samples with it reproduces the published per-problem results
400/400 (`analysis/validate_ifeval_grader.txt`). 541 problems, 2 samples, strict prompt-level accuracy:

| Config | Model | Protocol | IFEval acc | inst-level | cut | mean tok |
|---|---|---|---|---|---|---|
| published | base | think35 | 21.0 [18.2, 23.8] | 18.3 | 74.9 | 25,296 |
| published | p50c | think35 | 62.3 [58.8, 65.7] | 69.7 | 2.2 | 4,241 |
| E6c | p50c | think35 (local) | 63.8 [60.3, 67.2] | 71.2 | 2.2 | 4,154 |
| E6d | base | think35 (local, shard 0/5, 109 problems) | 20.6 [14.2, 27.5] | 19.1 | 73.9 | 25,147 |
| E6a | base | nothink35_32k | 52.8 [49.1, 56.5] | 63.6 | 0.6 | 444 |
| E6b | p50c | nothink35_32k | 50.5 [46.8, 54.2] | 61.4 | 0.0 | 252 |

- Base non-thinking − p50c thinking: −11.0 [−14.8, −7.2] (local), −9.5 [−13.4, −5.7] (published). Both intervals lie
  below −3, so criterion 2 of amendment 4 is met: base non-thinking does not reach p50c thinking on IFEval.
- Base non-thinking − published base thinking: +31.8 [+27.8, +35.8]. About 32 of the 41 points need no edit, only no
  thinking; about 10 points remain, as on GSM8K.
- p50c non-thinking − base non-thinking: −2.3 [−5.0, +0.5]. The edit does not help instruction following without thinking.
- The comparison cannot separate "the edit adds ability" from "thinking that terminates helps IFEval, and only the edit
  makes base's thinking terminate here"; E6b gives no support to the first. `report.md` 4.6 narrows the wording of
  amendment 4's criterion 2 accordingly.
- E6c − published p50c: +1.5 [−1.4, +4.3]; E6d − published base (same 109 problems): −0.5 [−6.9, +6.0].

## Layout

| Path | Contents |
|---|---|
| `report.md` | the final report (Chinese) |
| `analysis/` | scripts and outputs behind every table in the report |
| `PLAN.md` | question, configurations, pre-fixed decision criteria (Chinese) |
| `CHANGES.md` | every change made to the authors' code, and why (Chinese) |
| `code/` | copy of `exp8_math/code/` from the source repo, plus `make_random_control.py` and `summarize.py` |
| `tools/` | job queue runner, queue swap script, vLLM smoke test (`run_queue.sh` at the root is the same file, used by the running queue) |
| `queues/` | the exact job lists that were run |
| `code/instruction_following_eval/`, `external/ifeval_official/` | Google's official IFEval checkers and prompts (Apache-2.0), with sha256 |
| `external/web/`, `external/x/` | snapshots of the blog post, Honnibal's critique and the announcement thread, used to verify quotes |
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
- `code/instruction_following_eval/` and `external/ifeval_official/input_data.jsonl` are from google-research (Apache-2.0, see the LICENSE file there).
- Model: [Qwen/Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B) (Apache-2.0); no weights are redistributed.
