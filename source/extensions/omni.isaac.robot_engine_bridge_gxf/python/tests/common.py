import omni


def get_selected_path():
    selectedPrims = omni.usd.get_context().get_selection().get_selected_prim_paths()

    if len(selectedPrims) > 0:
        curr_prim = selectedPrims[-1]
    else:
        curr_prim = None
    return curr_prim


async def simulate(seconds, steps_per_sec=60):
    for frame in range(int(steps_per_sec * seconds)):
        await omni.kit.app.get_app().next_update_async()
