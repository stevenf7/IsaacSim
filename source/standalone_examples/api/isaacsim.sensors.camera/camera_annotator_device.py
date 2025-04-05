# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

import isaacsim.core.utils.numpy.rotations as rot_utils
import numpy as np
import warp as wp
from isaacsim.core.api import World
from isaacsim.sensors.camera import Camera


def test_camera_annotator_data(test_name, data, expected_class, expected_dtype, expected_shape):
    print(f"{test_name}: data.shape: {data.shape}; dtype: {data.dtype}; type: {type(data)}")
    if not isinstance(data, expected_class):
        raise Exception(f"Data is {type(data)} but expected {expected_class}")
    if data.dtype != expected_dtype:
        raise Exception(f"Data dtype is {data.dtype} but expected {expected_dtype}")
    if data.shape != expected_shape:
        raise Exception(f"Data shape is {data.shape} but expected {expected_shape}")


my_world = World(stage_units_in_meters=1.0)
camera_orientation = rot_utils.euler_angles_to_quats(np.array([0, 90, 0]), degrees=True)
camera_resolution = (256, 256)
camera_position = np.array([0.0, 0.0, 25.0])

camera_default = Camera(
    prim_path="/World/camera_default",
    position=camera_position,
    orientation=camera_orientation,
    resolution=camera_resolution,
)
camera_cpu = Camera(
    prim_path="/World/camera_cpu",
    position=camera_position,
    orientation=camera_orientation,
    resolution=camera_resolution,
    annotator_device="cpu",
)
camera_cuda = Camera(
    prim_path="/World/camera_cuda",
    position=camera_position,
    orientation=camera_orientation,
    resolution=camera_resolution,
    annotator_device="cuda",
)

my_world.scene.add_default_ground_plane()
my_world.reset()

for camera in [camera_default, camera_cpu, camera_cuda]:
    camera.initialize()
    camera.add_normals_to_frame()
    camera.add_motion_vectors_to_frame()
    camera.add_occlusion_to_frame()
    camera.add_distance_to_image_plane_to_frame()
    camera.add_distance_to_camera_to_frame()
    camera.add_bounding_box_2d_tight_to_frame()
    camera.add_bounding_box_2d_loose_to_frame()
    camera.add_bounding_box_3d_to_frame()
    camera.add_semantic_segmentation_to_frame()
    camera.add_instance_id_segmentation_to_frame()
    camera.add_instance_segmentation_to_frame()
    camera.add_pointcloud_to_frame()

# Render a few frames to get the annotator data
for i in range(10):
    my_world.step(render=True)

###################################### rgba #########################################################
print("=" * 80)
print("Testing: rgba")
rgba_shape = (camera_resolution[1], camera_resolution[0], 4)

print("-" * 40)
print("Get rgba data using Camera(annotator_device=None):")
print("---")
# Get the data using the default device (set by annotator_device), or override the default device using cpu or cuda
default_rgba = camera_default.get_rgba()
default_rgba_cpu = camera_default.get_rgba(device="cpu")
default_rgba_cuda = camera_default.get_rgba(device="cuda")
test_camera_annotator_data(
    test_name="None",
    data=default_rgba,
    expected_class=np.ndarray,
    expected_dtype=np.uint8,
    expected_shape=rgba_shape,
)
test_camera_annotator_data(
    test_name="cpu",
    data=default_rgba_cpu,
    expected_class=np.ndarray,
    expected_dtype=np.uint8,
    expected_shape=rgba_shape,
)
test_camera_annotator_data(
    test_name="cuda",
    data=default_rgba_cuda,
    expected_class=wp.array,
    expected_dtype=wp.types.uint8,
    expected_shape=rgba_shape,
)
print("---")
print("[PASS]")
print("---")

print("-" * 40)
print("Get rgba data using Camera(annotator_device='cpu'):")
print("---")
# Get the data using the default device (set by annotator_device), or override the default device using cpu or cuda
cpu_rgba = camera_cpu.get_rgba()
cpu_rgba_cpu = camera_cpu.get_rgba(device="cpu")
cpu_rgba_cuda = camera_cpu.get_rgba(device="cuda")
test_camera_annotator_data(
    test_name="get_rgba_device_None",
    data=cpu_rgba,
    expected_class=np.ndarray,
    expected_dtype=np.uint8,
    expected_shape=rgba_shape,
)
test_camera_annotator_data(
    test_name="get_rgba_device_cpu",
    data=cpu_rgba_cpu,
    expected_class=np.ndarray,
    expected_dtype=np.uint8,
    expected_shape=rgba_shape,
)
test_camera_annotator_data(
    test_name="get_rgba_device_cuda",
    data=cpu_rgba_cuda,
    expected_class=wp.array,
    expected_dtype=wp.types.uint8,
    expected_shape=rgba_shape,
)
print("---")
print("[PASS]")
print("---")

print("-" * 40)
print(f"Get rgba data using Camera(annotator_device='cuda'):")
# Get the data using the default device (set by annotator_device), or override the default device using cpu or cuda
cuda_rgba = camera_cuda.get_rgba()
cuda_rgba_cpu = camera_cuda.get_rgba(device="cpu")
cuda_rgba_cuda = camera_cuda.get_rgba(device="cuda")
test_camera_annotator_data(
    test_name="get_rgba_device_None",
    data=cuda_rgba,
    expected_class=wp.array,
    expected_dtype=wp.types.uint8,
    expected_shape=rgba_shape,
)
test_camera_annotator_data(
    test_name="get_rgba_device_cpu",
    data=cuda_rgba_cpu,
    expected_class=np.ndarray,
    expected_dtype=np.uint8,
    expected_shape=rgba_shape,
)
test_camera_annotator_data(
    test_name="get_rgba_device_cuda",
    data=cuda_rgba_cuda,
    expected_class=wp.array,
    expected_dtype=wp.types.uint8,
    expected_shape=rgba_shape,
)
print("---")
print("[PASS]")
print("---")


###################################### rgb #########################################################
print("=" * 80)
print("Testing: rgb")
rgb_shape = (camera_resolution[1], camera_resolution[0], 3)

print("-" * 40)
print("Get rgb data using Camera(annotator_device=None):")
print("---")
# Get the data using the default device (set by annotator_device), or override the default device using cpu or cuda
default_rgb = camera_default.get_rgb()
default_rgb_cpu = camera_default.get_rgb(device="cpu")
default_rgb_cuda = camera_default.get_rgb(device="cuda")
test_camera_annotator_data(
    test_name="get_rgb_device_None",
    data=default_rgb,
    expected_class=np.ndarray,
    expected_dtype=np.uint8,
    expected_shape=rgb_shape,
)
test_camera_annotator_data(
    test_name="get_rgb_device_cpu",
    data=default_rgb_cpu,
    expected_class=np.ndarray,
    expected_dtype=np.uint8,
    expected_shape=rgb_shape,
)
test_camera_annotator_data(
    test_name="get_rgb_device_cuda",
    data=default_rgb_cuda,
    expected_class=wp.array,
    expected_dtype=wp.types.uint8,
    expected_shape=rgb_shape,
)
print("---")
print("[PASS]")
print("---")

print("-" * 40)
print("Get rgb data using Camera(annotator_device='cpu'):")
print("---")
# Get the data using the default device (set by annotator_device), or override the default device using cpu or cuda
cpu_rgb = camera_cpu.get_rgb()
cpu_rgb_cpu = camera_cpu.get_rgb(device="cpu")
cpu_rgb_cuda = camera_cpu.get_rgb(device="cuda")
test_camera_annotator_data(
    test_name="get_rgb_device_None",
    data=cpu_rgb,
    expected_class=np.ndarray,
    expected_dtype=np.uint8,
    expected_shape=rgb_shape,
)
test_camera_annotator_data(
    test_name="get_rgb_device_cpu",
    data=cpu_rgb_cpu,
    expected_class=np.ndarray,
    expected_dtype=np.uint8,
    expected_shape=rgb_shape,
)
test_camera_annotator_data(
    test_name="get_rgb_device_cuda",
    data=cpu_rgb_cuda,
    expected_class=wp.array,
    expected_dtype=wp.types.uint8,
    expected_shape=rgb_shape,
)
print("---")
print("[PASS]")
print("---")

print("-" * 40)
print("Get rgb data using Camera(annotator_device='cuda'):")
print("---")
# Get the data using the default device (set by annotator_device), or override the default device using cpu or cuda
cuda_rgb = camera_cuda.get_rgb()
cuda_rgb_cpu = camera_cuda.get_rgb(device="cpu")
cuda_rgb_cuda = camera_cuda.get_rgb(device="cuda")
test_camera_annotator_data(
    test_name="get_rgb_device_None",
    data=cuda_rgb,
    expected_class=wp.array,
    expected_dtype=wp.types.uint8,
    expected_shape=rgb_shape,
)
test_camera_annotator_data(
    test_name="get_rgb_device_cpu",
    data=cuda_rgb_cpu,
    expected_class=np.ndarray,
    expected_dtype=np.uint8,
    expected_shape=rgb_shape,
)
test_camera_annotator_data(
    test_name="get_rgb_device_cuda",
    data=cuda_rgb_cuda,
    expected_class=wp.array,
    expected_dtype=wp.types.uint8,
    expected_shape=rgb_shape,
)
print("---")
print("[PASS]")
print("---")


###################################### depth #########################################################
print("=" * 80)
print("Testing: depth")
depth_shape = (camera_resolution[1], camera_resolution[0])

print("-" * 40)
print("Get depth data using Camera(annotator_device=None):")
print("---")
default_depth = camera_default.get_depth()
default_depth_cpu = camera_default.get_depth(device="cpu")
default_depth_cuda = camera_default.get_depth(device="cuda")
test_camera_annotator_data(
    test_name="get_depth_device_None",
    data=default_depth,
    expected_class=np.ndarray,
    expected_dtype=np.float32,
    expected_shape=depth_shape,
)
test_camera_annotator_data(
    test_name="get_depth_device_cpu",
    data=default_depth_cpu,
    expected_class=np.ndarray,
    expected_dtype=np.float32,
    expected_shape=depth_shape,
)
test_camera_annotator_data(
    test_name="get_depth_device_cuda",
    data=default_depth_cuda,
    expected_class=wp.array,
    expected_dtype=wp.types.float32,
    expected_shape=depth_shape,
)
print("---")
print("[PASS]")
print("---")


print("-" * 40)
print("Get depth data using Camera(annotator_device='cpu'):")
print("---")
cpu_depth = camera_cpu.get_depth()
cpu_depth_cpu = camera_cpu.get_depth(device="cpu")
cpu_depth_cuda = camera_cpu.get_depth(device="cuda")
test_camera_annotator_data(
    test_name="get_depth_device_None",
    data=cpu_depth,
    expected_class=np.ndarray,
    expected_dtype=np.float32,
    expected_shape=depth_shape,
)
test_camera_annotator_data(
    test_name="get_depth_device_cpu",
    data=cpu_depth_cpu,
    expected_class=np.ndarray,
    expected_dtype=np.float32,
    expected_shape=depth_shape,
)
test_camera_annotator_data(
    test_name="get_depth_device_cuda",
    data=cpu_depth_cuda,
    expected_class=wp.array,
    expected_dtype=wp.types.float32,
    expected_shape=depth_shape,
)
print("---")
print("[PASS]")
print("---")


print("-" * 40)
print("Get depth data using Camera(annotator_device='cuda'):")
print("---")
cuda_depth = camera_cuda.get_depth()
cuda_depth_cpu = camera_cuda.get_depth(device="cpu")
cuda_depth_cuda = camera_cuda.get_depth(device="cuda")
test_camera_annotator_data(
    test_name="get_depth_device_None",
    data=cuda_depth,
    expected_class=wp.array,
    expected_dtype=wp.types.float32,
    expected_shape=depth_shape,
)
test_camera_annotator_data(
    test_name="get_depth_device_cpu",
    data=cuda_depth_cpu,
    expected_class=np.ndarray,
    expected_dtype=np.float32,
    expected_shape=depth_shape,
)
test_camera_annotator_data(
    test_name="get_depth_device_cuda",
    data=cuda_depth_cuda,
    expected_class=wp.array,
    expected_dtype=wp.types.float32,
    expected_shape=depth_shape,
)
print("---")
print("[PASS]")
print("---")


###################################### pointcloud #########################################################
print("=" * 80)
print("Testing: pointcloud")
pointcloud_shape = (256 * 256, 3)

world_frame_list = [True, False]

print("-" * 40)
print("Get pointcloud data using Camera(annotator_device=None):")
print("---")
for world_frame in world_frame_list:
    print(f"world_frame: {world_frame}")
    print("---")
    default_pointcloud = camera_default.get_pointcloud(world_frame=world_frame)
    default_pointcloud_cpu = camera_default.get_pointcloud(device="cpu", world_frame=world_frame)
    default_pointcloud_cuda = camera_default.get_pointcloud(device="cuda", world_frame=world_frame)
    test_camera_annotator_data(
        test_name=f"get_pointcloud_device_None_world_frame_{world_frame}",
        data=default_pointcloud,
        expected_class=np.ndarray,
        expected_dtype=np.float32,
        expected_shape=pointcloud_shape,
    )
    test_camera_annotator_data(
        test_name=f"get_pointcloud_device_cpu_world_frame_{world_frame}",
        data=default_pointcloud_cpu,
        expected_class=np.ndarray,
        expected_dtype=np.float32,
        expected_shape=pointcloud_shape,
    )
    test_camera_annotator_data(
        test_name=f"get_pointcloud_device_cuda_world_frame_{world_frame}",
        data=default_pointcloud_cuda,
        expected_class=wp.array,
        expected_dtype=wp.types.float32,
        expected_shape=pointcloud_shape,
    )
    print("---")
    print("[PASS]")
    print("---")


print("-" * 40)
print("Get pointcloud data using Camera(annotator_device='cpu'):")
print("---")
for world_frame in world_frame_list:
    print(f"world_frame: {world_frame}")
    print("---")
    cpu_pointcloud = camera_cpu.get_pointcloud(world_frame=world_frame)
    cpu_pointcloud_cpu = camera_cpu.get_pointcloud(device="cpu", world_frame=world_frame)
    cpu_pointcloud_cuda = camera_cpu.get_pointcloud(device="cuda", world_frame=world_frame)
    test_camera_annotator_data(
        test_name=f"get_pointcloud_device_None_world_frame_{world_frame}",
        data=cpu_pointcloud,
        expected_class=np.ndarray,
        expected_dtype=np.float32,
        expected_shape=pointcloud_shape,
    )
    test_camera_annotator_data(
        test_name=f"get_pointcloud_device_cpu_world_frame_{world_frame}",
        data=cpu_pointcloud_cpu,
        expected_class=np.ndarray,
        expected_dtype=np.float32,
        expected_shape=pointcloud_shape,
    )
    test_camera_annotator_data(
        test_name=f"get_pointcloud_device_cuda_world_frame_{world_frame}",
        data=cpu_pointcloud_cuda,
        expected_class=wp.array,
        expected_dtype=wp.types.float32,
        expected_shape=pointcloud_shape,
    )
    print("---")
    print("[PASS]")
    print("---")


print("-" * 40)
print("Get pointcloud data using Camera(annotator_device='cuda'):")
print("---")
for world_frame in world_frame_list:
    print(f"world_frame: {world_frame}")
    print("---")
    cuda_pointcloud = camera_cuda.get_pointcloud(world_frame=world_frame)
    cuda_pointcloud_cpu = camera_cuda.get_pointcloud(device="cpu", world_frame=world_frame)
    cuda_pointcloud_cuda = camera_cuda.get_pointcloud(device="cuda", world_frame=world_frame)
    test_camera_annotator_data(
        test_name=f"get_pointcloud_device_None_world_frame_{world_frame}",
        data=cuda_pointcloud,
        expected_class=wp.array,
        expected_dtype=wp.types.float32,
        expected_shape=pointcloud_shape,
    )
    test_camera_annotator_data(
        test_name=f"get_pointcloud_device_cpu_world_frame_{world_frame}",
        data=cuda_pointcloud_cpu,
        expected_class=np.ndarray,
        expected_dtype=np.float32,
        expected_shape=pointcloud_shape,
    )
    test_camera_annotator_data(
        test_name=f"get_pointcloud_device_cuda_world_frame_{world_frame}",
        data=cuda_pointcloud_cuda,
        expected_class=wp.array,
        expected_dtype=wp.types.float32,
        expected_shape=pointcloud_shape,
    )
    print("---")
    print("[PASS]")
    print("---")


###################################### pointcloud - from depth #######################################################
print("=" * 80)
print("Testing: pointcloud - from depth (remove pointcloud from frame)")
pointcloud_shape = (256 * 256, 3)

camera.remove_pointcloud_from_frame()
simulation_app.update()
my_world.step(render=True)

world_frame_list = [True, False]

print("-" * 40)
print("Get pointcloud data using Camera(annotator_device=None):")
print("---")
for world_frame in world_frame_list:
    print(f"world_frame: {world_frame}")
    print("---")
    default_pointcloud = camera_default.get_pointcloud(world_frame=world_frame)
    default_pointcloud_cpu = camera_default.get_pointcloud(device="cpu", world_frame=world_frame)
    default_pointcloud_cuda = camera_default.get_pointcloud(device="cuda", world_frame=world_frame)
    test_camera_annotator_data(
        test_name=f"get_pointcloud_device_None_world_frame_{world_frame}",
        data=default_pointcloud,
        expected_class=np.ndarray,
        expected_dtype=np.float32,
        expected_shape=pointcloud_shape,
    )
    test_camera_annotator_data(
        test_name=f"get_pointcloud_device_cpu_world_frame_{world_frame}",
        data=default_pointcloud_cpu,
        expected_class=np.ndarray,
        expected_dtype=np.float32,
        expected_shape=pointcloud_shape,
    )
    test_camera_annotator_data(
        test_name=f"get_pointcloud_device_cuda_world_frame_{world_frame}",
        data=default_pointcloud_cuda,
        expected_class=wp.array,
        expected_dtype=wp.types.float32,
        expected_shape=pointcloud_shape,
    )
    print("---")
    print("[PASS]")
    print("---")


print("-" * 40)
print("Get pointcloud data using Camera(annotator_device='cpu'):")
print("---")
for world_frame in world_frame_list:
    print(f"world_frame: {world_frame}")
    print("---")
    cpu_pointcloud = camera_cpu.get_pointcloud(world_frame=world_frame)
    cpu_pointcloud_cpu = camera_cpu.get_pointcloud(device="cpu", world_frame=world_frame)
    cpu_pointcloud_cuda = camera_cpu.get_pointcloud(device="cuda", world_frame=world_frame)
    test_camera_annotator_data(
        test_name=f"get_pointcloud_device_None_world_frame_{world_frame}",
        data=cpu_pointcloud,
        expected_class=np.ndarray,
        expected_dtype=np.float32,
        expected_shape=pointcloud_shape,
    )
    test_camera_annotator_data(
        test_name=f"get_pointcloud_device_cpu_world_frame_{world_frame}",
        data=cpu_pointcloud_cpu,
        expected_class=np.ndarray,
        expected_dtype=np.float32,
        expected_shape=pointcloud_shape,
    )
    test_camera_annotator_data(
        test_name=f"get_pointcloud_device_cuda_world_frame_{world_frame}",
        data=cpu_pointcloud_cuda,
        expected_class=wp.array,
        expected_dtype=wp.types.float32,
        expected_shape=pointcloud_shape,
    )
    print("---")
    print("[PASS]")
    print("---")


print("-" * 40)
print("Get pointcloud data using Camera(annotator_device='cuda'):")
print("---")
for world_frame in world_frame_list:
    print(f"world_frame: {world_frame}")
    print("---")
    cuda_pointcloud = camera_cuda.get_pointcloud(world_frame=world_frame)
    cuda_pointcloud_cpu = camera_cuda.get_pointcloud(device="cpu", world_frame=world_frame)
    cuda_pointcloud_cuda = camera_cuda.get_pointcloud(device="cuda", world_frame=world_frame)
    test_camera_annotator_data(
        test_name=f"get_pointcloud_device_None_world_frame_{world_frame}",
        data=cuda_pointcloud,
        expected_class=wp.array,
        expected_dtype=wp.types.float32,
        expected_shape=pointcloud_shape,
    )
    test_camera_annotator_data(
        test_name=f"get_pointcloud_device_cpu_world_frame_{world_frame}",
        data=cuda_pointcloud_cpu,
        expected_class=np.ndarray,
        expected_dtype=np.float32,
        expected_shape=pointcloud_shape,
    )
    test_camera_annotator_data(
        test_name=f"get_pointcloud_device_cuda_world_frame_{world_frame}",
        data=cuda_pointcloud_cuda,
        expected_class=wp.array,
        expected_dtype=wp.types.float32,
        expected_shape=pointcloud_shape,
    )
    print("---")
    print("[PASS]")
    print("---")

###################################### frame #########################################################
print("=" * 80)
print("Testing: current frame")
annotators_without_cuda_support = {"bounding_box_2d_tight", "bounding_box_2d_loose", "bounding_box_3d"}
annotators_with_cuda_support = {
    "normals",
    "motion_vectors",
    "occlusion",
    "distance_to_image_plane",
    "distance_to_camera",
    "semantic_segmentation",
    "instance_id_segmentation",
    "instance_segmentation",
    "pointcloud",
}

current_frame_default = camera_default.get_current_frame()
current_frame_cpu = camera_cpu.get_current_frame()
current_frame_cuda = camera_cuda.get_current_frame()

print("-" * 40)
print("Current frame from Camera(annotator_device=None):")
print("---")
# Current frame from the default and cpu cameras should only have numpy arrays
for key in current_frame_default.keys():
    data = current_frame_default[key]
    if isinstance(data, dict):
        data = data["data"]
    if key in annotators_with_cuda_support:
        print(f"With CUDA: {key}, value type: {type(data)}")
        if not isinstance(data, np.ndarray):
            raise Exception(f"Data is {type(data)} but expected wp.array")
    if key in annotators_without_cuda_support:
        print(f"Without CUDA: {key}, value type: {type(data)}")
        if not isinstance(data, np.ndarray):
            raise Exception(f"Data is {type(data)} but expected np.ndarray")
print("---")
print("[PASS]")
print("---")


print("-" * 40)
print("Current frame from Camera(annotator_device='cpu'):")
print("---")
for key in current_frame_cpu.keys():
    data = current_frame_cpu[key]
    if isinstance(data, dict):
        data = data["data"]
    if key in annotators_with_cuda_support:
        print(f"With CUDA: {key}, value type: {type(data)}")
        if not isinstance(data, np.ndarray):
            raise Exception(f"Data is {type(data)} but expected wp.array")
    if key in annotators_without_cuda_support:
        print(f"Without CUDA: {key}, value type: {type(data)}")
        if not isinstance(data, np.ndarray):
            raise Exception(f"Data is {type(data)} but expected np.ndarray")
print("---")
print("[PASS]")
print("---")

print("-" * 40)
print("Current frame from Camera(annotator_device='cuda'):")
print("---")
# Current frame from the cuda camera should have wp.arrays for cuda supported annotators and numpy arrays for the rest
for key in current_frame_cuda.keys():
    data = current_frame_cuda[key]
    if isinstance(data, dict):
        data = data["data"]
    if key in annotators_with_cuda_support:
        print(f"With CUDA: {key}, value type: {type(data)}")
        if not isinstance(data, wp.array):
            raise Exception(f"Data is {type(data)} but expected wp.array")
    if key in annotators_without_cuda_support:
        print(f"Without CUDA: {key}, value type: {type(data)}")
        if not isinstance(data, np.ndarray):
            raise Exception(f"Data is {type(data)} but expected np.ndarray")
print("---")
print("[PASS]")
print("---")

simulation_app.close()
