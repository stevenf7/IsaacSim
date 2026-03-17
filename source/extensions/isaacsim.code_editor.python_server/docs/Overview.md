```{csv-table}
**Extension**: {{ extension_version }},**Documentation Generated**: {sub-ref}`today`
```

# Overview

The isaacsim.code_editor.python_server extension provides a TCP socket server that enables remote Python code execution within a running Isaac Sim instance. Any client (VS Code, LLM agents, custom scripts) can connect, send Python source code, and receive structured JSON results.

## Functionality

### Code Execution Server

The extension creates an async TCP server that listens for incoming Python source code. When code is received, it executes within Isaac Sim's Python environment using the Executor class, which handles both statements and expressions. Results, including output, evaluated expression values, errors, and tracebacks, are transmitted back as JSON.

### Wire Protocol

- **Request**: Raw UTF-8 Python source code sent over TCP.
- **Response**: JSON object with the following fields:
  - `status`: `"ok"` or `"error"`
  - `output`: Captured standard output
  - `result`: Evaluated expression value (present only for expression evaluation)
  - `traceback`: List of traceback strings (present only on error)
  - `ename`: Exception class name (present only on error)
  - `evalue`: Exception message (present only on error)

### Carbonite Log Broadcasting

An optional UDP-based logging feature broadcasts Isaac Sim's Carbonite logging messages to connected clients, providing real-time access to internal logging output.

## Key Components

### Executor

The Executor class manages Python code execution within Isaac Sim's environment. It accepts source code as strings and executes them asynchronously, capturing standard output, expression results, exceptions, and tracebacks. It distinguishes between expressions and statements, returning the evaluated value for expressions.

## Configuration

The extension provides three key configuration settings:

- `host`: Configures the IP address where the socket server listens for connections (default: 127.0.0.1)
- `port`: Sets the port number for socket communication (default: 8226)
- `carb_logs`: Controls whether Carbonite logging messages are broadcast via UDP (default: false, with warnings about potential application freezing)

## Integration

The extension depends on isaacsim.core.deprecation_manager for compatibility management within the Isaac Sim ecosystem.
