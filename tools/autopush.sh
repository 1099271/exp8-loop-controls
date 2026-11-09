#!/usr/bin/env bash
# Auto-commit and push results: on every job end / failure / queue swap in logs/queue_*.log (checked every 30 s), and
# every 30 min for in-progress logs. Runs code/summarize.py first (merged.json, eval/summary.json). A failed push is
# retried on the next tick. Shares tools/git_locked.sh's lock with manual commits.
W=/home/www/workspace/mathedit
cd $W
last=""; beat=$(date +%s); retry=0
while true; do
  cur=$(grep -hE "end rc|FAILED|swapped|queue done" logs/queue_*.log 2>/dev/null | md5sum)
  now=$(date +%s)
  if [[ "$cur" != "$last" || $((now - beat)) -ge 1800 ]]; then
    ev=$(grep -hE "end rc|FAILED|swapped|queue done" logs/queue_*.log 2>/dev/null | sort | tail -1)
    [[ "$cur" != "$last" ]] && msg="auto: ${ev}" || msg="auto: progress logs $(date '+%F %T')"
    .venv/bin/python code/summarize.py eval /home/www/workspace/github/lm_understand-logs/exp8_math/eval > /dev/null 2>&1
    flock /tmp/exp8-git.lock bash -c "
      git add eval logs queues PLAN.md 2>/dev/null
      git diff --cached --quiet || git commit -q -m \"$msg

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\"
      tools/push.sh 2>&1 | tail -2" && echo "$(date '+%F %T') ok: $msg"
    last=$cur; beat=$now     # committed; a failed push is retried below without new commits
    git status -sb | head -1 | grep -q ahead && echo "$(date '+%F %T') push pending (will retry)"
  elif git status -sb | head -1 | grep -q ahead && [[ $((now - retry)) -ge 300 ]]; then
    retry=$now
    flock /tmp/exp8-git.lock tools/push.sh 2>&1 | tail -1
    git status -sb | head -1 | grep -q ahead && echo "$(date '+%F %T') push still failing (retry in 5 min)" || echo "$(date '+%F %T') ok: pending commits pushed"
  fi
  sleep 30
done
