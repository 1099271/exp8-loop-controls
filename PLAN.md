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
