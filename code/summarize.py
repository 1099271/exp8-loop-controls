"""Reproduction summary: merge every eval/<config>/parts with merge.py, then per set: acc, cut_share, mean_tokens,
a 95 % bootstrap interval over problems (problems resampled, the per-problem mean of its samples), and paired
differences between configs on the same problems.   python summarize.py [eval dir] [published eval dir]"""
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import merge as M  # noqa: E402


def per_problem(d, s):
    out = {}
    for f in glob.glob(os.path.join(d, "parts", f"{s}_*", f"{s}_per_problem.json")):
        for p in json.load(open(f)):
            out[p["id"]] = np.mean(p["correct"])
    return out


def boot(x, n=10000, seed=0):
    x = np.asarray(x)
    i = np.random.default_rng(seed).integers(0, len(x), (n, len(x)))
    m = x[i].mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main(ev, pub):
    rows = {}
    for d in sorted(glob.glob(os.path.join(ev, "*"))) + sorted(glob.glob(os.path.join(pub, "*"))):
        if not glob.glob(os.path.join(d, "parts", "*", "scores.json")):    # no finished job yet: no merged.json
            continue
        name = ("pub:" if d.startswith(pub) else "") + os.path.basename(d)
        m = M.merge(d) if not d.startswith(pub) else json.load(open(os.path.join(d, "merged.json")))
        for s in ("math500", "gsm8k"):
            if s not in m:
                continue
            pp = per_problem(d, s)
            lo, hi = boot(list(pp.values()))
            rows[(name, s)] = dict(m[s], ci=(lo, hi), pp=pp)
    json.dump({f"{k[0]}|{k[1]}": {a: b for a, b in v.items() if a != "pp"} for k, v in rows.items()},
              open(os.path.join(ev, "summary.json"), "w"), indent=1)
    for (name, s), v in sorted(rows.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        print(f"{s:8s} {name:28s} acc {100*v['acc']:5.1f} [{100*v['ci'][0]:4.1f},{100*v['ci'][1]:4.1f}]  cut {100*v['cut_share']:5.1f}"
              f"  tok {v['mean_tokens']:7.0f}  problems {v['problems']}{'' if v['complete'] else ' (partial)'}")
    return rows


def paired(rows, a, b, s="math500"):
    pa, pb = rows[(a, s)]["pp"], rows[(b, s)]["pp"]
    ids = sorted(set(pa) & set(pb))
    d = np.array([pb[i] - pa[i] for i in ids])
    lo, hi = boot(d)
    return len(ids), 100 * d.mean(), 100 * lo, 100 * hi


if __name__ == "__main__":
    ev = sys.argv[1] if len(sys.argv) > 1 else "/home/www/workspace/mathedit/eval"
    pub = sys.argv[2] if len(sys.argv) > 2 else "/home/www/workspace/github/lm_understand-logs/exp8_math/eval"
    rows = main(ev, pub)
    for a, b in [x.split(",") for x in sys.argv[3:]]:
        print(f"paired {b} - {a}:", "n %d  diff %+.1f [%+.1f, %+.1f]" % paired(rows, a, b))
