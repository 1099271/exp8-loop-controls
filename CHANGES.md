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

## IFEval（2026-11-09，修订 4，用户批准补跑）
- 新文件 `code/instruction_following_eval/`：Google 官方 IFEval 评分器（google-research 提交 0eebfd40 的
  instructions.py、instructions_registry.py、instructions_util.py，未改动；LICENSE 为 Apache-2.0）。
- 新文件 `code/weightenv/lmo/tasks/ifevalg.py`：shim，把作者 import 的 `weightenv.lmo.tasks.ifevalg` 指向上面的官方包。
  evaluate.py 的 `grade_other` 没改。
- 新文件 `tools/prepare_ifeval.py`：从 `external/ifeval_official/input_data.jsonl`（同一提交，541 题）生成
  bench/ifeval.jsonl，保持文件顺序。各分片题号和作者发布的 ifeval_s*of5 完全一致。sha256 见 external/ifeval_official/SHA256SUMS。
- venv 新装：absl-py、langdetect、nltk 3.10.4、immutabledict（官方 requirements.txt 列的 4 个）。nltk 数据 punkt / punkt_tab
  从 nltk_data 的 gh-pages 手动下载到 cache/nltk_data（nltk.download 被本机代理拦了），zip 的 sha256：punkt 51c30789…，
  punkt_tab e57f6418…。nltk 3.10 读 `punkt/english.pickle` 时实际用的是 punkt_tab。
- `tools/run_queue.sh`：加了 `NLTK_DATA=$W/cache/nltk_data`。
- 验证：`analysis/validate_ifeval_grader.py` 重判作者发布的 400 个 IFEval 首样本（unedited、p10c、p25c、p50c），
  和作者逐题结果 400/400 一致；其中 166 个判对，233 个写完了 `</think>`。
