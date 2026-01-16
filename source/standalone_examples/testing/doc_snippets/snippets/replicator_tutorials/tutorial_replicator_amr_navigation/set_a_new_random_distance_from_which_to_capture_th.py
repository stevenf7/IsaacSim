NUM_FRAMES = 9
ENV_INTERVAL = 3
USE_TEMP_RP = True

out_dir = os.path.join(os.getcwd(), "_out_nav_sdg_demo", "")
nav_demo = NavSDGDemo()
asyncio.ensure_future(
    nav_demo.run_async(
        num_frames=NUM_FRAMES,
        out_dir=out_dir,
        env_urls=ENV_URLS,
        env_interval=ENV_INTERVAL,
        use_temp_rp=USE_TEMP_RP,
        seed=22,
    )
)
