"""List all visible UI windows in the Isaac Sim application.

No injected globals required.
"""


async def _list():
    import omni.ui as ui

    windows = ui.Workspace.get_windows()
    visible = [w for w in windows if w.visible]
    hidden = [w for w in windows if not w.visible]

    print("Visible windows:")
    for w in visible:
        print(f"  [{w.width:.0f}x{w.height:.0f}] {w.title}")

    print("\nHidden windows:")
    for w in hidden:
        print(f"  {w.title}")


await _list()
