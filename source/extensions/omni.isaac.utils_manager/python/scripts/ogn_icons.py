from pathlib import Path


class Icons:
    """A utility that scans the icon folder and returns the icon depending on the type"""

    def __init__(self):
        import carb.settings

        current_path = Path(__file__).parent
        icon_path = current_path.joinpath("icons")

        self._style = carb.settings.get_settings().get_as_string("/persistent/app/window/uiStyle") or "NvidiaDark"

        # Read all the svg files in the directory
        self._icons = {icon.stem: icon for icon in icon_path.joinpath(self._style).glob("*.svg")}

    def get(self, prim_type, default=None):
        """Checks the icon cache and returns the icon if exists"""
        found = self._icons.get(prim_type)
        if not found and default:
            found = self._icons.get(default)

        if found:
            return str(found)

        return ""
