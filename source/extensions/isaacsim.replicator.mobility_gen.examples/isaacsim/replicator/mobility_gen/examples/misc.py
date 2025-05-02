import os
from typing import Tuple

from isaacsim.core.utils.stage import add_reference_to_stage, get_current_stage
from isaacsim.replicator.mobility_gen.impl.camera import MobilityGenCamera
from isaacsim.replicator.mobility_gen.impl.common import Module


class HawkCamera(Module):

    usd_url: str = (
        "http://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/4.2/Isaac/Sensors/LeopardImaging/Hawk/hawk_v1.1_nominal.usd"
    )
    resolution: Tuple[int, int] = (960, 600)
    left_camera_path: str = "left/camera_left"
    right_camera_path: str = "right/camera_right"

    def __init__(self, left: MobilityGenCamera, right: MobilityGenCamera):
        self.left = left
        self.right = right

    @classmethod
    def build(cls, prim_path: str) -> "HawkCamera":

        stage = get_current_stage()

        add_reference_to_stage(usd_path=cls.usd_url, prim_path=prim_path)

        return cls.attach(prim_path)

    @classmethod
    def attach(cls, prim_path: str) -> "HawkCamera":

        left_camera = MobilityGenCamera(os.path.join(prim_path, cls.left_camera_path), cls.resolution)
        right_camera = MobilityGenCamera(os.path.join(prim_path, cls.right_camera_path), cls.resolution)

        return HawkCamera(left_camera, right_camera)
