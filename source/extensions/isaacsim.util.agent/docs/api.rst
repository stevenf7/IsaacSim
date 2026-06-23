AI Agent Chat Extension [isaacsim.util.agent]
##############################################

In-UI chat panel that drives an external AI coding agent to build and manipulate
Isaac Sim scenes over the ``isaacsim.code_editor.python_server`` loopback socket.

The base :class:`AgentSession` owns the per-turn subprocess lifecycle and takes an
injected :class:`ResponseParser`; concrete backends live in their own subpackage
(``impl/claude`` provides :class:`ClaudeSession` + :class:`ClaudeResponseParser`).


Agent Session (base)
====================

.. automodule:: isaacsim.util.agent.impl.agent_session
    :members:
    :undoc-members:
    :no-show-inheritance:


Stream Events
=============

.. automodule:: isaacsim.util.agent.impl.stream_events
    :members:
    :undoc-members:
    :no-show-inheritance:


Claude Session
==============

.. automodule:: isaacsim.util.agent.impl.claude.claude_session
    :members:
    :undoc-members:
    :no-show-inheritance:


Claude Response Parser
======================

.. automodule:: isaacsim.util.agent.impl.claude.claude_parser
    :members:
    :undoc-members:
    :no-show-inheritance:


Event Pump
==========

.. automodule:: isaacsim.util.agent.impl.event_pump
    :members:
    :undoc-members:
    :no-show-inheritance:


Chat Window
===========

.. automodule:: isaacsim.util.agent.impl.chat_window
    :members:
    :undoc-members:
    :no-show-inheritance:


Port Discovery
==============

.. automodule:: isaacsim.util.agent.impl.port_discovery
    :members:
    :undoc-members:
    :no-show-inheritance:


Extension
=========

.. automodule:: isaacsim.util.agent.impl.extension
    :members:
    :undoc-members:
    :no-show-inheritance:
