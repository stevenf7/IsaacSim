#!/usr/bin/env bash
# setup_sandbox.sh — Configure Claude Code sandbox for Isaac Sim (run once)
#
# This script does two things:
#   1. Installs a GPU-passthrough bwrap wrapper to ~/.local/bin/bwrap
#   2. Checks ~/.claude/settings.json and reports any missing sandbox entries
#
# After running this script, manually add any missing JSON to
# ~/.claude/settings.json (see output), then relaunch Claude Code.

set -euo pipefail

WRAPPER_DEST="$HOME/.local/bin/bwrap"
SETTINGS="$HOME/.claude/settings.json"

# ---------------------------------------------------------------------------
# 1. Check PATH ordering
# ---------------------------------------------------------------------------
echo "=== Checking PATH ==="
local_bin_pos=""
usr_bin_pos=""
idx=0
IFS=: read -ra path_parts <<< "$PATH"
for p in "${path_parts[@]}"; do
  idx=$((idx + 1))
  [[ "$p" == "$HOME/.local/bin" ]] && local_bin_pos=$idx
  [[ "$p" == "/usr/bin" ]]         && usr_bin_pos=$idx
done

if [[ -z "$local_bin_pos" ]]; then
  echo "  WARN: ~/.local/bin is not on PATH at all."
  echo "        Add the following to your ~/.bashrc or ~/.zshrc:"
  echo '          export PATH="$HOME/.local/bin:$PATH"'
elif [[ -n "$usr_bin_pos" && "$local_bin_pos" -gt "$usr_bin_pos" ]]; then
  echo "  WARN: ~/.local/bin (position $local_bin_pos) comes AFTER /usr/bin (position $usr_bin_pos)."
  echo "        The bwrap wrapper won't be picked up by Claude Code."
  echo "        Move ~/.local/bin earlier in PATH in your shell rc file."
else
  echo "  OK  ~/.local/bin is ahead of /usr/bin on PATH."
fi
echo ""

# ---------------------------------------------------------------------------
# 2. Install bwrap wrapper
# ---------------------------------------------------------------------------
echo "=== Installing bwrap wrapper ==="
mkdir -p "$HOME/.local/bin"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WRAPPER_SRC="$SCRIPT_DIR/bwrap_wrapper.sh"

if [[ ! -f "$WRAPPER_SRC" ]]; then
  echo "  ERROR: $WRAPPER_SRC not found. Run this script from the repo."
  exit 1
fi

if [[ -f "$WRAPPER_DEST" ]] && diff "$WRAPPER_SRC" "$WRAPPER_DEST" &>/dev/null; then
  echo "  OK  $WRAPPER_DEST already up to date."
else
  verb="Writing"
  [[ -f "$WRAPPER_DEST" ]] && verb="Updating"
  echo "  $verb $WRAPPER_DEST ..."
  cp "$WRAPPER_SRC" "$WRAPPER_DEST"
  chmod +x "$WRAPPER_DEST"
  echo "  Done."
fi
echo ""

# ---------------------------------------------------------------------------
# 3. Check ~/.claude/settings.json
# ---------------------------------------------------------------------------
echo "=== Checking $SETTINGS ==="

REQUIRED_DISK_WRITES=(
  "~/.cache/packman"
  "~/.local/share/ov"
  "~/.nvidia-omniverse"
  "/dev/nvidia*"
  "/dev/dri/*"
  "/dev/nvidia-caps/*"
  "/tmp/.X11-unix"
)

REQUIRED_NETWORK_HOSTS=(
  "bootstrap.packman.nvidia.com"
  "d4i3qtqj3r0z5.cloudfront.net"
  "urm.nvidia.com"
  "omnipackages.nvidia.com"
  "pdx.s8k.io"
)

missing_disk=()
missing_network=()
sandbox_enabled_ok=false
auto_allow_ok=false

if [[ ! -f "$SETTINGS" ]]; then
  echo "  WARN: $SETTINGS not found — all entries are missing."
  missing_disk=("${REQUIRED_DISK_WRITES[@]}")
  missing_network=("${REQUIRED_NETWORK_HOSTS[@]}")
else
  settings_content=$(cat "$SETTINGS")

  # Check sandbox.enabled
  if echo "$settings_content" | grep -q '"enabled".*true'; then
    sandbox_enabled_ok=true
    echo '  OK  sandbox.enabled: true'
  else
    echo '  ✗   sandbox.enabled: true  (missing or false)'
  fi

  # Check autoAllowBashIfSandboxed
  if echo "$settings_content" | grep -q '"autoAllowBashIfSandboxed".*true'; then
    auto_allow_ok=true
    echo '  OK  sandbox.autoAllowBashIfSandboxed: true'
  else
    echo '  ✗   sandbox.autoAllowBashIfSandboxed: true  (missing or false)'
  fi

  # Check disk write paths
  for path in "${REQUIRED_DISK_WRITES[@]}"; do
    if echo "$settings_content" | grep -qF "\"$path\""; then
      echo "  OK  disk.write: $path"
    else
      echo "  ✗   disk.write: $path  (missing)"
      missing_disk+=("$path")
    fi
  done

  # Check network hosts
  for host in "${REQUIRED_NETWORK_HOSTS[@]}"; do
    if echo "$settings_content" | grep -qF "\"$host\""; then
      echo "  OK  network.allowedHosts: $host"
    else
      echo "  ✗   network.allowedHosts: $host  (missing)"
      missing_network+=("$host")
    fi
  done
fi

echo ""

# ---------------------------------------------------------------------------
# 4. Print instructions if anything is missing
# ---------------------------------------------------------------------------
if [[ ${#missing_disk[@]} -eq 0 && ${#missing_network[@]} -eq 0 && "$sandbox_enabled_ok" == true && "$auto_allow_ok" == true ]]; then
  echo "=== All settings present. Sandbox is fully configured. ==="
  echo ""
  echo "Reminder: relaunch Claude Code for any bwrap changes to take effect."
else
  echo "=== ACTION REQUIRED: Add missing entries to $SETTINGS ==="
  echo ""
  echo "Open $SETTINGS and merge in the following JSON under the top-level object."
  echo "If a 'sandbox' key already exists, merge carefully — don't duplicate keys."
  echo ""
  echo '--------------------------------------------------------------------'
  echo '"sandbox": {'
  echo '  "enabled": true,'
  echo '  "autoAllowBashIfSandboxed": true,'
  echo '  "permissions": {'
  echo '    "disk": {'
  echo '      "write": ['
  for path in "${REQUIRED_DISK_WRITES[@]}"; do
    echo "        \"$path\","
  done
  echo '        ... (keep any existing entries)'
  echo '      ]'
  echo '    },'
  echo '    "network": {'
  echo '      "allowedHosts": ['
  for host in "${REQUIRED_NETWORK_HOSTS[@]}"; do
    echo "        \"$host\","
  done
  echo '        ... (keep any existing entries)'
  echo '      ]'
  echo '    }'
  echo '  }'
  echo '}'
  echo '--------------------------------------------------------------------'
  echo ""
  echo "After editing settings.json, relaunch Claude Code."
fi
