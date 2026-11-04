#!/usr/bin/env bash
# Push main: SSH first (it goes through the local proxy and is sometimes refused with "Permission denied (publickey)");
# on failure, one HTTPS push with the gh login's credentials (given on the command line only; git config is not changed).
# Exit 0 if main reached GitHub by either route. Call under the lock: tools/git_locked.sh tools/push.sh
U=https://github.com/1099271/exp8-loop-controls.git
timeout 60 git push -q origin main 2>/dev/null && exit 0
G=(git -c credential.helper= -c 'credential.helper=!gh auth git-credential')
timeout 120 "${G[@]}" push -q "$U" main || exit 1
timeout 60 "${G[@]}" fetch -q "$U" +refs/heads/main:refs/remotes/origin/main     # keeps "ahead" in git status correct
echo "$(date '+%F %T') pushed over HTTPS (SSH refused)"
