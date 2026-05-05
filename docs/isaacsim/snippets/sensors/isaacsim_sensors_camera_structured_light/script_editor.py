from pathlib import Path

import omni.kit.app
from isaacsim.sensors.experimental.rtx import CameraSensor, StructuredLightCamera

# Resolve the bundled structured-light test patterns shipped with the extension.
ext_root = (
    omni.kit.app.get_app().get_extension_manager().get_extension_path_by_module("isaacsim.sensors.experimental.rtx")
)
data_dir = Path(ext_root) / "isaacsim/sensors/experimental/rtx/tests/data/structured_light_camera"
patterns = [data_dir / "patterns" / f"image_{i:02d}.png" for i in range(10)]
direction_texture = data_dir / "projector_opencv_pinhole_4000x2880_2025_10_08_10_51_18.exr"

# 10 patterns spaced over 0 - 2 ms with variable intervals. Rational tuples
# avoid floating-point error at sub-millisecond resolution.
projector_timestamps = [
    (0, 1),
    (19, 100_000),
    (41, 100_000),
    (62, 100_000),
    (4, 5_000),
    (101, 100_000),
    (61, 50_000),
    (141, 100_000),
    (179, 100_000),
    (1, 500),
]

# Create the camera at a root-level path. The projector RectLight prims are
# created at ``/structured_light_camera/projectors`` and cycle automatically
# based on the current simulation time.
cam = StructuredLightCamera(
    "/structured_light_camera",
    projector_light_patterns=patterns,
    projector_direction_texture=direction_texture,
    projector_timestamps=projector_timestamps,
    projector_intensity=150_000.0,
)

# Wrap the camera in a CameraSensor with the rgb annotator to retrieve frames.
sensor = CameraSensor(cam, resolution=(720, 1280), annotators=["rgb"])
