# Public API for module isaacsim.robot.poser.ui:

## Classes

- class UIBuilder
  - def __init__(self)
  - def on_menu_callback(self)
  - def on_timeline_event(self, event: Any)
  - def on_assets_loaded(self)
  - def on_simulation_stop_play(self)
  - def on_update(self, dt: float)
  - def cleanup(self)
  - def build_ui(self)
  - def toggle_tracking_for_path(self, prim_path: str, enable: bool) -> bool
