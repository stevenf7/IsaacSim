import omni.kit.app


def get_extension_id(extension_name: str) -> str:
    """Get extension id for a loaded extension
        Args:
            extension_name (str): name of the extension

        Returns:
            str: Full extension id
    """
    extension_manager = omni.kit.app.get_app().get_extension_manager()
    return extension_manager.get_enabled_extension_id(extension_name)


def get_extension_path(ext_id: str) -> str:
    """Get extension path for a loaded extension
        Args:
            extension_name (str): name of the extension

        Returns:
            str: Path to loaded extension root directory
    """
    extension_manager = omni.kit.app.get_app().get_extension_manager()
    return extension_manager.get_extension_path(ext_id)


def enable_extension(extension_name: str) -> bool:
    """Load an extension
        Args:
            extension_name (str): name of the extension

        Returns:
            bool: True if extension could be loaded, False otherwise
    """
    extension_manager = omni.kit.app.get_app().get_extension_manager()
    return extension_manager.set_extension_enabled_immediate(extension_name, True)


def disable_extension(extension_name: str) -> bool:
    """Load an extension
        Args:
            extension_name (str): name of the extension

        Returns:
            bool: True if extension could be loaded, False otherwise
    """
    extension_manager = omni.kit.app.get_app().get_extension_manager()
    return extension_manager.set_extension_enabled_immediate(extension_name, False)


def set_extension_enabled(name: str, enabled: bool) -> None:
    """
    Set the state for an extension

    Args:
        name (str): name of extension to enabled
        enabled (bool): true if extension should be enabled, false to turn extension off

    """
    extension_manager = omni.kit.app.get_app().get_extension_manager()
    return extension_manager.set_extension_enabled_immediate(name, enabled)
