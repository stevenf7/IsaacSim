
.. _isaac_sim_app_python_server:


==========================================
Python Server (Remote Code Execution)
==========================================

Overview
---------

The ``isaacsim.code_editor.python_server`` extension provides a TCP socket server that enables remote Python code execution within a running Isaac Sim instance.
Any client — VS Code, LLM agents, custom automation scripts — can connect over TCP, send Python source code, and receive structured JSON results.

The extension is automatically loaded as a dependency of ``isaacsim.code_editor.vscode``, but it can also be enabled independently for headless or programmatic workflows.

|br| |hr|

Enabling the Extension
------------------------

Enable the extension using the :doc:`Extension Manager <extensions:ext_core/ext_extension-manager>` by searching for ``isaacsim.code_editor.python_server``.

By default the server listens on ``127.0.0.1:8226``.
These values can be changed through the Carbonite settings (see :ref:`python_server_settings` below).

|br| |hr|

.. _python_server_wire_protocol:

Wire Protocol
--------------

The wire protocol is intentionally simple so that any TCP client can use it:

**Request**

Send raw UTF-8 Python source code over a TCP connection to the configured host and port.
After sending all code, the client **must** signal end-of-input by performing a TCP half-close
(``write_eof()`` in Python, ``shutdown(SHUT_WR)`` at the socket level, or ``-q 0`` with netcat).
The server buffers incoming data until EOF is received, ensuring that TCP-fragmented payloads
are fully reassembled before execution.

.. warning::

   If the client does not signal EOF, the server will wait indefinitely for more data and
   the connection will hang until the client disconnects or a timeout occurs.

**Response**

A single JSON object is returned, then the connection is closed by the server.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Field
     - Description
   * - ``status``
     - ``"ok"`` on success, ``"error"`` on failure.
   * - ``output``
     - Captured standard output (``stdout``) from the executed code.
   * - ``result``
     - *(present only for expression evaluation)* The evaluated expression value.
       JSON-native types (``str``, ``int``, ``float``, ``bool``, ``None``, ``list``, ``dict``) are returned directly.
       Non-serializable objects fall back to their ``repr()`` string.
   * - ``traceback``
     - *(present only on error)* List of traceback strings.
   * - ``ename``
     - *(present only on error)* Exception class name.
   * - ``evalue``
     - *(present only on error)* Exception message string.

|br| |hr|

Usage Examples
---------------

Python Client
^^^^^^^^^^^^^^

Connect from any Python script or LLM tool to execute code in the running Isaac Sim instance:

.. code-block:: python

    import asyncio
    import json


    async def execute_in_isaac(source: str, host: str = "127.0.0.1", port: int = 8226) -> dict:
        """Send Python source to a running Isaac Sim instance and return the result."""
        reader, writer = await asyncio.open_connection(host, port)
        writer.write(source.encode())
        writer.write_eof()
        data = await reader.read()
        writer.close()
        return json.loads(data.decode())


    # Execute a statement
    result = asyncio.run(execute_in_isaac('print("Hello from Isaac Sim!")'))
    print(result)
    # {'status': 'ok', 'output': 'Hello from Isaac Sim!'}

    # Evaluate an expression
    result = asyncio.run(execute_in_isaac("1 + 1"))
    print(result)
    # {'status': 'ok', 'output': '', 'result': 2}

    # Handle errors
    result = asyncio.run(execute_in_isaac("1 / 0"))
    print(result["status"])   # 'error'
    print(result["ename"])    # 'ZeroDivisionError'

Command-line (netcat)
^^^^^^^^^^^^^^^^^^^^^^

For quick testing, use ``netcat`` or similar tools:

.. code-block:: bash

    echo 'print("Hello")' | nc 127.0.0.1 8226

|br| |hr|

Async Code Support
--------------------

The server supports top-level ``await`` expressions.
When submitted code contains ``await``, the server compiles it as an async coroutine,
schedules it on the Kit event loop, and awaits the result before sending the JSON response.

.. code-block:: python

    # Top-level await is supported
    import asyncio
    await asyncio.sleep(0.1)
    print("this output is captured")

Standard output from ``print()`` calls inside awaited coroutines is captured and included in the
JSON response ``output`` field, just like synchronous code.

|br| |hr|

.. _python_server_state_persistence:

State Persistence
-------------------

The server maintains a shared Python globals dictionary across all connections within a session.
Variables, imports, and function definitions from one request are available in subsequent requests.
This enables incremental workflows such as building a scene step by step:

.. code-block:: python

    # Request 1: Create a stage
    import isaacsim.core.experimental.utils.stage as stage_utils
    await stage_utils.create_new_stage_async(template="empty")

    # Request 2: Uses stage_utils from the previous request
    stage_utils.define_prim("/World", "Xform")

Each new TCP connection reuses the same globals, so there is no need to re-import modules
or re-define variables between calls.

|br| |hr|

LLM Integration
-----------------

The Python server is designed to be easy for LLM agents to use.
An LLM tool implementation needs only to:

1. Open a TCP connection to the configured host and port.
2. Send the Python code as UTF-8 bytes.
3. Signal end-of-input by calling ``write_eof()`` (required — the server buffers until EOF).
4. Read the JSON response.
5. Parse ``status`` to determine success or failure, ``output`` for printed text, and ``result`` for expression values.

Because the protocol is a single request/response per connection, there is no connection-level state to manage.
However, Python-level state (variables, imports) persists across connections within a session
(see :ref:`python_server_state_persistence` above).

|br| |hr|

.. _python_server_settings:

Settings
---------

The extension is configured through Carbonite settings under ``/exts/isaacsim.code_editor.python_server/``.

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Setting
     - Default
     - Description
   * - ``host``
     - ``"127.0.0.1"``
     - IP address the server listens on. Set to ``"0.0.0.0"`` to accept remote connections.
   * - ``port``
     - ``8226``
     - TCP port number.
   * - ``carb_logs``
     - ``false``
     - Enable UDP broadcasting of Carbonite log messages to connected clients.
       May cause the application to freeze in certain circumstances.

.. warning::

   Setting ``host`` to ``"0.0.0.0"`` allows **any** machine on the network to execute arbitrary Python code
   in your Isaac Sim session. Only do this in trusted network environments.

|br| |hr|

Carbonite Log Broadcasting (UDP)
----------------------------------

When ``carb_logs`` is enabled, the extension opens a UDP socket on the same host and port.
Clients register by sending any datagram to that address, after which all Carbonite log messages
(Info, Warning, Error, Fatal) are broadcast to registered clients as UTF-8 strings in the format:

.. code-block:: text

    [Level][Source] Message

This is primarily used by the `Isaac Sim VS Code Edition`_ extension to display Isaac Sim logs in the VS Code output panel.

.. _Isaac Sim VS Code Edition: https://marketplace.visualstudio.com/items?itemName=NVIDIA.isaacsim-vscode-edition
