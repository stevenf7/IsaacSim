import carb.settings
import omni.kit

## Set Carb Setting
settings = carb.settings.get_settings()
settings.set("/exts/isaacsim.code_editor.python_server/keepalive_interval", 5)

## Restart Extension to Apply Changes
extension_manager = omni.kit.app.get_app().get_extension_manager()
extension_manager.set_extension_enabled_immediate("isaacsim.code_editor.python_server", False)
extension_manager.set_extension_enabled_immediate("isaacsim.code_editor.python_server", True)
