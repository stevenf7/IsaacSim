class VolumeStackRandomizer(BehaviorScript):
    BEHAVIOR_NS = "volumeStackRandomizer"
    EVENT_NAME_IN = f"{EXTENSION_NAME}.{BEHAVIOR_NS}.in"
    EVENT_NAME_OUT = f"{EXTENSION_NAME}.{BEHAVIOR_NS}.out"
    ACTION_FUNCTION_MAP = {
        "setup": "_setup_async",
        "run": "_run_behavior_async",
        "reset": "_reset_async",
    }

    async def _setup_async(self):
        # Asynchronous setup logic...
        pass

    async def _run_behavior_async(self):
        # Asynchronous behavior execution...
        pass

    async def _reset_async(self):
        # Asynchronous reset logic...
        pass
