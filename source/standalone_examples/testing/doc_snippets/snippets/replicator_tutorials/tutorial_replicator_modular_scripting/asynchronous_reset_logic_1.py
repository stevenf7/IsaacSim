async def run_stacking_simulation_async(prim_path=None):
    actions = [("reset", "RESET", 10), ("setup", "SETUP", 500), ("run", "FINISHED", 1500)]
    for action, state, wait in actions:
        await publish_event_and_wait_for_completion_async(
            publish_payload={"prim_path": prim_path, "action": action},
            expected_payload={"prim_path": prim_path, "state_name": state},
            publish_event_name=VolumeStackRandomizer.EVENT_NAME_IN,
            subscribe_event_name=VolumeStackRandomizer.EVENT_NAME_OUT,
            max_wait_updates=wait,
        )
