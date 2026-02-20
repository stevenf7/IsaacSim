import carb.settings

settings = carb.settings.get_settings()

# set different types into different keys
# guideline: each extension puts settings in /ext/[ext name]/ and lists them extension.toml for discoverability
settings.set("/renderer/multiGPU/enabled", True)
