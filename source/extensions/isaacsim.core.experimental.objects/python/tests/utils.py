# Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from typing import Callable, Literal

import omni.kit.test
import omni.usd
from isaacsim.core.simulation_manager import SimulationManager


def parametrize(
    *,
    devices: list[Literal["cpu", "cuda"]] = ["cpu", "cuda"],
    backends: list[Literal["usd", "usdrt", "fabric", "tensor"]] = ["usd", "usdrt", "fabric", "tensor"],
    instances: list[Literal["one", "many"]] = ["one", "many"],
    operations: list[Literal["wrap", "create"]] = ["wrap", "create"],
    prim_classes: list[type],
    prim_classes_kwargs: list[dict] | None = None,
    populate_stage_func: Callable[[int, Literal["wrap", "create"]], None],
    max_num_prims: int = 5,
):
    def decorator(func):
        async def wrapper(self):
            for device in devices:
                for backend in backends:
                    for instance in instances:
                        for operation in operations:
                            for prim_class, prim_class_kwargs in zip(
                                prim_classes,
                                [{}] * len(prim_classes) if prim_classes_kwargs is None else prim_classes_kwargs,
                            ):
                                assert backend in ["usd", "fabric", "tensor"], f"Invalid backend: {backend}"
                                assert instance in ["one", "many"], f"Invalid instance: {instance}"
                                assert operation in ["wrap", "create"], f"Invalid operation: {operation}"
                                print(
                                    f"  |-- device: {device}, backend: {backend}, instance: {instance}, operation: {operation}, prim_class: {prim_class.__name__}"
                                )
                                # populate stage
                                await populate_stage_func(max_num_prims, operation)
                                # configure simulation manager
                                SimulationManager.set_physics_sim_device(device)
                                # parametrize test
                                if operation == "wrap":
                                    paths = "/World/A_0" if instance == "one" else "/World/A_.*"
                                elif operation == "create":
                                    paths = (
                                        "/World/A_0"
                                        if instance == "one"
                                        else [f"/World/A_{i}" for i in range(max_num_prims)]
                                    )
                                prim = prim_class(paths, **prim_class_kwargs)
                                num_prims = 1 if instance == "one" else max_num_prims
                                # call test method according to backend
                                if backend == "tensor":
                                    omni.timeline.get_timeline_interface().play()
                                    await omni.kit.app.get_app().next_update_async()
                                    await func(self, prim=prim, num_prims=num_prims, device=device, backend=backend)
                                    omni.timeline.get_timeline_interface().stop()
                                elif backend in ["usd", "usdrt", "fabric"]:
                                    await func(self, prim=prim, num_prims=num_prims, device=device, backend=backend)

        return wrapper

    return decorator
