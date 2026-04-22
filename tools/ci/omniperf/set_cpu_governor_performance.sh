#!/bin/bash
# Save current CPU governor and switch all CPUs to "performance" for benchmarking.
# Called from test-linux-x86_64-omniperf-benchmarks-1-gpu CI job.
# Mirrors set_cpu_governor_performance_linux in .GTL_app_template_linux_v2.

cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor > /tmp/omniperf_prev_governor 2>/dev/null || true
PREV=$(cat /tmp/omniperf_prev_governor 2>/dev/null || echo "unknown")
echo "Previous CPU governor: $PREV"
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    echo "performance" | sudo tee "$cpu" > /dev/null 2>/dev/null || true
done
CURRENT=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo "unknown")
if [ "$CURRENT" = "performance" ]; then
    echo "CPU governor set to performance successfully"
else
    echo "WARNING: Failed to set CPU governor (current: $CURRENT)"
fi
