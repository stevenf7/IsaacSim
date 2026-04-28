# -- Test setup --
import omni.usd
from pxr import UsdGeom

stage = omni.usd.get_context().get_stage()
UsdGeom.Camera.Define(stage, "/World/Camera")

CAMERA_STAGE_PATH = "/World/Camera"


def get_active_viewport():
    class _Viewport:
        def get_render_product_path(self):
            return "/Render/RenderProduct"

    return _Viewport()


def set_camera_prim_path(render_product_path, camera_path):
    pass


render_product_path = get_active_viewport().get_render_product_path()
# -- End test setup --

# [set-camera]
# Grab the render product and set the camera prim
render_product_path = get_active_viewport().get_render_product_path()
set_camera_prim_path(render_product_path, CAMERA_STAGE_PATH)
# [/set-camera]

# [cpu-noise-kernel]
import numpy as np


def image_gaussian_noise_np(data_in: np.ndarray, seed: int, sigma: float = 25.0):
    np.random.seed(seed)
    return data_in + sigma * np.random.randn(*data_in.shape)


# [/cpu-noise-kernel]

# [gpu-noise-kernel]
import warp as wp


@wp.kernel
def image_gaussian_noise_warp(
    data_in: wp.array3d(dtype=wp.uint8), data_out: wp.array3d(dtype=wp.uint8), seed: int, sigma: float = 0.5
):
    i, j = wp.tid()
    dim_i = data_out.shape[0]
    dim_j = data_out.shape[1]
    pixel_id = i * dim_i + j
    state_r = wp.rand_init(seed, pixel_id + (dim_i * dim_j * 0))
    state_g = wp.rand_init(seed, pixel_id + (dim_i * dim_j * 1))
    state_b = wp.rand_init(seed, pixel_id + (dim_i * dim_j * 2))

    data_out[i, j, 0] = wp.uint8(float(data_in[i, j, 0]) + (255.0 * sigma * wp.randn(state_r)))
    data_out[i, j, 1] = wp.uint8(float(data_in[i, j, 1]) + (255.0 * sigma * wp.randn(state_g)))
    data_out[i, j, 2] = wp.uint8(float(data_in[i, j, 2]) + (255.0 * sigma * wp.randn(state_b)))


# [/gpu-noise-kernel]

# [register-annotator]
import omni.replicator.core as rep

rep.annotators.register(
    name="rgb_gaussian_noise",
    annotator=rep.annotators.augment_compose(
        source_annotator=rep.annotators.get("rgb", device="cuda"),
        augmentations=[
            rep.annotators.Augmentation.from_function(
                image_gaussian_noise_warp, sigma=0.1, seed=1234, data_out_shape=(-1, -1, 3)
            ),
        ],
    ),
)
# [/register-annotator]

# -- Test setup --
import omni.syntheticdata

# -- End test setup --

# [register-writer]
rep.writers.register_node_writer(
    name="CustomROS2PublishImage",
    node_type_id="isaacsim.ros2.bridge.ROS2PublishImage",
    annotators=[
        "rgb_gaussian_noise",
        omni.syntheticdata.SyntheticData.NodeConnectionTemplate(
            "IsaacReadSimulationTime", attributes_mapping={"outputs:simulationTime": "inputs:timeStamp"}
        ),
    ],
    category="custom",
)

(
    rep.WriterRegistry._default_writers.append("CustomROS2PublishImage")
    if "CustomROS2PublishImage" not in rep.WriterRegistry._default_writers
    else None
)
# [/register-writer]

# [attach-writer]
writer = rep.writers.get("CustomROS2PublishImage")
writer.initialize(topicName="rgb_augmented", frameId="sim_camera")
writer.attach([render_product_path])
# [/attach-writer]
