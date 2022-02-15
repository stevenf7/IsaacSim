# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


"""Generate Freespace Segmentation dataset
"""

import os
import omni
from omni.isaac.kit import SimulationApp
import carb.tokens
import argparse

CONFIG = {
    "experience": f'{os.environ["EXP_PATH"]}/omni.isaac.sim.python.kit',
    "width": 1280,
    "height": 720,
    "sync_loads": True,
    "headless": False,
    "renderer": "RayTracedLighting",
}

# D435
FOCAL_LEN = 24
HORIZONTAL_APERTURE = 21
VERTICAL_APERTURE = 11
FOCUS_DIST = 400


class FreespaceSegmentation:
    def __init__(self, scenario, semantic_labels):
        self.scenario = scenario
        self.semantic_labels = semantic_labels
        self.kit = SimulationApp(launch_config=CONFIG)
        from omni.isaac.core import SimulationContext
        from omni.isaac.core.utils.extensions import enable_extension

        self.simulation_context = SimulationContext(stage_units_in_meters=0.01)
        import omni

        # Enable SDK bridge extension
        enable_extension("omni.isaac.robot_engine_bridge")

        from pxr import UsdGeom, Usd, Gf
        import omni.isaac.dr as dr
        from omni.isaac.synthetic_utils import SyntheticDataHelper

        self._viewport = omni.kit.viewport_legacy.get_viewport_interface()

        self.dr = dr
        self.sd_helper = SyntheticDataHelper()
        self.frame = 0
        self.Gf = Gf
        self.UsdGeom = UsdGeom
        self.Usd = Usd

    def close(self):
        self.kit.close()

    def start(self):
        self.simulation_context.play()

    def stop(self):
        self.simulation_context.stop()
        omni.kit.commands.execute("RobotEngineBridgeDestroyApplication")
        self.kit.close()

    def create_stage(self):
        # Open base stage and set up axis to Z
        stage = self.kit.context.get_stage()
        rootLayer = stage.GetRootLayer()
        rootLayer.SetPermissionToEdit(True)
        with self.Usd.EditContext(stage, rootLayer):
            self.UsdGeom.SetStageUpAxis(stage, self.UsdGeom.Tokens.z)

        self._world = stage.DefinePrim("/World", "Xform")

        from omni.isaac.core.utils.nucleus import find_nucleus_server

        self.result, nucleus_server = find_nucleus_server()
        if self.result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return False
        self.asset_path = nucleus_server + "/Isaac"
        stage_path = self.asset_path + self.scenario

        self._world.GetReferences().AddReference(stage_path)
        self.kit.app.update()
        return True

    def create_camera(self):
        from omni.isaac.core.utils import rotations, prims

        self._camera = prims.create_prim(
            "/World/Camera",
            "Camera",
            translation=(789, 1456, 100.0),
            orientation=rotations.gf_rotation_to_np_array(self.Gf.Rotation(self.Gf.Vec3d(1, 0, 0), 90)),
            attributes={
                "focusDistance": FOCUS_DIST,
                "focalLength": FOCAL_LEN,
                "horizontalAperture": HORIZONTAL_APERTURE,
                "verticalAperture": VERTICAL_APERTURE,
            },
        )

        # Activate new camera
        self._viewport.get_viewport_window().set_active_camera(str(self._camera.GetPath()))

    def create_bridge_components(self):
        result, self.reb_camera = omni.kit.commands.execute(
            "RobotEngineBridgeCreateCamera",
            path="/World/REB_Camera",
            parent=None,
            rgb_output_component="output",
            rgb_output_channel="color",
            depth_output_component="output",
            depth_output_channel="encoder_depth",
            segmentation_output_component="output",
            segmentation_output_channel="segmentation",
            bbox2d_output_component="output",
            bbox2d_output_channel="encoder_bbox",
            bbox2d_class_list="",
            bbox3d_output_component="output",
            bbox3d_output_channel="encoder_bbox3d",
            bbox3d_class_list="",
            rgb_enabled=True,
            depth_enabled=False,
            segmentaion_enabled=True,
            bbox2d_enabled=False,
            bbox3d_enabled=False,
            camera_prim_rel=[self._camera.GetPath()],
            resolution=self.Gf.Vec2i(1280, 720),
        )

    def configure_bridge(self, json_file: str = "isaacsim.app.json"):
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.robot_engine_bridge")
        reb_extension_path = ext_manager.get_extension_path(ext_id)
        app_file = f"{reb_extension_path}/resources/isaac_engine/json/{json_file}"
        carb.log_info(f"create application with: {reb_extension_path} {app_file}")
        return omni.kit.commands.execute(
            "RobotEngineBridgeCreateApplication", asset_path=reb_extension_path, app_file=app_file
        )

    def configure_randomization(self):
        # Add color & transform randomization
        base_path = str(self._world.GetPath())
        self.color_comp = self.dr.commands.CreateColorComponentCommand(
            path=base_path + "/color_component",
            prim_paths=[base_path + "/Warehouse_Empty_small_realtime", base_path + "/GroundPlane"],
            include_children=True,
            first_color_range=(0.0, 0.0, 0.0),
            second_color_range=(1.0, 1.0, 1.0),
            roughness_range=(0.0, 1.0),
            metallic_range=(0.0, 1.0),
            duration=1.0,
        ).do()
        self.transform_comp = self.dr.commands.CreateTransformComponentCommand(
            path=base_path + "/transform_component",
            prim_paths=[self._camera.GetPath()],
            include_children=True,
            translate_max_range=(941, 1800.0, 200),
            translate_min_range=(-1033, -1250, 30.0),
            duration=1.0,
        ).do()
        self.dr.commands.ToggleManualModeCommand().do()

    def randomize_scene(self):
        self.dr.commands.RandomizeOnceCommand().do()

    def step(self):
        self.randomize_scene()
        self.kit.update()
        omni.kit.commands.execute("RobotEngineBridgeTickComponent", path=str(self.reb_camera.GetPath()))
        if self.frame % 100 == 0:
            print("FPS: ", self._viewport.get_viewport_window().get_fps())
        self.frame = self.frame + 1

    def add_update_semantics(self, type_label="class"):
        # Add lables to classes
        from pxr import Semantics

        stage = self.kit.context.get_stage()

        for prim in stage.Traverse():
            if not prim.HasAPI(Semantics.SemanticsAPI):
                sem = Semantics.SemanticsAPI.Apply(prim, "Semantics")
                sem.CreateSemanticTypeAttr()
                sem.CreateSemanticDataAttr()
            else:
                sem = Semantics.SemanticsAPI.Get(prim, "Semantics")
                continue

            typeAttr = sem.GetSemanticTypeAttr()
            dataAttr = sem.GetSemanticDataAttr()
            if type_label is not None:
                typeAttr.Set(type_label)
            for semantic_label in self.semantic_labels:
                if semantic_label in prim.GetPath().pathString.lower():
                    dataAttr.Set(semantic_label)
                elif (
                    "rackshelf" in prim.GetPath().pathString.lower()
                    or "palette" in prim.GetPath().pathString.lower()
                    or "forklift" in prim.GetPath().pathString.lower()
                    or "box" in prim.GetPath().pathString.lower()
                ):
                    dataAttr.Set("obstacle")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Freespace Segmentation data")
    parser.add_argument(
        "--scenario",
        type=str,
        default="/Environments/Simple_Warehouse/warehouse_with_forklifts.usd",
        help="Scenario to load from omniverse server",
    )
    parser.add_argument("--semantic_labels", type=list, nargs="+", default=["floor", "wall"], help="Class labels")
    parser.add_argument("--test", default=False, action="store_true", help="Run in test mode")

    args, unknown = parser.parse_known_args()
    sample = FreespaceSegmentation(args.scenario, args.semantic_labels)

    if sample.create_stage():
        sample.create_camera()
        sample.add_update_semantics()
        sample.kit.update()
        sample.configure_randomization()
        from omni.isaac.core.utils.stage import is_stage_loading

        print("Loading stage...")
        while is_stage_loading():
            sample.kit.update()
        print("Loading Complete")

        sample.create_bridge_components()
        sample.configure_bridge()
        sample.start()
        while sample.kit.app.is_running():
            sample.step()
            if args.test is True:
                break
        sample.stop()
    sample.close()
