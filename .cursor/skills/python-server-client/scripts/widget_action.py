"""Find and interact with a UI widget by query string.

Injected globals (via isaacsim_send.py --arg):
    action: str — Action to perform: click, double_click, right_click, type, read (default: click).
    query: str — Widget query string (e.g. "Load", "Play", window/button name).
    text: str — Text to type (only for action=type).
    max_frames: int — Max frames to poll for widget (default: 100).
"""

# Defaults
if "action" not in dir():
    action = "click"  # noqa: F841
if "query" not in dir():
    raise ValueError("query is required (e.g. --arg query=Load)")
if "text" not in dir():
    text = ""  # noqa: F841
if "max_frames" not in dir():
    max_frames = 100  # noqa: F841


async def _act():
    from isaacsim.test.utils.menu_utils import perform_widget_action

    try:
        result = await perform_widget_action(query, action=action, text=text, max_frames=int(max_frames))
    except TimeoutError:
        print(f"ERROR: Widget '{query}' not found after {max_frames} frames")
        return
    except ValueError as e:
        print(f"ERROR: {e}")
        return

    if action == "read":
        for k, v in result.items():
            print(f"  {k}: {v}")
    else:
        print(f"{action.replace('_', ' ').capitalize()}ed widget '{query}'")


await _act()
