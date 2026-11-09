"""Check the IFEval grader against the author's published results: re-grade every published first sample
(eval/<model>/parts/ifeval_s*of5/ifeval_first_samples.jsonl.gz, thinking on) with evaluate.grade_other and compare with
correct[0] of the same problem in ifeval_per_problem.json.  python analysis/validate_ifeval_grader.py"""
import glob, gzip, json, os, sys
sys.path.insert(0, "/home/www/workspace/mathedit/code")
import evaluate as E
PUB = "/home/www/workspace/github/lm_understand-logs/exp8_math/eval"
bench = {r["id"]: r for r in E.load_set("ifeval")}
tot = agree = 0
for m in ("unedited", "p10c", "p25c", "p50c"):
    n = a = 0
    for d in sorted(glob.glob(f"{PUB}/{m}/parts/ifeval_s*of5")):
        pub = {x["id"]: x["correct"][0] for x in json.load(open(f"{d}/ifeval_per_problem.json"))}
        for l in gzip.open(f"{d}/ifeval_first_samples.jsonl.gz", "rt"):
            s = json.loads(l)
            good = E.grade_other(bench[s["id"]], s["text"], True)[0]
            n += 1
            a += int(good) == pub[s["id"]]
            if int(good) != pub[s["id"]]:
                print("MISMATCH", m, s["id"], "ours", int(good), "published", pub[s["id"]])
    print(m, f"{a}/{n} agree")
    tot += n
    agree += a
print("all", f"{agree}/{tot} agree")
