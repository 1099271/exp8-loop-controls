#!/usr/bin/env bash
# when the running stage-2 job ends, stop the old queue before the next job gets far and start stage2b
W=/home/www/workspace/mathedit
n=$(grep -c "end rc" $W/logs/queue_stage2.log)
until [ $(grep -c "end rc" $W/logs/queue_stage2.log) -gt $n ]; do sleep 2; done
tmux kill-session -t stage2; sleep 5; pkill -f "code/evaluate.py run" ; sleep 10
echo "$(date '+%F %T') swapped to stage2b" >> $W/logs/queue_stage2.log
tmux new-session -d -s stage2b "cd $W && ./tools/run_queue.sh queues/stage2b.txt 2>&1 | tee -a logs/queue_stage2b.log"
