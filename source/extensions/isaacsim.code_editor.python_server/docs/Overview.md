```{csv-table}
**Extension**: {{ extension_version }},**Documentation Generated**: {sub-ref}`today`
```

# Overview

The isaacsim.code_editor.python_server extension provides a TCP socket server that enables remote Python code execution within a running Isaac Sim instance. Any client (VS Code, LLM agents, custom scripts) can connect, send Python source code, and receive structured JSON results.

## Quick Start

Launch Isaac Sim with the extension enabled:

```bash
bash isaac-sim.sh --no-window --enable isaacsim.code_editor.python_server
```

Wait for `app ready` in the output, then connect from any TCP client on port 8226.

## Functionality

### Code Execution Server

The extension creates an async TCP server that listens for incoming Python source code. When code is received, it executes within Isaac Sim's Python environment using the Executor class, which handles both statements and expressions. Results, including output, evaluated expression values, errors, and tracebacks, are transmitted back as JSON.

### Wire Protocol

- **Request**: Raw UTF-8 Python source code sent over TCP. The client must signal end-of-input by calling ``write_eof()`` (TCP half-close) after sending all data. The server buffers incoming data until EOF is received before executing, ensuring that TCP-fragmented payloads are fully reassembled.
- **Response**: JSON object with the following fields:
  - `status`: `"ok"` or `"error"`
  - `output`: Captured standard output (includes output from both synchronous and async code)
  - `result`: Evaluated expression value (present only for expression evaluation)
  - `traceback`: List of traceback strings (present only on error)
  - `ename`: Exception class name (present only on error)
  - `evalue`: Exception message (present only on error)

### Async Code Support

The server supports top-level ``await`` expressions. When submitted code produces a coroutine, the server awaits it within the Kit event loop. Standard output from ``print()`` calls inside awaited coroutines is captured and included in the JSON response ``output`` field.

```python
# Top-level await is supported
import asyncio
await asyncio.sleep(0.1)
print("this appears in the output field")
```

### State Persistence

The server maintains a shared globals dictionary across all connections within a session. Variables defined in one request are available in subsequent requests. This enables incremental scene construction across multiple client calls.

### Carbonite Log Broadcasting

An optional UDP-based logging feature broadcasts Isaac Sim's Carbonite logging messages to connected clients, providing real-time access to internal logging output.

## Client Example

### Python (asyncio)

```python
import asyncio
import json

async def send_code(code: str, host: str = "127.0.0.1", port: int = 8226) -> dict:
    """Send Python code to Isaac Sim and return the JSON response."""
    reader, writer = await asyncio.open_connection(host, port)
    writer.write(code.encode())
    writer.write_eof()  # Signal end-of-input (required)
    data = await asyncio.wait_for(reader.read(), timeout=30.0)
    writer.close()
    return json.loads(data.decode())

# Usage
result = asyncio.run(send_code('print("Hello from Isaac Sim")'))
print(result)
# {"status": "ok", "output": "Hello from Isaac Sim", "result": null}
```

**Important**: Always call ``writer.write_eof()`` after sending code. The server buffers incoming data and only executes once it receives EOF. Without it, the connection will hang until the timeout.

### netcat (quick test)

```bash
echo 'print("hello")' | nc -q 0 127.0.0.1 8226
```

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
