# Isaac Sim — Claude Code Guide

At the start of every conversation, read the following in full to load all project rules and skills:

- All `*.mdc` files in `.cursor/rules/`
- All `SKILL.md` files in `.cursor/skills/` (search recursively)

## Sandbox Setup (recommended, run once)

Claude Code's sandbox needs GPU device access and network/filesystem allowlists to build and run Isaac Sim.

**Step 1 — Install the GPU bwrap wrapper and check settings:**
```bash
./tools/claude/setup_sandbox.sh
```

**Step 2 — Add the printed snippet to `~/.claude/settings.json`:**
```json
"sandbox": {
  "enabled": true,
  "autoAllowBashIfSandboxed": true,
  "permissions": {
    "disk": {
      "write": [
        "~/.cache/packman",
        "~/.local/share/ov",
        "~/.nvidia-omniverse",
        "/dev/nvidia*",
        "/dev/dri/*",
        "/dev/nvidia-caps/*",
        "/tmp/.X11-unix"
      ]
    },
    "network": {
      "allowedHosts": [
        "bootstrap.packman.nvidia.com",
        "d4i3qtqj3r0z5.cloudfront.net",
        "urm.nvidia.com",
        "omnipackages.nvidia.com",
        "pdx.s8k.io"
      ]
    }
  }
}
```

**Step 3 — Relaunch Claude Code** so the new bwrap wrapper is picked up.

> **PATH requirement:** `~/.local/bin` must appear before `/usr/bin` in `PATH`. The setup script will warn if this is not the case.

---

## Building

| Target | Command (internal) | Command (external/no-docker) |
|--------|-------------------|-------------------------------|
| C++ + extensions | `./build.sh` | `./build.sh --no-docker` |
| Docs | `./tools/build_docs.sh` | `./tools/build_docs.sh` |

Internal (NVIDIA) builds use linbuild (Docker-based) by default — omit `--no-docker`.
External / open-source builds pass `--no-docker` since linbuild is not available.

On machines with many cores, add `-j12` to avoid OOM:
```bash
./build.sh -j12
```

> **Sandbox note:** Docker (`linbuild`) does not work inside the Claude Code sandbox. When building inside the sandbox, use `--no-docker`.

---

## Running

Headless (no display required):
```bash
./build/linux-x86_64/release/isaac-sim.sh --no-window
```

> **Sandbox note:** `isaac-sim.sh` and other Kit/Isaac Sim app launch scripts require GPU and filesystem access beyond the sandbox defaults. Run them outside of sandbox mode, or ensure the sandbox setup above is complete.

---

## Notes

- **Packman cache** lives at `~/.cache/packman` (outside the repo). It is sandbox-allowlisted so builds can download packages.
- **Extension cache** lives at `~/.local/share/ov` and `~/.nvidia-omniverse`. Both are sandbox-allowlisted.
- Verify GPU is visible inside the sandbox at any time: `nvidia-smi`

