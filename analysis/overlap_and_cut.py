"""No-GPU analyses for the report. (1) Do two configs solve the same problems? Per-problem correlation, with the same
model re-run (published p50c vs akhaliq) as the ceiling set by sampling noise. (2) How much of a thinking-mode score comes
from answers with no </think>, whose last \\boxed{} inside the reasoning is what gets graded? Uses the published first
sample of every problem. No </think> is a proxy for "cut at the limit": per-sample finish reasons were not published."""
import glob
import gzip
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from weightenv.lmo.tasks import mathqa as Q  # noqa: E402

P = "/home/www/workspace/github/lm_understand-logs/exp8_math/eval/"
W = "/home/www/workspace/mathedit/"


def load(pat):
    return {p["id"]: np.mean(p["correct"]) for f in glob.glob(pat) for p in json.load(open(f))}


cfg = {"pub p50c think": load(P + "p50c/parts/math500_*/math500_per_problem.json"),
       "akhaliq p50c think": {p["id"]: np.mean(p["correct"]) for p in
                              json.load(open(W + "external/hf_akhaliq_eval/scores_edited_math500.json"))["per_problem"]},
       "base nothink32k": load(W + "eval/base__nothink35_32k/parts/math500_*/*_per_problem.json"),
       "p50c nothink32k": load(W + "eval/p50c__nothink35_32k/parts/math500_*/*_per_problem.json"),
       "base nothink8k": load(W + "eval/base__nothink35/parts/math500_*/*_per_problem.json"),
       "p50c nothink8k": load(W + "eval/p50c__nothink35/parts/math500_*/*_per_problem.json")}
ids = sorted(cfg["pub p50c think"])
print("(1) per-problem Pearson r, and problems solved at least 3/4 by one config and at most 1/4 by the other")
for a, b in [("pub p50c think", "akhaliq p50c think"), ("base nothink8k", "p50c nothink8k"), ("base nothink32k", "p50c nothink32k"),
             ("base nothink32k", "pub p50c think"), ("base nothink32k", "akhaliq p50c think")]:
    x, y = np.array([cfg[a][i] for i in ids]), np.array([cfg[b][i] for i in ids])
    print(f"  {a:18s} vs {b:18s} r={np.corrcoef(x, y)[0, 1]:.3f}  only-first {int(((x >= .75) & (y <= .25)).sum()):3d}  only-second {int(((y >= .75) & (x <= .25)).sum()):3d}")

print("(2) published first samples: score by whether the answer closed its reasoning")
for run in ("unedited", "p50c"):
    for s in ("math500", "gsm8k"):
        n = {True: [0, 0, 0], False: [0, 0, 0]}
        for d in glob.glob(f"{P}{run}/parts/{s}_*"):
            per = {p["id"]: p for p in json.load(open(glob.glob(d + f"/{s}_per_problem.json")[0]))}
            for l in gzip.open(glob.glob(d + f"/{s}_first_samples.jsonl.gz")[0], "rt"):
                x = json.loads(l)
                c = "</think>" in x["text"]
                n[c][0] += 1
                n[c][1] += per[x["id"]]["correct"][0]
                n[c][2] += Q.extract(x["text"])[0] is not None
        tot = n[True][0] + n[False][0]
        print(f"  {run:9s} {s:8s} n={tot:5d} | closed: {n[True][0]:5d} acc {100*n[True][1]/max(n[True][0],1):5.1f}"
              f" | not closed: {n[False][0]:5d} acc {100*n[False][1]/max(n[False][0],1):5.1f} (has a box {100*n[False][2]/max(n[False][0],1):5.1f} %)"
              f" | share of all correct from not closed {100*n[False][1]/max(n[True][1]+n[False][1],1):5.1f} %")
