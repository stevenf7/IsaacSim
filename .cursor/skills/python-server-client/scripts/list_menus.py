"""List all menu item paths from the Isaac Sim menubar.

No injected globals required. Requires a display (UI mode).
"""


async def _list():
    from isaacsim.test.utils.menu_utils import list_menu_paths

    import omni.kit.ui_test as ui_test

    if ui_test.get_menubar() is None:
        print("ERROR: No menubar found (is the app running with UI?)")
        return

    paths = list_menu_paths()
    print(f"Menu paths ({len(paths)}):")
    for path in paths:
        print(f"  {path}")


await _list()
