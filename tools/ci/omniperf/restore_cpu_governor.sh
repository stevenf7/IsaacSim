#!/bin/bash
# Restore the CPU governor saved by set_cpu_governor_performance.sh.
# Called from test-linux-x86_64-omniperf-benchmarks-1-gpu CI job after_script.
# Mirrors restore_cpu_governor_linux in .GTL_app_template_linux_v2.

PREV_GOV=$(cat /tmp/omniperf_prev_governor 2>/dev/null || echo "")
if [ -n "$PREV_GOV" ]; then
    for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        echo "$PREV_GOV" | sudo tee "$cpu" > /dev/null 2>/dev/null || true
    done
    CURRENT=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo "unknown")
    if [ "$CURRENT" = "$PREV_GOV" ]; then
        echo "CPU governor restored to $PREV_GOV successfully"
    else
        echo "WARNING: Failed to restore CPU governor (expected: $PREV_GOV, current: $CURRENT)"
    fi
else
    echo "No previous CPU governor saved, skipping restore"
fi
