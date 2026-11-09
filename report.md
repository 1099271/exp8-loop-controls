# Weight-Space Programming 实验 8 的复现与对照评测

对象：[RikiyaT/lm_understand-logs](https://github.com/RikiyaT/lm_understand-logs)（提交 4d09ba6）exp8_math 的 p50c 编辑：
Qwen3.5-0.8B 第 15、19 层 `mlp.down_proj` 各 64 列，共 131,072 个权重，作者发布 MATH-500 从 7.9 % 升到 48.1 %。

完成时间：2026-11-05。硬件：一张 RTX 4090（WSL2）。表格和配对差由 `analysis/final_tables.py` 从 `eval/` 算出（输出见 `analysis/final_tables.txt`），首样本分析和重叠分析见
`analysis/overlap_and_cut.txt`，Gemma 数字来自原仓库的 `merged.json`。

## 1. 结论

**问题：这个提升是 "找到了特殊的方向"，还是 "任何能打断循环的办法都行"？**

**两边都只对一半。**

- **最终分数不特殊。** 不改权重，只把 base 切到 non-thinking 模式（模型卡说的 0.8B 默认模式），token 上限给到同样的 32,768，
  MATH-500 就有 49.9 %。同一台机器上 p50c thinking 是 51.3 %，配对差 +1.5 [−1.3, +4.2]，差异不显著。
- **方向是特殊的。** 在 thinking 模式下，这里试过的其他办法都没能打断大部分循环。两个同范数随机方向只有 23.3 % 和 10.7 %，
  调温度、加重复惩罚只到 18–23 %；p50c 比它们高 28–41 个点。
- **这两点不矛盾。** 能绕开循环的办法确实能拿到差不多的分，但这次试过的办法里，只有 p50c 能在 thinking 模式内部做到。

**作者已经说过提升来自循环。** 博客正文写道："Fixing loops, however, is not the same as making a model better at math: it lets the
model finish answers it could already work out."；讲 IFEval 时也写了 "The loops are not special to math, so performance beyond
math improved as well"。所以这份报告是**补充而不是反驳**。博客全文没有提到 non-thinking，
也没有采样调整或随机方向这类对照，这些是本报告新增的内容。摘要和正文的措辞不同，见 4.4。

**有一个例外：GSM8K。** p50c thinking（67.1 %，作者发布）比 base non-thinking 32k（56.9 %）高 10.2 [+8.1, +12.3]，token 上限解释不了。

## 2. 结果总表

95 % 区间是在题目层面 bootstrap 得到的。`cut` = 跑满 token 上限的样本比例。MATH-500 每题 4 个样本，GSM8K 每题 2 个样本。

| 实验 | 模型 | 模式与采样（未注明的同 think35） | MATH-500 acc | cut % | 平均 token | GSM8K acc | 题数 |
|---|---|---|---|---|---|---|---|
| 作者发布 | base | thinking，t=0.6 | 7.9 [6.0, 9.8] | 93.0 | 30,868 | 13.8 | 500 / 1319 |
| 作者发布 | p50c | thinking，t=0.6 | 48.1 [44.3, 51.8] | 33.1 | 22,037 | 67.1 | 500 / 1319 |
| 他人重跑 | p50c | thinking，t=0.6，H200（akhaliq） | 51.0 | 31.6 | 21,704 | – | 500 |
| 阶段 1 | base | thinking，t=0.6，shard 0/10（作者同分片 7.0 / 95.0 / 31,331） | 5.0 [1.0, 10.5] | 95.5 | 31,463 | – | 50 |
| 阶段 1 | p50c | thinking，t=0.6，shard 0/10（作者同分片 37.0 / 31.0 / 23,043） | 43.0 [32.0, 54.5] | 34.0 | 23,564 | – | 50 |
| **E4** | p50c | thinking，t=0.6，seed 1000 | **51.3 [47.8, 54.9]** | 32.4 | 22,011 | – | 500 |
| E1 | base | non-thinking，8k | 44.5 [41.2, 48.1] | 30.4 | 3,661 | 56.9 [54.7, 59.2] | 500 / 1319 |
| E1 | p50c | non-thinking，8k | 44.3 [40.9, 47.7] | 32.0 | 3,836 | 54.4 [52.2, 56.6] | 500 / 1319 |
| **E1b** | base | non-thinking，32k | **49.9 [46.5, 53.3]** | 11.7 | 7,697 | 56.9 [54.6, 59.2]* | 500 / 1319 |
| E1b | p50c | non-thinking，32k | 50.1 [46.9, 53.4] | 0.35 | 6,219 | 54.9 [52.6, 57.1]* | 500 / 1319 |
| E2 | base | thinking，t=1.0 | 18.1 [15.4, 21.0] | 81.2 | 29,472 | – | 500 |
| E2 | p50c | thinking，t=1.0 | 28.0 [24.6, 31.4] | 67.5 | 27,220 | – | 500 |
| E3 | base | thinking，rp=1.1 | 23.3 [20.4, 26.3] | 75.0 | 27,112 | – | 500 |
| E3 | p50c | thinking，rp=1.1 | 42.8 [39.3, 46.2] | 42.3 | 22,825 | – | 500 |
| E3b | base | thinking，rp=1.05，shard 0/5 | 14.5 [9.5, 20.2] | 85.2 | 29,372 | – | 100 |
| E5 | rand0 | thinking，t=0.6 | 23.3 [20.5, 26.2] | 75.5 | 26,978 | – | 500 |
| E5b | rand1 | thinking，t=0.6 | 10.7 [8.9, 12.6] | 89.2 | 30,362 | – | 500 |

\* 看到 E1b 的 MATH-500 结果之后才加的事后补充（PLAN 修订 2）。

## 3. 每项一句结论

配对差是同一批题上的差值，单位是百分点。

- **阶段 1（自检）：** 流程和作者对得上，cut 和平均 token 几乎相同；base 的 cut 接近 0.9，p50c 远低于它。
- **E1（non-thinking，8k）：** base 自己就有 44.5 %，编辑在这个模式下没有效果（−0.2 [−2.2, +1.8]）。
- **E1b（non-thinking，32k）：** 上限放宽后 base 涨到 49.9 %（+5.3 [+3.6, +7.1]），追平 p50c thinking；E1 里剩下的差距来自 8k 上限。
- **E1b 里的编辑：** 打断了 non-thinking 下残余的循环（cut 11.7 % → 0.35 %），但 MATH-500 分数不变（+0.3 [−1.9, +2.5]），GSM8K 略降（−2.1 [−4.1, −0.1]）。
- **E2（温度 1.0）：** base 只到 18.1 %，cut 仍有 81.2 %；p50c 掉到 28.0 %（与 E4 差 −23.4 [−26.2, −20.6]），但仍比同温度的 base 高 +9.8 [+7.8, +11.8]。
- **E3（rp 1.1）：** base 只到 23.3 %，cut 75.0 %；p50c 降到 42.8 %（与 E4 差 −8.6 [−10.7, −6.4]）。
- **E3b（rp 1.05，100 题）：** 惩罚更弱，效果更差：14.5 %，cut 85.2 %，比同批题上的 rp 1.1 低 −6.2 [−10.0, −2.8]。
- **E4（p50c 换 seed）：** 51.3 %。和 akhaliq 没有差别（+0.3 [−1.6, +2.2]），但比作者发布值高（+3.2 [+1.3, +5.1]）。
- **E5 / E5b（随机方向）：** 同列、同范数的两个随机方向差别很大（rand0 比 rand1 高 +12.6 [+10.4, +14.8]），都远低于 p50c（E4 比它们高 +28.0 [+25.2, +30.9] 和 +40.6 [+37.5, +43.7]）。

## 4. 回答开头的问题

### 4.1 证据

| 比较（MATH-500，500 题） | 配对差 [95 %] | 含义 |
|---|---|---|
| E4 − base non-thinking 32k（同机） | +1.5 [−1.3, +4.2] | 差异不显著 |
| 作者发布 p50c − base non-thinking 32k | −1.8 [−4.4, +0.9] | 差异不显著 |
| akhaliq p50c − base non-thinking 32k | +1.1 [−1.6, +3.9] | 差异不显著 |
| E4 − rand0 | +28.0 [+25.2, +30.9] | 方向重要 |
| E4 − rand1 | +40.6 [+37.5, +43.7] | 方向重要 |
| E4 − base rp 1.1 | +28.0 [+25.2, +30.6] | 采样调整比不上编辑 |
| E4 − base t=1.0 | +33.1 [+30.1, +36.1] | 采样调整比不上编辑 |

作者自己的 Gemma 后续实验指向同一方向：模型本来很少循环时，Astra 改不动它（lenient 分数：未编辑 6.8 %，编辑后 7.0–7.7 %）。

### 4.2 对照预先固定的判定标准（`PLAN.md`，写于 E1b–E5 出结果之前）

- **标准 1（支持 "任何办法都行"）：不满足。** 没有哪个不改权重的 thinking 配置，或随机方向，把 cut 降到 50 % 以下。
- **标准 2（支持 "方向特殊"）：不适用。** 它的前提是这些配置已经大幅打断循环，实际没有发生。
- **标准 3（cut 仍 > 80 %，不算打断循环的办法）：** 适用于 t=1.0（81.2 %）、rp 1.05（85.2 %）和 rand1（89.2 %）。
- **灰色地带：** rp 1.1（75.0 %）和 rand0（75.5 %）落在 50–80 % 之间，标准没有覆盖这种情况。
- **标准 4（方向是否特殊）：** rand1（10.7 %，cut 89.2 %）符合 "接近 base"；rand0（23.3 %，cut 75.5 %）既不接近 base 也不接近 p50c。

所以 "方向特殊" 是根据配对差值下的判断，**不是预注册标准直接判出的结果**。标准 3 还规定，这种情况下对 A/B 的结论只依据 E1 / E1b，
也就是 4.1 表的前三行。

### 4.3 哪些说法成立，哪些不成立

**可以说：**
- MATH-500 从 7.9 % 到 48–51 % 的提升，大小和 base 切到 non-thinking 能拿到的分数相当。
- 把这次编辑放到 non-thinking 模式里，MATH-500 没有提升，所以没有证据表明它给模型增加了数学能力。这和作者的说法一致。
- 在 thinking 模式下，这个方向明显优于这里试过的两个随机方向和几种采样调整。
- p50c 的效果对采样设置敏感。

**不能说：**
- "作者挑了对自己有利的温度"：0.6 是模型卡 thinking 测评表的设置，1.0 是模型卡对文本任务的通用推荐，两个都出自模型卡。
- "Astra 在 0.6 下练习，所以 p50c 只在 0.6 下有效"：这个因果关系没有测试过。
- "编辑毫无价值"：它在 thinking 模式下确实有效，GSM8K 上也有 non-thinking 拿不到的分数。
- "base 和 p50c 一样好"：两者的分数差异不显著，但逐题相关只有 0.72（同一模型两次运行是 0.86），答对的题并不完全相同。

### 4.4 摘要和正文的措辞

博客摘要原文（2026-11-09 下载的页面，`external/web/`）：

> Astra identifies an issue in its weights causing reasoning loops that Qwen's own model card warns about, and fixes this by
> natively editing 0.016% of the weights. With the same sampling settings, this weight correction raises MATH-500 from 7.9% to
> 48.1% and generalizes out of the box to instruction following, raising IFEval by 3x.

| 内容 | 摘要 | 正文 |
|---|---|---|
| 提升和循环有关 | 写了（"causing reasoning loops"） | 写了 |
| 修好循环不等于数学变强 | 没写 | 写了（Gemma 一节开头："Fixing loops, however, is not the same as making a model better at math"） |
| IFEval 的提升 | "generalizes out of the box to instruction following" | "The loops are not special to math, so performance beyond math improved as well" |
| non-thinking 基线 | 没写 | 没写 |

- **"With the same sampling settings" 本身没有问题。** base 和 p50c 确实用了同一套设置。本报告补的是换设置之后的结果
  （温度 1.0 时 p50c 降到 28.0 %），不能说这句话本身有误导。
- **差别在 "generalizes" 这个词。** 正文把 IFEval 的提升归因到循环，摘要写成了 "泛化到指令遵循"。
  IFEval 的 non-thinking 基线见第 4.6 节（E6）。
- **摘要只读一遍容易得出的印象**，是编辑让模型的数学和指令遵循能力变强了。正文和本报告的数据都不支持这个印象。

### 4.5 和 Honnibal 评论的关系

Matthew Honnibal（spaCy 作者）2026-11-03 发了一篇评论，标题是 "The 'Astra can read and write weights to improve Qwen' post is
misleading"（<https://honnibal.dev/blog/astra-read-write-misleading>，2026-11-09 下载的页面在 `external/web/`）。

他的观点：
- 摘要开头是 "Just by looking at the raw weights"，但只有实验 1、2、4 是只看原始权重（不用 Python、不运行网络，1.7 万–17.2 万个权重）。
- 实验 8 要写 Python，还能 "run the model on up to 50 batches of practice problems"。
- 所以实验 8 说明的是 "Astra can be prompted to devise and perform tasks that a human ML engineer could do"。他也承认
  "AI models of a year or two ago would have failed at all these tasks"。
- 用 Python 的实验 "don't belong in the same post or paper" 和只读权重的实验放在一起，因为 "it's not a single technique"。

他没有重跑实验，也没有质疑任何数字；没有提到 non-thinking、采样设置或随机方向。

| | Honnibal | 本报告 |
|---|---|---|
| 问的问题 | 这些实验能不能说明同一种能力 | 实验 8 的提升相对什么基线，是否依赖这个方向 |
| 方法 | 按博客自己报告的设置重新分类 | 在本机实测 |
| 对实验 8 的结论 | 是工程师式的工作流（Python + 运行模型） | 最终分数不超过 base non-thinking；方向在 thinking 模式下是特殊的 |

两者**互补，不冲突**。"方向特殊" 对作者有利，Honnibal 的文章也没有否认这一点。
本报告只核对了他表格第 8 行的两项：作者日志里 p50c 的运行有 80 次 Python 调用、69 次前向调用，和 "Python: Yes / Runs network: Yes" 一致。
其余行没有核对。

## 5. 哪些结论样本量或设计不够

- **随机方向只有 2 个。** 两者差 12.6 个点，说不出随机方向的典型水平或分布。可以说 "这两个都远低于 p50c"，不能说 "随机方向一般能拿到多少"。
- **GSM8K 的差距无法归因。** thinking 模式下没有哪种不改权重的办法打断了循环，所以这 10 个点是这个方向独有的，还是任何能让 thinking 正常结束的办法都能拿到，这里回答不了。
  另外本机没有跑 GSM8K 的 thinking，这个差值是跨环境比较。
- **E3b 只有 100 题，** 只够确认方向（惩罚更弱，效果更差）。
- **阶段 1 只有 50 题，** 本机 base thinking 没有全量。7.9 % 这个起点来自作者的环境。
- **"差异不显著" 不等于相等。** 区间上限 +4.2 没有排除 p50c 略高几个点。
- **约 3 个点的环境差异没有查明。** 作者（text-only 导出，vLLM 版本日志没写）是 48.1，两次重跑（vLLM 0.33.0，多模态发布版）是 51.0、51.3。这里分不出是软件版本、导出方式还是别的原因。
- **两种模式的比较有局限。** non-thinking 和 thinking 的 presence penalty 相同（1.5），但 temperature（0.7 对 0.6）、top_p（0.8 对 0.95）都不同，所以这里比的是 "两套设置"，不只是模式。
- **没有做多重比较校正。** 这份报告有二十多个配对比较。主要结论的差值都很大或明显不显著，受影响的是接近边界的项，比如 GSM8K 的 −2.1 [−4.1, −0.1]。
- **采样调整只试了少数几个取值，** 不能说 "所有采样设置都打断不了循环"。
- **首样本分析样本小且是近似判断。** 作者只发布了每个分片前 20 题的首样本全文（每个配置 200 条，README 写的是 "每道题"）。
  按有没有 `</think>` 近似判断是否写完：base 写完的 13 条 MATH-500 全部答对，p50c 写完的 152 条答对 60.5 %；这很可能是选择效应（base 只写得完简单题）。
  被截断回答对分数贡献很小（base 的正确回答里约 13 %，p50c 是 0）。
- **推文原文没有核对。** 本机读不到 X 的内容，发评论前要核对它的具体措辞。

## 6. 和原计划的差异

- **E1b 是计划外新增的。** 因为 E1 里 30 % 的回答撞到 8k 上限，所以补了一组 32k。这项写进了预注册计划。
- **GSM8K 的 E1b 是事后补充**（修订 2），其他 thinking 配置没有跑 GSM8K。
- **E3b 缩减为 base 的 1 个分片，新增 E5b（rand1）**（修订 3，用户决定）。
- **E4 用 seed 1000 而不是 1：** vLLM 给 n 个样本的 seed 是 seed+i，seed 1 会和 seed 0 重用三组随机数流。
- **vLLM 用 0.33.0。** 没查到确切的最低支持版本，装了当时的最新稳定版，并确认架构已注册。
- **E5 的随机改动怎么构造：** 从 p50c 的改动 Δ = σ·u·vᵀ 出发，保留 σ、v 和列，把输出方向 u 换成与两层 u 都正交的随机单位向量 r。没有用 "W − c·r·rᵀ·W" 的形式，
  因为随机方向上的分量很小，要匹配范数需要极大的系数。这种构造保证每一列的改动幅度和 p50c 一样。
- **p50c 的实际形式：** 两层都是 W_S' = W_S − 6·u·uᵀ·W_S（系数 6.00），也就是把这些列在 u 上的分量反号并放大 5 倍，而不是去除（系数 1）。

代码改动见 `CHANGES.md`，计划与修订见 `PLAN.md`，时间线见 git 历史。

## 7. 过程中更正过的判断

这些在中途说错过，这里统一记录，**不要在后续写作中沿用**：

| 当时的说法 | 实际情况 |
|---|---|
| 3 个点的差是硬件和 batching 造成的 | 没有根据，见第 5 节 |
| 温度 1.0 才是 "模型卡推荐"，0.6 不是 | 两个都出自模型卡 |
| rp 1.1 对 p50c 影响不大 | 这是 100 题时的判断，全量差异显著 |
| 随机方向能拿回约三分之一的提升 | 只对 rand0 成立，rand1 几乎没有效果 |
| 标准 4 下 "方向特殊" 成立 | 只有 rand1 符合；这是配对差值下的判断 |
| 把提升来自循环当成新发现 | 作者的博客正文已经这样写了；摘要只提到循环，没有 "Fixing loops..." 这句限定（见 4.4） |

## 8. 文件

- `eval/<模型>__<协议>/parts/<集合>_s<i>of<k>/`：每个配置的 `scores.json`、`*_per_problem.json`、`*_first_samples.jsonl`，格式同原仓库；`merged.json` 由 `code/merge.py` 合并。
- `analysis/`：`final_tables.py`（总表和配对差）、`overlap_and_cut.py`（逐题重叠、截断计分）。
- `external/hf_akhaliq_eval/`：akhaliq 重跑的分数文件（Apache-2.0），附来源和哈希。
- `external/web/`：博客和 Honnibal 评论的页面存档（HTML 和提取出的纯文本）。
- `provenance/`：系统和包版本、权重与题库的 sha256、p50c / rand0 / rand1 的构建日志。
- `logs/`、`queues/`：每个任务的完整日志和实际运行的队列。

## 9. 来源

- 博客：<https://rikiyat.github.io/blog/weight-space-programming/>（原文引用已对照 2026-11-04 和 2026-11-09 下载的页面文本；2026-11-09 的页面存在 `external/web/`，sha256 a326bc5b…）
- Honnibal 的评论：<https://honnibal.dev/blog/astra-read-write-misleading>（2026-11-03；页面存在 `external/web/`，sha256 06362124…）
- 日志仓库：<https://github.com/RikiyaT/lm_understand-logs>（提交 4d09ba6）
- HF checkpoint 与 akhaliq 重跑：<https://huggingface.co/RikiyaT/Qwen3.5-0.8B-weight-space-programming>
- Qwen 模型卡：<https://huggingface.co/Qwen/Qwen3.5-0.8B>
