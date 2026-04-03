```{csv-table}
**Extension**: {{ extension_version }},**Documentation Generated**: {sub-ref}`today`
```

# Settings

## Settings Provided by the Extension

### exts."isaacsim.code_editor.python_server".host
- **Default Value**: "127.0.0.1"
- **Description**: IP address where the extension server will listen for connections.

### exts."isaacsim.code_editor.python_server".port
- **Default Value**: 8226
- **Description**: Port number where the extension server will listen for connections.

### exts."isaacsim.code_editor.python_server".carb_logs
- **Default Value**: false
- **Description**: Whether to publish incoming carb logging messages. Warning: enabling this feature may cause the application to freeze in certain circumstances.

### exts."isaacsim.code_editor.python_server".execution_timeout
- **Default Value**: 0
- **Description**: Global default execution timeout in seconds. When a request exceeds this limit, the server returns a TimeoutError response. Set to `0` to disable timeouts (no limit). Individual requests can override this value using the `timeout` field in the JSON envelope.

### exts."isaacsim.code_editor.python_server".keepalive_interval
- **Default Value**: 0
- **Description**: When non-zero, the server includes an `elapsed_seconds` field in the JSON response for any execution that takes longer than this many seconds. This provides visibility into long-running requests without changing the wire protocol. Set to `0` to disable (default). Applies to both synchronous and asynchronous code execution.
