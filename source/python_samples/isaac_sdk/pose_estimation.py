import random
import os
import omni
from pxr import UsdGeom, Usd, Gf
from omni.isaac.synthetic_utils import OmniKitHelper
from omni.isaac.synthetic_utils import DomainRandomization
from omni.isaac.synthetic_utils import SyntheticDataHelper

from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server

import carb.tokens

CONFIG = {
    "experience": f'{os.environ["EXP_PATH"]}/isaac-sim-python.json',
    "width": 1280,
    "height": 720,
    "sync_loads": True,
    "headless": True,
    "renderer": "RayTracedLighting",
}

# D435
FOCAL_LEN = 1.93
HORIZONTAL_APERTURE = 2.682
VERTICAL_APERTURE = 1.509
FOCUS_DIST = 400

RANDOMIZE_SCENE_EVERY_N_STEPS = 10


class DualCameraSample:
    def __init__(self):
        self.kit = OmniKitHelper(config=CONFIG)
        import omni.physx
        from omni.isaac.robot_engine_bridge import _robot_engine_bridge

        self._re_bridge = _robot_engine_bridge.acquire_robot_engine_bridge_interface()
        self._viewport = omni.kit.viewport.get_viewport_interface()

        self.dr_helper = DomainRandomization()
        self.sd_helper = SyntheticDataHelper()
        self.frame = 0

    def start(self):
        self.kit.play()

    def stop(self):
        self.kit.stop()
        self._re_bridge.destroy_application()

    def create_stage(self):
        # open base stage and set up axis to Z
        stage = self.kit.get_stage()
        rootLayer = stage.GetRootLayer()
        rootLayer.SetPermissionToEdit(True)
        with Usd.EditContext(stage, rootLayer):
            UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        # make two prims, one for env and one for just the room
        # this allows us to add other prims to environment for randomization and still hide them all at once
        self._environment = stage.DefinePrim("/environment", "Xform")

        self._room = stage.DefinePrim("/environment/room", "Xform")

        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return False
        self._asset_path = nucleus_server + "/Isaac"
        stage_path = self._asset_path + "/Environments/Simple_Room/simple_room.usd"

        self._room.GetReferences().AddReference(stage_path)

        self._target_prim = self.kit.create_prim(
            "/objects/cube", "Cube", translation=(0, 0, 100), scale=(10, 10, 50), semantic_label="target"
        )
        return True

    def create_camera(self):
        self._camera = self.kit.create_prim(
            "/World/Camera",
            "Camera",
            translation=(0.0, 0.0, 0.0),
            attributes={
                "focusDistance": FOCUS_DIST,
                "focalLength": FOCAL_LEN,
                "horizontalAperture": HORIZONTAL_APERTURE,
                "verticalAperture": VERTICAL_APERTURE,
            },
        )

        # activate new camera
        self._viewport.get_viewport_window().set_active_camera(str(self._camera.GetPath()))

        # the camera reference frame between sdk and sim seems to be flipped 180 on x
        # this prim acts as a proxy to do that coordinate transformation
        self._camera_proxy = self.kit.create_prim("/World/Camera/proxy", "Xform", rotation=(180, 0, 0))

    def create_bridge_components(self):
        import omni.isaac.RobotEngineBridgeSchema as REBSchema

        stage = self.kit.get_stage()

        def setup_base_component(prim, time_offset):
            prim.CreateNodeNameAttr("interface")
            prim.CreateEnabledAttr(True)
            prim.CreateTimeOffsetAttr(time_offset)

        self.occluded_provider = REBSchema.RobotEngineCamera.Define(stage, "/World/REB_Occluded_Provider")
        setup_base_component(self.occluded_provider, 0.0)
        self.occluded_provider.CreateRgbOutputComponentAttr("output")
        self.occluded_provider.CreateRgbOutputChannelAttr("encoder_color")

        self.occluded_provider.CreateDepthOutputComponentAttr("output")
        self.occluded_provider.CreateDepthOutputChannelAttr("encoder_depth")

        self.occluded_provider.CreateSegmentationOutputComponentAttr("output")
        self.occluded_provider.CreateSegmentationOutputChannelAttr("encoder_segmentation")

        self.occluded_provider.CreateBoundingBox2DOutputComponentAttr("output")
        self.occluded_provider.CreateBoundingBox2DOutputChannelAttr("encoder_bbox")
        self.occluded_provider.CreateBoundingBox2DClassListAttr("")

        self.occluded_provider.CreateBoundingBox3DOutputComponentAttr("output")
        self.occluded_provider.CreateBoundingBox3DOutputChannelAttr("encoder_bbox3d")
        self.occluded_provider.CreateBoundingBox3DClassListAttr("")

        self.occluded_provider.CreateRgbEnabledAttr(True)
        self.occluded_provider.CreateDepthEnabledAttr(False)
        self.occluded_provider.CreateSegmentationEnabledAttr(True)
        self.occluded_provider.CreateBoundingBox2DEnabledAttr(False)
        self.occluded_provider.CreateBoundingBox3DEnabledAttr(False)

        self.unoccluded_provider = REBSchema.RobotEngineCamera.Define(stage, "/World/REB_Unoccluded_Provider")
        setup_base_component(self.unoccluded_provider, 0.0)
        self.unoccluded_provider.CreateRgbOutputComponentAttr("output")
        self.unoccluded_provider.CreateRgbOutputChannelAttr("decoder_color")

        self.unoccluded_provider.CreateDepthOutputComponentAttr("output")
        self.unoccluded_provider.CreateDepthOutputChannelAttr("decoder_depth")

        self.unoccluded_provider.CreateSegmentationOutputComponentAttr("output")
        self.unoccluded_provider.CreateSegmentationOutputChannelAttr("decoder_segmentation")

        self.unoccluded_provider.CreateBoundingBox2DOutputComponentAttr("output")
        self.unoccluded_provider.CreateBoundingBox2DOutputChannelAttr("decoder_bbox")
        self.unoccluded_provider.CreateBoundingBox2DClassListAttr("")

        self.unoccluded_provider.CreateBoundingBox3DOutputComponentAttr("output")
        self.unoccluded_provider.CreateBoundingBox3DOutputChannelAttr("decoder_bbox3d")
        self.unoccluded_provider.CreateBoundingBox3DClassListAttr("")

        self.unoccluded_provider.CreateRgbEnabledAttr(True)
        self.unoccluded_provider.CreateDepthEnabledAttr(False)
        self.unoccluded_provider.CreateSegmentationEnabledAttr(True)
        self.unoccluded_provider.CreateBoundingBox2DEnabledAttr(False)
        self.unoccluded_provider.CreateBoundingBox3DEnabledAttr(False)

        # create rigid body sink to publish ground truth pose information
        self.rbs_provider = REBSchema.RobotEngineRigidBodySink.Define(stage, "/World/REB_RigidBodiesSink")
        setup_base_component(self.rbs_provider, 0.0)
        self.rbs_provider.CreateOutputComponentAttr("output")
        self.rbs_provider.CreateOutputChannelAttr("bodies")
        self.rbs_provider.CreateRigidBodyPrimsRel().SetTargets(
            [self._camera_proxy.GetPath(), self._target_prim.GetPath()]
        )

    def configure_bridge(self):
        asset_path = os.path.abspath(
            carb.tokens.get_tokens_interface().resolve(
                f'{os.environ["ISAAC_PATH"]}/exts/omni.isaac.robot_engine_bridge/'
            )
        )
        # This path can be changed as long as the absolute path is supplied
        # You could also generate one via python here, save it to a temp folder and point to it
        json_path = os.path.abspath(
            carb.tokens.get_tokens_interface().resolve(
                f'{os.environ["ISAAC_PATH"]}/exts/omni.isaac.robot_engine_bridge/resources/isaac_engine/json/isaacsim.app.json'
            )
        )
        # start bridge application
        self._re_bridge.create_application(asset_path, json_path, [], [])

    def configure_randomization(self):
        texture_list = [
            self._asset_path + "/Samples/DR/Materials/Textures/checkered.png",
            self._asset_path + "/Samples/DR/Materials/Textures/marble_tile.png",
            self._asset_path + "/Samples/DR/Materials/Textures/picture_a.png",
            self._asset_path + "/Samples/DR/Materials/Textures/picture_b.png",
            self._asset_path + "/Samples/DR/Materials/Textures/textured_wall.png",
            self._asset_path + "/Samples/DR/Materials/Textures/checkered_color.png",
        ]
        base_path = str(self._room.GetPath())
        self.texture_comp = self.dr_helper.create_texture_comp([base_path], False, texture_list)
        # self.color_comp = self.dr_helper.create_color_comp([base_path+"/floor"])
        # disable automatic DR, we run it ourselves in the step function

        # add a movement and rotation component
        # the movement component is offset by 100cm in z so that the object remains above the table
        self.movement_comp = self.dr_helper.create_movement_comp(
            [str(self._target_prim.GetPath())], min_range=(-10, -10, -10 + 100), max_range=(10, 10, 10 + 100)
        )
        self.rotation_comp = self.dr_helper.create_rotation_comp([str(self._target_prim.GetPath())])

        self.dr_helper.toggle_manual_mode()

    def randomize_camera(self):
        # randomize camera position
        self._viewport.get_viewport_window().set_camera_position(
            str(self._camera.GetPath()),
            random.randrange(-250, 250),
            random.randrange(-250, 250),
            random.randrange(10, 250),
            True,
        )

        # get target pose and point camera at it
        pose = omni.usd.get_world_transform_matrix(self._target_prim)
        # can specify an offset on target position
        target = pose.ExtractTranslation() + Gf.Vec3d(0, 0, 0)

        self._viewport.get_viewport_window().set_camera_target(
            str(self._camera.GetPath()), target[0], target[1], target[2], True
        )

    def randomize_scene(self):
        self.dr_helper.randomize_once()

    def toggle_environment(self, state):
        imageable = UsdGeom.Imageable(self._environment)
        if state:
            imageable.MakeVisible()
        else:
            imageable.MakeInvisible()

    def step(self):
        # randomize camera every frame
        self.randomize_camera()
        # randomize textures every 10 frames
        if self.frame % RANDOMIZE_SCENE_EVERY_N_STEPS == 0:
            self.randomize_scene()

        # turn both cameras off so that we don't send an image when time is stepped
        self.occluded_provider.GetEnabledAttr().Set(False)
        self.unoccluded_provider.GetEnabledAttr().Set(False)
        # disable rigid body sink until the final image is sent out so its only published once
        self.rbs_provider.GetEnabledAttr().Set(False)
        self.toggle_environment(True)
        self.kit.update(1.0 / 60.0)
        # render occluded view
        self.occluded_provider.GetEnabledAttr().Set(True)
        self.unoccluded_provider.GetEnabledAttr().Set(False)
        self.kit.update(0)
        # hide everything but the object
        self.occluded_provider.GetEnabledAttr().Set(False)
        self.unoccluded_provider.GetEnabledAttr().Set(False)
        self.toggle_environment(False)
        self.kit.update(0)
        # render unoccluded view
        self.occluded_provider.GetEnabledAttr().Set(False)
        self.unoccluded_provider.GetEnabledAttr().Set(True)
        self.rbs_provider.GetEnabledAttr().Set(True)
        self.kit.update(0)

        # output fps every 100 frames
        if self.frame % 100 == 0:
            print("FPS: ", self.kit.editor.get_fps())
        self.frame = self.frame + 1


if __name__ == "__main__":
    sample = DualCameraSample()
    # On start if state creation was successful
    if sample.create_stage():
        sample.create_camera()
        sample.configure_randomization()
        # wait for stage to load
        while sample.kit.is_loading():
            sample.kit.update(0)

        sample.create_bridge_components()
        sample.configure_bridge()

        sample.start()

        while sample.kit.app.is_running():
            sample.step()

        sample.stop()
