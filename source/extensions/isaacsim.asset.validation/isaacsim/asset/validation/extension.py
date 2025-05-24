import omni.ext


class IsaacSimAssetValidationExtension(omni.ext.IExt):
    """Isaac Sim Asset Validation Extension.

    This extension provides various custom rules to validate content for Isaac Sim,
    including physics validation, robot schema validation, and material validation.
    """

    def on_startup(self, ext_id):
        """Initialize the extension on startup.

        Args:
            ext_id: The extension identifier.
        """
        pass

    def on_shutdown(self):
        """Clean up resources when the extension is shut down."""
        pass
