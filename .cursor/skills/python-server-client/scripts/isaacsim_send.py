#!/usr/bin/env python3
"""Send Python code to a running Isaac Sim instance via the python_server TCP socket.

Usage:
    # Inline code
    python isaacsim_send.py 'print("hello")'

    # From stdin (pipe or heredoc)
    echo 'print("hello")' | python isaacsim_send.py

    # Custom host/port
    python isaacsim_send.py --host 127.0.0.1 --port 8226 'print("hello")'

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
    reader, writer = await asyncio.open_connection(host, port)
    writer.write(source.encode())
    writer.write_eof()
    data = await asyncio.wait_for(reader.read(), timeout=timeout)
    writer.close()
    return json.loads(data.decode())


async def main():
    parser = argparse.ArgumentParser(description="Send Python code to Isaac Sim python_server")
    parser.add_argument("code", nargs="?", help="Python code to execute (reads stdin if omitted)")
    parser.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8226, help="Server port (default: 8226)")
    parser.add_argument("--timeout", type=float, default=60.0, help="Response timeout in seconds (default: 60)")
    args = parser.parse_args()

    source = args.code if args.code else sys.stdin.read()
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

    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("status") == "ok" else 1)


if __name__ == "__main__":
    asyncio.run(main())
