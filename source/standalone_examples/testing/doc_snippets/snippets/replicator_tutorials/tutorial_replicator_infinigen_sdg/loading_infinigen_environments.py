# Load the environment URLs from the configuration
env_config = config.get("environments", {})
env_urls = infinigen_utils.get_usd_paths(
    files=env_config.get("files", []), folders=env_config.get("folders", []), skip_folder_keywords=[".thumbs"]
)

# Cycle through the environments
env_cycle = cycle(env_urls)

# Load the next environment in the cycle
env_url = next(env_cycle)
print(f"[SDG] Loading environment: {env_url}")
infinigen_utils.load_env(env_url, prim_path="/Environment")
