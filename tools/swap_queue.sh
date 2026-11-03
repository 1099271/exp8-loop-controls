#!/usr/bin/env bash
# usage: swap_queue.sh <old tmux session> <new queue name>   (queues/<name>.txt, logs/queue_<name>.log, session <name>)
# when the old queue's running job ends, stop the old queue before the next job gets far and start the new one;
# finished jobs are skipped by run_queue.sh / evaluate.py, a job killed while loading has written nothing.
W=/home/www/workspace/mathedit; old=$1; new=$2
n=$(grep -c "end rc" $W/logs/queue_$old.log)
until [ $(grep -c "end rc" $W/logs/queue_$old.log) -gt $n ]; do sleep 2; done
tmux kill-session -t $old; sleep 5; pkill -f "code/evaluate.py run"; sleep 10
echo "$(date '+%F %T') swapped to $new" >> $W/logs/queue_$old.log
tmux new-session -d -s $new "cd $W && ./tools/run_queue.sh queues/$new.txt 2>&1 | tee -a logs/queue_$new.log"
