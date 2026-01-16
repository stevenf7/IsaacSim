# Get server path
assets_root_path = await get_assets_root_path_async()
if assets_root_path is None:
    print("[SDG] Could not get nucleus server path")
    return

# Load environment stage
env_url = config.get("env_url", "/Isaac/Environments/Grid/default_environment.usd")
env_path = env_url if env_url.startswith("omniverse://") else assets_root_path + env_url
print(f"[SDG] Loading Stage {env_url}")
omni.usd.get_context().open_stage(env_path)
stage = omni.usd.get_context().get_stage()

await omni.kit.app.get_app().next_update_async()
