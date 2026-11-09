"""Every number of report.md: per-config scores recomputed from the parts, coverage checks, paired differences
(problem-level bootstrap, 10,000 draws, seed 0), per-problem correlations.   python analysis/final_tables.py"""
import glob, json, os
import numpy as np

W = "/home/www/workspace/mathedit/"
P = "/home/www/workspace/github/lm_understand-logs/exp8_math/eval/"
CFG = {"base think35 t0.6 (pub)": (P + "unedited", "pub"), "p50c think35 t0.6 (pub)": (P + "p50c", "pub"),
       "local base think35 (E0 math 0/10, E6d ifeval 0/5)": (W + "eval/base__think35", ""), "local p50c think35 (E0 math 0/10, E6c ifeval)": (W + "eval/p50c__think35", ""),
       "E1 base nothink 8k": (W + "eval/base__nothink35", ""), "E1 p50c nothink 8k": (W + "eval/p50c__nothink35", ""),
       "E1b base nothink 32k": (W + "eval/base__nothink35_32k", ""), "E1b p50c nothink 32k": (W + "eval/p50c__nothink35_32k", ""),
       "E2 base t1.0": (W + "eval/base__think35_t10", ""), "E2 p50c t1.0": (W + "eval/p50c__think35_t10", ""),
       "E3 base rp1.1": (W + "eval/base__think35_rp110", ""), "E3 p50c rp1.1": (W + "eval/p50c__think35_rp110", ""),
       "E3b base rp1.05 (shard 0/5)": (W + "eval/base__think35_rp105", ""),
       "E4 p50c seed1000": (W + "eval/p50c__think35_s1000", ""), "E5 rand0": (W + "eval/rand0__think35", ""), "E5b rand1": (W + "eval/rand1__think35", "")}


def pp(d, s):
    out, n = {}, 0
    for f in glob.glob(f"{d}/parts/{s}_*/{s}_per_problem.json"):
        for p in json.load(open(f)):
            assert p["id"] not in out, p["id"]
            out[p["id"]] = np.mean(p["correct"]); n += len(p["correct"])
    return out, n


def agg(d, s):
    a = {"ok": 0, "total": 0, "cut": 0, "tokens_sum": 0, "n": 0, "inst_ok": 0, "inst_total": 0}
    for f in glob.glob(f"{d}/parts/{s}_*/scores.json"):
        v = json.load(open(f)).get(s)
        if v:
            for k in ("ok", "total", "cut", "tokens_sum", "inst_ok", "inst_total"):
                a[k] += v.get(k, 0)
            a["n"] += v["n_problems"]
    return a


def boot(x):
    x = np.asarray(x); m = x[np.random.default_rng(0).integers(0, len(x), (10000, len(x)))].mean(1)
    return 100 * x.mean(), 100 * np.percentile(m, 2.5), 100 * np.percentile(m, 97.5)


D = {}
for s in ("math500", "gsm8k", "ifeval"):
    print(f"== {s}: config | acc [95 %] | cut | mean tokens | problems (checks)")
    for k, (d, _) in CFG.items():
        a = agg(d, s)
        if not a["total"]:
            continue
        x, n = pp(d, s); D[(k, s)] = x
        assert n == a["total"] and len(x) == a["n"], k
        assert abs(sum(x.values()) * a["total"] / len(x) - a["ok"]) < 1e-6, k
        m, lo, hi = boot(list(x.values()))
        print(f"{k:30s} {m:5.1f} [{lo:4.1f},{hi:4.1f}] {100*a['cut']/a['total']:5.1f} {a['tokens_sum']/a['total']:8.0f} {a['n']:5d}"
              + (f"  inst-level {100*a['inst_ok']/a['inst_total']:.1f}" if a['inst_total'] else ""))
ak = {p["id"]: np.mean(p["correct"]) for p in json.load(open(W + "external/hf_akhaliq_eval/scores_edited_math500.json"))["per_problem"]}
D[("akhaliq p50c", "math500")] = ak


def pr(a, b, s="math500"):
    A, B = D[(a, s)], D[(b, s)]; ids = sorted(set(A) & set(B))
    m, lo, hi = boot([A[i] - B[i] for i in ids])
    x, y = np.array([A[i] for i in ids]), np.array([B[i] for i in ids])
    print(f"{a:28s} - {b:28s} n={len(ids):4d} {m:+6.1f} [{lo:+5.1f},{hi:+5.1f}]  ({100*x.mean():.1f} vs {100*y.mean():.1f}) r={np.corrcoef(x,y)[0,1]:.3f}")


print("== paired, MATH-500")
E4, BN, PN = "E4 p50c seed1000", "E1b base nothink 32k", "E1b p50c nothink 32k"
for a, b in [(E4, BN), ("p50c think35 t0.6 (pub)", BN), ("akhaliq p50c", BN), (E4, "p50c think35 t0.6 (pub)"), (E4, "akhaliq p50c"), ("akhaliq p50c", "p50c think35 t0.6 (pub)"),
             (BN, "E1 base nothink 8k"), (PN, "E1 p50c nothink 8k"), ("E1 p50c nothink 8k", "E1 base nothink 8k"), (PN, BN),
             (E4, "E5 rand0"), (E4, "E5b rand1"), ("E5 rand0", "E5b rand1"), ("E5 rand0", "base think35 t0.6 (pub)"), ("E5b rand1", "base think35 t0.6 (pub)"),
             ("E2 base t1.0", "base think35 t0.6 (pub)"), ("E2 p50c t1.0", E4), ("E2 p50c t1.0", "E2 base t1.0"), (E4, "E2 base t1.0"),
             ("E3 base rp1.1", "base think35 t0.6 (pub)"), ("E3 p50c rp1.1", E4), ("E3 p50c rp1.1", "E3 base rp1.1"), (E4, "E3 base rp1.1"), ("E3 base rp1.1", "E5 rand0"),
             ("E3b base rp1.05 (shard 0/5)", "E3 base rp1.1"), ("E3b base rp1.05 (shard 0/5)", "base think35 t0.6 (pub)")]:
    pr(a, b)
print("== paired, GSM8K")
for a, b in [("p50c think35 t0.6 (pub)", BN), ("p50c think35 t0.6 (pub)", PN), (PN, BN), ("E1 p50c nothink 8k", "E1 base nothink 8k"), (BN, "E1 base nothink 8k")]:
    pr(a, b, "gsm8k")
print("== paired, IFEval (E6, amendment 4)")
LB, LP = "local base think35 (E0 math 0/10, E6d ifeval 0/5)", "local p50c think35 (E0 math 0/10, E6c ifeval)"
for a, b in [(BN, "p50c think35 t0.6 (pub)"), (BN, LP), (PN, BN), (LP, "p50c think35 t0.6 (pub)"), ("p50c think35 t0.6 (pub)", "base think35 t0.6 (pub)"),
             (BN, "base think35 t0.6 (pub)"), (LB, "base think35 t0.6 (pub)"), (PN, LP)]:
    if (a, "ifeval") in D and (b, "ifeval") in D:
        pr(a, b, "ifeval")
