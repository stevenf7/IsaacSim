import carb.settings
import omni.kit

## Set Carb Setting
settings = carb.settings.get_settings()
settings.set("/exts/isaacsim.my.extension/data/foo", True)

## Restart Extension to Apply Changes
omni.kit.app.get_app().get_extension_manager().set_extension_enabled_immediate("isaacsim.my.extension", False)
omni.kit.app.get_app().get_extension_manager().set_extension_enabled_immediate("isaacsim.my.extension", True)
