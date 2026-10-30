#!/bin/bash
# Non-intrusive monitor for the ACTIVE H3 training run (PID 14528).
# Polls liveness + epoch count every 5 min; exits when the process exits.
# READ-ONLY: touches nothing, launches nothing.
EXP="D:/Softfors/jup/experiments/h3_kub_localizer_sigma_adaptive_sizeaware_seed42_clean_v3"
PID=14528
for i in $(seq 1 144); do   # safety cap 144 polls * 300s = 12h
  alive=$(powershell -NoProfile -Command "[bool](Get-Process -Id $PID -ErrorAction SilentlyContinue)" 2>/dev/null | tr -d '\r')
  rows=$(($(wc -l < "$EXP/history.csv" 2>/dev/null || echo 1) - 1))
  echo "$(date '+%Y-%m-%d %H:%M:%S') alive=$alive epochs=$rows"
  if [ "$alive" != "True" ]; then
    echo "=== H3 TRAINING PROCESS EXITED at $(date '+%Y-%m-%d %H:%M:%S') ==="
    echo "--- training.log tail ---"
    tail -8 "$EXP/training.log"
    echo "--- registry tail ---"
    tail -1 "D:/Softfors/jup/experiments/registry.csv"
    exit 0
  fi
  sleep 300
done
echo "=== MONITOR SAFETY CAP REACHED (12h) — process still alive? ==="
powershell -NoProfile -Command "[bool](Get-Process -Id $PID -ErrorAction SilentlyContinue)" | tr -d '\r'
