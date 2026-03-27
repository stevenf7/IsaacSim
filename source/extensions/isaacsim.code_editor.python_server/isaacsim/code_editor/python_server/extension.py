# SPDX-FileCopyrightText: Copyright (c) 2018-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""TCP socket server extension for remote Python code execution in Isaac Sim."""

from __future__ import annotations

__all__ = []

import asyncio
import contextlib
import io
import json
import socket
import sys
import threading
import time
import traceback

import carb
import omni.ext

from .executor import ExecutionResult, Executor

_SETTINGS_PREFIX = "/exts/isaacsim.code_editor.python_server"


def _get_event_loop() -> asyncio.AbstractEventLoop:
    """Retrieve the current event loop with a fallback for older Python runtimes.

    Returns:
        The current asyncio event loop.
    """
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        return asyncio.get_event_loop_policy().get_event_loop()


def _serialize_result(value: object) -> object:
    """Attempt to convert *value* into a JSON-native representation.

    Falls back to `repr` for objects that are not directly JSON-serializable.

    Args:
        value: The Python object to serialize.

    Returns:
        A JSON-compatible representation of *value*.
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [_serialize_result(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _serialize_result(v) for k, v in value.items()}
    return repr(value)


class Extension(omni.ext.IExt):
    """TCP socket server for remote Python code execution in Isaac Sim.

    The extension creates a TCP server that accepts Python source code from any
    client (VS Code, LLM agents, custom tools), executes it within Isaac Sim's
    Python environment, and returns structured JSON responses.

    Optionally, Carbonite log messages can be broadcast over UDP to connected
    clients.

    Configuration is managed through Carbonite settings under
    ``/exts/isaacsim.code_editor.python_server/``.
    """

    def on_startup(self, ext_id: str) -> None:
        """Initialize the TCP server and optional UDP log broadcaster.

        Args:
            ext_id: The extension identifier.
        """
        self._globals: dict = {**globals()}

        settings = carb.settings.get_settings()
        self._socket_host: str = settings.get(f"{_SETTINGS_PREFIX}/host")
        self._socket_port: int = settings.get(f"{_SETTINGS_PREFIX}/port")
        self._publish_carb_logs: bool = settings.get(f"{_SETTINGS_PREFIX}/carb_logs")

        if self._publish_carb_logs:
            self._logging = carb.logging.acquire_logging()
            self._logger_handle = self._logging.add_logger(self._carb_logging)
            self._logging_levels: dict[int, str] = {
                carb.logging.LEVEL_INFO: "Info",
                carb.logging.LEVEL_WARN: "Warning",
                carb.logging.LEVEL_ERROR: "Error",
                carb.logging.LEVEL_FATAL: "Fatal",
            }

            self._udp_server: socket.socket | None = None
            self._udp_clients: list[tuple[str, int]] = []
            self._udp_server_running = False
            threading.Thread(target=self._create_udp_socket).start()

        self._server: asyncio.AbstractServer | None = None
        _get_event_loop().create_task(self._create_socket())

    def on_shutdown(self) -> None:
        """Shut down the TCP server and clean up resources."""
        if self._server is not None:
            self._server.close()
            asyncio.run_coroutine_threadsafe(self._server.wait_closed(), _get_event_loop())
            self._server = None

        if self._publish_carb_logs:
            self._logging.remove_logger(self._logger_handle)
            self._logging = None
            self._logger_handle = None
            self._udp_server = None
            self._udp_clients = []
            trial_count = 0
            while self._udp_server_running:
                time.sleep(0.1)
                trial_count += 1
                if trial_count > 10:
                    break
            self._udp_server_running = False

    # ------------------------------------------------------------------
    # UDP carb log broadcasting
    # ------------------------------------------------------------------

    def _carb_logging(self, source: str, level: int, filename: str, line_number: int, message: str) -> None:
        """Broadcast a carb log message to all registered UDP clients.

        Args:
            source: The source of the log message.
            level: The logging level.
            filename: The source filename.
            line_number: The line number in the source file.
            message: The log message content.
        """
        if level in self._logging_levels and self._udp_server and self._udp_clients:
            data = f"[{self._logging_levels[level]}][{source}] {message}".encode()
            for client in self._udp_clients:
                try:
                    self._udp_server.sendto(data, client)
                except Exception as exc:
                    carb.log_error(f"{exc} len:{len(data)}")

    def _create_udp_socket(self) -> None:
        """Create a UDP socket for broadcasting carb log messages."""
        self._udp_clients = []
        self._udp_server_running = True
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
            try:
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind((self._socket_host, self._socket_port))
                server.setblocking(False)
                server.settimeout(0.25)
            except Exception as exc:
                self._udp_server = None
                self._udp_clients = []
                carb.log_error(str(exc))
                self._udp_server_running = False
                return

            self._udp_server = server
            while self._udp_server:
                try:
                    _, addr = server.recvfrom(1024)
                    if addr not in self._udp_clients:
                        self._udp_clients.append(addr)
                except socket.timeout:
                    pass
                except Exception as exc:
                    carb.log_warn(f"UDP server error: {exc}")
                    break
            self._udp_server = None
            self._udp_clients = []
            self._udp_server_running = False

    # ------------------------------------------------------------------
    # TCP code execution server
    # ------------------------------------------------------------------

    async def _create_socket(self) -> None:
        """Create the async TCP server and begin accepting connections."""

        class _ServerProtocol(asyncio.Protocol):
            """Handle individual TCP connections from clients.

            Incoming data is buffered until the client signals EOF (half-close),
            ensuring that TCP-fragmented payloads are fully reassembled before
            execution.
            """

            def __init__(self, parent: Extension) -> None:
                super().__init__()
                self._parent = parent
                self._buffer = bytearray()

            def connection_made(self, transport: asyncio.BaseTransport) -> None:
                carb.log_info(f"Connection from {transport.get_extra_info('peername')}")
                self.transport = transport

            def data_received(self, data: bytes) -> None:
                self._buffer.extend(data)

            def eof_received(self) -> bool:
                self._parent._process_code(self._buffer.decode(), self.transport)
                self._buffer.clear()
                return True

        try:
            self._server = await _get_event_loop().create_server(
                protocol_factory=lambda: _ServerProtocol(self),
                host=self._socket_host,
                port=self._socket_port,
                family=socket.AF_INET,
                reuse_port=None if sys.platform == "win32" else True,
            )
            carb.log_info(f"Serving at {self._socket_host}:{self._socket_port}")
            await self._server.start_serving()
        except Exception as exc:
            carb.log_error(str(exc))
            self._server = None

    def _process_code(self, source: str, transport: asyncio.Transport) -> None:
        """Execute Python source and send a JSON reply back to the client.

        Synchronous code is executed directly inside the protocol callback so
        that the event loop is **not** inside an asyncio Task.  This avoids
        ``RuntimeError: Cannot enter into task … while another task … is being
        executed`` when the user code pumps the application event loop (e.g.
        ``update_app``).

        If the compiled code is a coroutine (contains ``await``), a Task is
        created to await it and send the reply asynchronously.

        Args:
            source: The Python source code to execute.
            transport: The asyncio transport for sending the response.
        """
        executor = Executor(self._globals, self._globals)
        exec_result: ExecutionResult = executor.execute(source)

        if exec_result.exception is None and asyncio.iscoroutine(exec_result.result):
            _get_event_loop().create_task(self._await_and_reply(exec_result, transport))
            return

        self._send_reply(exec_result, transport)

    async def _await_and_reply(self, exec_result: ExecutionResult, transport: asyncio.Transport) -> None:
        """Await a coroutine result produced by user code and send the reply.

        Stdout is redirected during the await so that ``print()`` calls inside
        the coroutine are captured in the JSON response ``output`` field.

        Args:
            exec_result: The execution result whose ``result`` is a coroutine.
            transport: The asyncio transport for sending the response.
        """
        coro = exec_result.result
        async_output = io.StringIO()
        try:
            with contextlib.redirect_stdout(async_output):
                awaited = await coro
        except Exception as exc:
            combined_output = exec_result.output + async_output.getvalue()
            exec_result = ExecutionResult(
                output=combined_output,
                exception=exc,
                traceback_str=traceback.format_exc(),
            )
        else:
            combined_output = exec_result.output + async_output.getvalue()
            exec_result = ExecutionResult(output=combined_output, result=awaited)
        self._send_reply(exec_result, transport)

    def _send_reply(self, exec_result: ExecutionResult, transport: asyncio.Transport) -> None:
        """Build and send the JSON response for an execution result.

        Args:
            exec_result: The completed execution result.
            transport: The asyncio transport for sending the response.
        """
        output = exec_result.output
        if output.endswith("\n"):
            output = output[:-1]

        reply: dict[str, object] = {
            "status": "ok" if exec_result.exception is None else "error",
            "output": output,
        }

        if exec_result.exception is None and exec_result.is_expression:
            reply["result"] = _serialize_result(exec_result.result)

        if exec_result.exception is not None:
            reply["traceback"] = [exec_result.traceback_str]
            reply["ename"] = type(exec_result.exception).__name__
            reply["evalue"] = str(exec_result.exception)

        transport.write(json.dumps(reply, separators=(",", ":")).encode())
        transport.close()
