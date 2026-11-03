"""E5 (reproduction): random-direction control for p50c.

p50c's edit of each of layers 15 / 19 mlp.down_proj (shape 1024 x 3584) is, up to bfloat16 rounding, rank one on 64
columns S: D = W_p50c - W_base = s1 * u v^T (u: a unit 1,024-d output direction, v: unit weights over the columns S;
measured: second singular value / first = 0.0006; the edit is W_S - 6 u u^T W_S). The control keeps s1 and v (the same
columns, the same per-column magnitudes, the same Frobenius norm) and replaces u by a random unit vector r that is
orthogonal to both layers' u (one r for both layers, as p50c's two u nearly coincide, |cos| = 0.85).

    python make_random_control.py <base dir> <p50c dir> <out dir> [seed]
<out dir> must be a copy of the base model folder; its safetensors file is rewritten.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import st_numpy as S  # noqa: E402

F = "model.safetensors-00001-of-00001.safetensors"
NAMES = [f"model.language_model.layers.{l}.mlp.down_proj.weight" for l in (15, 19)]


def main(base, p50c, out, seed=0):
    tb = S.load(os.path.join(base, F))
    te = S.load(os.path.join(p50c, F), NAMES)
    parts = {}
    for n in NAMES:
        W = S.bf16_to_f32(tb[n][1]).astype(np.float64)
        D = S.bf16_to_f32(te[n][1]).astype(np.float64) - W
        cols = np.where(np.abs(D).sum(0) > 0)[0]
        U, s, Vt = np.linalg.svd(D[:, cols], full_matrices=False)
        parts[n] = (W, cols, U[:, 0], s[0], Vt[0])
    us = np.stack([p[2] for p in parts.values()], 1)            # 1024 x 2
    r = np.random.default_rng(seed).standard_normal(1024)
    q, _ = np.linalg.qr(us)
    r -= q @ (q.T @ r)
    r /= np.linalg.norm(r)
    report = {"seed": seed, "tensors": []}
    for n, (W, cols, u, s1, v) in parts.items():
        Wn = W.copy()
        Wn[:, cols] += s1 * np.outer(r, v)
        bits = S.bf16_bits(Wn.astype(np.float32)).reshape(W.shape)
        tb[n] = ("BF16", bits)
        Dr = S.bf16_to_f32(bits).astype(np.float64) - W
        sv = np.linalg.svd(Dr[:, cols], compute_uv=False)
        rec = {"name": n, "columns": cols.tolist(), "p50c_norm": float(s1), "control_norm": float(np.linalg.norm(Dr)),
               "control_s2_over_s1": float(sv[1] / sv[0]), "cos_r_u": float(abs(r @ u)),
               "outside_columns_changed": int((np.abs(np.delete(Dr, cols, 1)) > 0).sum())}
        report["tensors"].append(rec)
        print(json.dumps({k: v for k, v in rec.items() if k != "columns"}))
    S.save(os.path.join(out, F), tb, {"format": "pt"})
    json.dump(report, open(os.path.join(out, "random_control.json"), "w"), indent=1)
    print("->", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 0)
