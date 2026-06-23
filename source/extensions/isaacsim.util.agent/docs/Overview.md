# AI Agent Chat

`isaacsim.util.agent` adds a chat panel to the Isaac Sim UI for driving an external AI coding agent that builds and manipulates the scene interactively — e.g. *"find a forklift and place it at the loading dock."*

## How it works

The panel lives inside Isaac Sim. When you send a message, it spawns an external user-selected agent process (one subprocess per turn, resumed by session id) with its working directory at the repository root, so the robotics-sim **agent skills** auto-load. The agent acts on the **same** running Kit process over the loopback `isaacsim.code_editor.python_server` socket — its tool use is allow-listed to the in-repo `skills/isaac-sim-remote/scripts/` socket drivers — so scene changes appear live in the viewport.

```
StringField → AgentSession.send() → agent subprocess (stream-json)
   → reader thread → parse_line() → EventPump queue → per-frame drain → ChatWindow
agent Bash tool → isaacsim_send.py --port <P> → python_server (this Kit) → live stage
```

## Security

**The real security boundary is an OS sandbox** (restricted filesystem + network
egress) around the Isaac Sim process — and there is no substitute for it. The
agent's entire job is to send arbitrary Python over the socket into this Kit
process, which has full filesystem and network access; that code can read
`~/.ssh`, reach the network, or do anything the process can, regardless of any
tool rules. **Only run this panel in an environment you would trust the agent to
act in.**

The agent's tool allow-list (`Bash` restricted to the in-repo socket drivers,
`Read`/`Glob`/`Grep` scoped to the repo cwd) is cosmetic by comparison: it only
shapes the agent's *own* file tools and does nothing about the Python it
executes in-process, so it is not a containment mechanism. Prompts and scene
context are sent to the configured external agent/LLM provider.

## Status

Prototype.
