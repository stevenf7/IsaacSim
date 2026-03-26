#!/usr/bin/env python3
"""Send Python code to a running Isaac Sim instance via the python_server TCP socket.

Usage:
    # Inline code
    python isaacsim_send.py 'print("hello")'

    # From stdin (pipe or heredoc)
    echo 'print("hello")' | python isaacsim_send.py

    # Send a .py file
    python isaacsim_send.py --file path/to/script.py

    # Send a file with injected variables
    python isaacsim_send.py --file script.py --arg output_path=/tmp/shot.png --arg width=1920

    # Custom host/port/timeout
    python isaacsim_send.py --host 127.0.0.1 --port 8226 --timeout 120 'print("hello")'

    # Raw JSON output (default is formatted human-readable)
    python isaacsim_send.py --raw 'print("hello")'

    # --file scripts are isolated by default (no state leakage between calls).
    # Use --no-isolate to share state across calls:
    python isaacsim_send.py --no-isolate --file setup.py

Exit codes:
    0 - Execution succeeded (status: "ok")
    1 - Execution failed (status: "error") or connection error
"""

import argparse
import asyncio
import json
import sys


async def send_and_receive(host: str, port: int, source: str, timeout: float = 60.0) -> dict:
    """Send Python source code and return the parsed JSON response."""
    reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
    writer.write(source.encode())
    writer.write_eof()
    data = await asyncio.wait_for(reader.read(), timeout=timeout)
    writer.close()
    return json.loads(data.decode())


def _inject_args(source: str, args: list[str]) -> str:
    """Prepend variable assignments for --arg key=value pairs."""
    if not args:
        return source
    lines = []
    for arg in args:
        key, _, value = arg.partition("=")
        key = key.strip()
        value = value.strip()
        try:
            parsed = eval(value, {"__builtins__": {}})  # noqa: S307
            lines.append(f"{key} = {repr(parsed)}")
        except Exception:
            lines.append(f'{key} = "{value}"')
    return "\n".join(lines) + "\n" + source


def _wrap_isolated(source: str, args: list[str]) -> str:
    """Wrap script in an async function scope to isolate from executor state.

    The python_server executor shares global state between connections.
    Wrapping in a function prevents variable leakage between calls.
    Top-level `await` expressions are supported inside the wrapper.
    """
    # Build argument assignments
    arg_lines = []
    for arg in args:
        key, _, value = arg.partition("=")
        key = key.strip()
        value = value.strip()
        try:
            parsed = eval(value, {"__builtins__": {}})  # noqa: S307
            arg_lines.append(f"    {key} = {repr(parsed)}")
        except Exception:
            arg_lines.append(f'    {key} = "{value}"')

    # Indent the source
    indented = "\n".join("    " + line if line.strip() else "" for line in source.splitlines())

    parts = ["async def _isolated_script():"]
    if arg_lines:
        parts.extend(arg_lines)
    parts.append(indented)
    parts.append("")
    parts.append("await _isolated_script()")

    return "\n".join(parts)


async def main():
    parser = argparse.ArgumentParser(description="Send Python code to Isaac Sim python_server")
    parser.add_argument("code", nargs="?", help="Python code to execute (reads stdin if omitted)")
    parser.add_argument("--file", "-f", help="Path to a Python file to send instead of inline code")
    parser.add_argument("--arg", "-a", action="append", default=[], help="Inject key=value as a global variable (use with --file)")
    parser.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8226, help="Server port (default: 8226)")
    parser.add_argument("--timeout", type=float, default=60.0, help="Response timeout in seconds (default: 60)")
    parser.add_argument("--raw", action="store_true", help="Print raw JSON instead of formatted output")
    parser.add_argument("--no-isolate", action="store_true", help="Don't wrap --file scripts in isolated scope (use for state persistence)")
    args = parser.parse_args()

    if args.file:
        with open(args.file) as f:
            source = f.read()
        if args.no_isolate:
            source = _inject_args(source, args.arg)
        else:
            source = _wrap_isolated(source, args.arg)
    elif args.code:
        source = args.code
        source = _inject_args(source, args.arg)
    else:
        source = sys.stdin.read()

    if not source.strip():
        print("Error: No code provided", file=sys.stderr)
        sys.exit(1)

    try:
        result = await send_and_receive(args.host, args.port, source, args.timeout)
    except ConnectionRefusedError:
        print(f"Error: Cannot connect to Isaac Sim at {args.host}:{args.port}", file=sys.stderr)
        print("Make sure Isaac Sim is running with isaacsim.code_editor.python_server enabled.", file=sys.stderr)
        sys.exit(1)
    except asyncio.TimeoutError:
        print(f"Error: Timeout after {args.timeout}s waiting for response", file=sys.stderr)
        sys.exit(1)

    if args.raw:
        print(json.dumps(result, indent=2))
    else:
        output = result.get("output", "")
        if output:
            print(output)
        if "result" in result and result["result"] is not None:
            print(f"=> {result['result']}")
        if result.get("status") == "error":
            print(f"\nERROR [{result.get('ename', '?')}]: {result.get('evalue', '?')}", file=sys.stderr)
            for tb in result.get("traceback", []):
                print(tb, file=sys.stderr)

    sys.exit(0 if result.get("status") == "ok" else 1)


if __name__ == "__main__":
    asyncio.run(main())
