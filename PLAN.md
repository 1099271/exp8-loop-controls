# 复现与对照评测计划（写于 2026-11-03 14:35 +08:00，E2–E5 尚无任何结果）

对象：RikiyaT/lm_understand-logs（提交 4d09ba6）exp8_math 的 p50c 编辑（Qwen3.5-0.8B，第 15、19 层 mlp.down_proj
各 64 列；作者发布 MATH-500 7.9 % -> 48.1 %，thinking 模式，协议 think35）。

## 问题
提升是 "找到了特殊方向"（A），还是 "任何能打断循环的办法都行"（B）？

## 写这份计划时已知的结果（如实记录，不属于预注册）
- 阶段 1（think35，MATH-500 shard 0/10）：base 5.0 % / cut 95.5 %（发布 7.0 / 95.0）；p50c 43.0 % / cut 34.0 %
  （发布 37.0 / 31.0）。流程和作者对得上。
- E1（nothink35，全量）：MATH-500 base 44.5 %、p50c 44.3 %（配对差 -0.2，95 % 区间 [-2.2, +1.8]）；
  GSM8K base 56.9 %、p50c 54.4 %。
- p50c 编辑的结构：W_S' = W_S - 6 u u^T W_S（两层 alpha 都是 6.00），不是投影去除（alpha = 1）。

## 待跑配置（全部 MATH-500 全量，5 个分片，4 样本/题；队列见 queues/stage2b.txt）
| 名称 | 模型 | 协议 | 改动（相对 think35） |
|---|---|---|---|
| E1b | base, p50c | nothink35_32k | thinking 关，max 32,768（和 thinking 运行同预算） |
| E2 | base, p50c | think35_t10 | temperature 1.0（模型卡 thinking 推荐） |
| E3 | base, p50c | think35_rp110 | repetition_penalty 1.1 |
| E4 | p50c | think35_s1000 | seed 1000（子样本 seed 1000..1003，与 seed 0 的 0..3 不重叠） |
| E5 | rand0 | think35 | 权重：同 64 列、同范数、rank-1，输出方向换成与 u 正交的随机单位向量 |
| E3b | base, p50c | think35_rp105 | repetition_penalty 1.05 |

## 预先固定的判定标准
参照值：p50c think35（作者发布 48.1 %，加上 E4 测得的 seed 波动）。

1. 某个不改权重的配置（E2、E3、E3b 的 base）或 E5 的 rand0，如果 cut_share 大幅下降（比如降到 50 % 以下），
   并且 MATH-500 与 p50c think35 的差值落在 E4 测得的 seed 波动内（或配对差 <= 3 个百分点），就支持 B。
2. 如果这些配置 cut_share 大幅下降，但 MATH-500 仍然明显低于 p50c（配对差的 95 % 区间整体在 -3 以下），
   就支持 A：p50c 的作用不只是打断循环。
3. 如果这些配置的 cut_share 没有明显下降（仍 > 80 %），它们算不上 "打断循环的办法"，对 A/B 不提供证据；
   这时结论只依据 E1 / E1b。
4. E5 单独回答 "方向是否特殊"：rand0 接近 base（cut 仍 > 80 %、acc < 15 %）就说明方向是特殊的；
   rand0 接近 p50c 就说明在这些列上动到这个幅度，换什么方向都行。只有一个随机方向，样本量不够时如实注明。

所有区间都是在题目层面（每题 4 个样本取平均）做 bootstrap 得到的 95 % 区间，配对比较只用同一批题（code/summarize.py）。
时间允许的话，补充 GSM8K 和第二个随机方向（rand1）；这些是计划外的补充，会单独标出。

## 修订 1（2026-11-03 15:19 +0800；应用户要求，由研究会话 lm-understand-logs-02 转达）
修订时已知的计划内结果：E1（全量）、E2 base 的第 1/5 分片（15.2 %，cut 84.5 %）。E1b 的第 1/5 分片正在跑，还没有结果。
E3、E4、E5 都还没有结果。

新的外部信息（本会话已独立核实，数据在 external/hf_akhaliq_eval/，来源和 sha256 见 SOURCE.txt）：
- 作者在 HF 发布了 p50c：RikiyaT/Qwen3.5-0.8B-weight-space-programming（revision d1671a17）。其中 safetensors 的
  LFS sha256 = fd1e42ac…，和本地 models/p50c 逐位相同。
- akhaliq 在这个 checkpoint 上重跑了 MATH-500 全量（think35，seed 0，H200，vLLM 0.33.0，transformers 5.20.2，
  math-verify 0.9.0）：acc 51.0 %，cut 31.6 %，mean_tokens 21,704。与作者发布的 p50c 逐题配对（500 题）：+2.9，
  95 % 区间 [+0.95, +4.80]。权重、协议、seed 都相同，差别只在硬件和 batching，结果相差约 3 个点。

改动：
1. E4（p50c think35_s1000）移到队列最后，改为可选。"48.1 的运行间波动" 先用 akhaliq 和发布值的差（+2.9）来估计；
   这个差来自硬件和 batching 的非确定性，不是换了 seed。E4 如果跑完，以 E4 为准，两者并列报告。
2. 每一轮轮转里 E5（rand0 think35）排第一。
3. E3b（rp 1.05）改为有条件：看 E3（rp 1.1）第 1/5 分片的结果再定。rp 1.1 如果已经打断循环
   （cut < 50 %），而且 acc 没有明显变差（不低于 p50c 在同批题上的发布值减 5 个点），就不跑 E3b；否则把 E3b 插到 E4 前面。
4. 判定标准里的 "参照值" 改为：p50c thinking 记为 48–51 的区间（作者 48.1，akhaliq 51.0）；标准 1 中
   "E4 测得的 seed 波动" 在 E4 没跑的情况下，改用上面这 2.9 个点。其余标准不变。

## 修订 2（2026-11-03 16:44 +0800；事后补充，不属于预注册）
动机：E1b 显示，MATH-500 上 p50c thinking（48–51）和 base non-thinking 的差距，完全来自 8,192 的 token 上限
（base nothink 32k = 49.9）。GSM8K 上同样存在差距（p50c thinking 67.1，base nothink 8k 56.9；8k 时的 cut 为 4.5 %），
所以补跑 GSM8K 的 nothink35_32k（base、p50c 各 5 个分片），插在 E5 第 1/5 分片之后。这一项是看到 E1b 结果后才加的，
报告里单独标注。修订时已知的计划内结果：E1、E1b（全量），E2 base 第 1/5 分片。

## 决策记录：E3b（2026-11-03 21:26 +0800，按修订 1 第 3 条）
E3 第 1/5 分片：base rp1.1 为 20.8 %，cut 77.8 %；p50c rp1.1 为 41.5 %，cut 46.8 %（同批 100 题上，p50c 发布值为 45.0 %）。
不改权重的 base 在 rp1.1 下循环没有被打断（cut 77.8 %，不低于 50 %），不满足 "跳过 E3b" 的条件，所以 E3b（rp 1.05，
base 和 p50c 各 5 个分片）按规则插到 E4 前面（queues/stage2e.txt）。

## 修订 3（2026-11-03 23:43 +0800；用户决定，采用本会话提出的方案 A）
修订时已知的计划内结果（都是部分结果）：E2 base 200 题（16.6 %，cut 82.5 %）、E2 p50c 100 题（25.8 %，cut 70.0 %）、
E3 base 和 p50c 各 100 题（20.8 % / 41.5 %）、E5 rand0 200 题（21.0 %，cut 76.9 %）。E1、E1b 已全量完成。
1. E3b（rp 1.05）只跑 base 的 1 个分片（0/5），用来确认 "惩罚更弱也打断不了循环"；不跑 p50c 的 E3b。
   理由：rp 1.1 没有打断 base 的循环（cut 77.8 %），惩罚更弱的 1.05 不可能打断得更多；修订 1 第 3 条
   原本是为 "rp 1.1 打断了循环但伤了准确率" 准备的，这个情况没有出现。
2. E4（p50c think35，seed 1000，全量）照跑。除了估计 seed 波动，它还是本机上唯一一次 p50c thinking 的全量结果，
   让 E1b 与 p50c 的比较可以在同一台机器、同一套软件上进行。
3. 新增 E5b：第二个随机方向 rand1（make_random_control.py，seed 1；|cos(r0, r1)| = 0.0066），think35，MATH-500 全量。
   用来检验 "方向是特殊的" 是否只是抽到了一个差的随机方向；判定方式与 E5 相同（PLAN 标准 4）。
顺序：E2、E3、E5 剩余轮次 -> E4 -> E5b -> E3b（base 0/5）。
