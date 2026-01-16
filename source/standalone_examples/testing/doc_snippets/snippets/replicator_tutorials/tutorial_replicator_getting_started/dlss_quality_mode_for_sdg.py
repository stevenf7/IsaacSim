import carb.settings

# Set DLSS to Quality mode (2) for best SDG results (Options: 0 (Performance), 1 (Balanced), 2 (Quality), 3 (Auto))
carb.settings.get_settings().set("/rtx/post/dlss/execMode", 2)
