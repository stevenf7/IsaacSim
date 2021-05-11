import omni.kit


async def simulate(seconds, steps_per_sec=60):
    for frame in range(int(steps_per_sec * seconds)):
        await omni.kit.app.get_app().next_update_async()
