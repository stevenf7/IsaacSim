from isaacsim import SimulationApp

SimulationApp(
    {
        "headless": True,
        "extra_args": [
            "--/app/hydraEngine/waitIdle=1",
            "--/app/updateOrder/checkForHydraRenderComplete=1000",
            "--/exts/isaacsim.ros2.bridge/publish_multithreading_disabled=1",
        ],
    },
)
