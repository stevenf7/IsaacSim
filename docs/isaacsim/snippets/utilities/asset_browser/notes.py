import carb.settings
import omni.kit

## Change file filters
settings = carb.settings.get_settings()
settings.set("/exts/isaacsim.asset.browser/data/filter_file_suffixes", [])  # Show all file types
# settings.set("/exts/isaacsim.asset.browser/data/filter_file_suffixes", [".usd",".png",".yaml"])  # Show selected file types
settings.set("/exts/isaacsim.asset.browser/data/hide_file_without_thumbnails", False)

## Restart Extension
omni.kit.app.get_app().get_extension_manager().set_extension_enabled_immediate("isaacsim.asset.browser", False)
omni.kit.app.get_app().get_extension_manager().set_extension_enabled_immediate("isaacsim.asset.browser", True)
