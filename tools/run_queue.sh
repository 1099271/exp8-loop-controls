#!/usr/bin/env bash
# Runs the jobs of a queue file one by one: each line "<model> <protocol> <set> <shard i/k>" ->
# eval/<model>__<protocol>/parts/<set>_s<i>of<k>/ (the layout of <repo>/exp8_math/eval). A finished job (its set is in
# scores.json with the same _job) is skipped by evaluate.py itself, so the queue can be re-run after a crash.
W=/home/www/workspace/mathedit
cd $W && source .venv/bin/activate
export PYTHONDONTWRITEBYTECODE=1 HF_HOME=$W/hf_cache VLLM_CACHE_ROOT=$W/cache/vllm NLTK_DATA=$W/cache/nltk_data
while read -r model proto set shard; do
  [[ -z "$model" || "$model" == \#* ]] && continue
  i=${shard%/*}; k=${shard#*/}
  out=$W/eval/${model}__${proto}/parts/${set}_s${i}of${k}
  log=$W/logs/${model}__${proto}__${set}_s${i}of${k}.log
  if [[ -f $out/scores.json ]] && grep -q "\"_protocol\"" $out/scores.json; then echo "skip $out"; continue; fi
  echo "$(date '+%F %T') start $model $proto $set $shard"
  t0=$(date +%s)
  python code/evaluate.py run models/$model $out --sets $set --protocol $proto --shard $shard > $log 2>&1
  rc=$?
  echo "$(date '+%F %T') end rc=$rc $(( $(date +%s) - t0 ))s $model $proto $set $shard"
  [[ $rc -ne 0 ]] && echo "FAILED, see $log"
done < "$1"
echo "$(date '+%F %T') queue done $1"
