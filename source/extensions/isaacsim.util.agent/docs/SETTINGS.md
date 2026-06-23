```{csv-table}
**Extension**: {{ extension_version }},**Documentation Generated**: {sub-ref}`today`
```

# Settings

### exts."isaacsim.util.agent".system_prompt_append
- **Default Value**: ""
- **Description**: Text appended to the built-in agent system prompt. The built-in prompt (socket usage, port, screenshot instructions) is always included; use this to add project-specific guidance without editing source.

### exts."isaacsim.util.agent".allowed_tools
- **Default Value**: [
  "Read(**)",
  "Glob(**)",
  "Grep(**)",
  "Skill"
]
- **Description**: Tool allow rules passed to the agent, in addition to the mandatory in-repo socket-driver Bash rule that the extension always adds. These do not bound the agent (it executes arbitrary Python in-process); see the security note in docs/Overview.md.

### exts."isaacsim.util.agent".disallowed_tools
- **Default Value**: [
  "Read(//**)",
  "Glob(//**)",
  "Grep(//**)"
]
- **Description**: Tool deny rules passed to the agent; block the agent's own file tools from absolute paths. Cosmetic only (see docs/Overview.md).
