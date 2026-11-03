# 相对 <repo>/exp8_math/code/（提交 4d09ba6）的改动

源仓库只读；`code/` 是它的副本，下面列出副本上的全部改动。

## 环境（阶段 0）
- venv：`uv venv .venv --python 3.12`，装了 vllm==0.33.0（自带 torch 2.14.0+cu130）、transformers 5.20.2、datasets 5.1.0、
  math-verify==0.9.0（带 latex2sympy2-extended 1.11.0、antlr4 4.13.2，和 mathqa.py 写的版本一样）、numpy 2.3.5。
  已在装好的 vLLM 里确认 `Qwen3_5ForConditionalGeneration` / `Qwen3_5ForCausalLM` 已注册。
- 模型：`models/base` = Qwen/Qwen3.5-0.8B@2fc06364715b967f1860aea9cf38778875588b17（多模态发布版）；
  `models/p50c` = base 的副本，用 `<repo>/exp8_math/code/apply_edit.py` 重建了 2 个张量（两个都 "hash OK"），
  见 logs/apply_edit_p50c.log。
- HF 数据集缓存放在 `hf_cache/`（运行时设 HF_HOME）；运行时设 PYTHONDONTWRITEBYTECODE=1，避免在源仓库里写 __pycache__。

## code/evaluate.py
1. `REPO = dirname(dirname(dirname(__file__)))` 改为 `REPO = dirname(__file__)`：shim 包 `weightenv/` 放在 code/ 下。
2. `ROOT = "<data>/mathedit"` 改为 `ROOT = "/home/www/workspace/mathedit"`（题库在 $W/bench）。
3. `LLM(...)` 加 `language_model_only=True`（对应 CLI 的 `--language-model-only`）：作者评测用的是 text-only 导出
   （Qwen3_5ForCausalLM），这里加载的是多模态发布版的语言部分。张量名（model.language_model.*）、rope、eos（248044）、
   chat_template.jinja 都和 <repo>/exp8_math/base_model/Qwen3.5-0.8B-text 一致（已逐项对比）。
   max_model_len 沿用原代码 = max_tokens + 2048（think 协议下是 34,816）；gpu_memory_utilization 沿用 EVAL_GPU_MEM（默认 0.85）。

## code/profiles.py
- `ROOT` 同样改成 $W（evaluate.py 不 import 它，改它只是为了一致）。

## 新文件：code/weightenv/ shim
- `weightenv/__init__.py`、`weightenv/lmo/__init__.py`、`weightenv/lmo/tasks/__init__.py`：空文件。
- `weightenv/lmo/tasks/mathqa.py`：把 code/mathqa.py 原样作为 `weightenv.lmo.tasks.mathqa` 暴露（同一个模块对象）。
- `weightenv/lmo/tasks/mcqa.py`：stub。mathqa.py 在 import 时要 `from ...mcqa import loop_signals`，但 mcqa 没有发布；
  数学评测不会调用它。stub 里的 `loop_signals` / `extract` 直接抛 NotImplementedError，所以不会在没人察觉的情况下顶替
  MMLU-Pro / GPQA 的评分（这两个本次不跑）。

## 验证
- `evaluate.py prepare`：math500 500、gsm8k 1319（其余几个集合也生成了，本次不用）。各 10 个分片的题目 id 和顺序与
  <repo>/exp8_math/eval/unedited/parts/{math500,gsm8k}_s*of10/*_per_problem.json 完全一致。
- 用本副本重新评发布的 400 条首样本全文（unedited + p50c 的 math500 各分片）：抽取答案和对错 400/400 一致。
