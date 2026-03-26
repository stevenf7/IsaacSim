"""Capture annotator data (depth, normals, segmentation, etc.) from the active viewport.

Injected globals (via isaacsim_send.py --arg):
    annotator: str — Annotator name (default: distance_to_camera).
        Options: rgb, distance_to_camera, distance_to_image_plane, normals,
                 semantic_segmentation, instance_id_segmentation, etc.
    output_path: str — File path for output. .npy for raw array, .png for image
        (default: /tmp/annotator_data.npy).
"""

# Defaults
if "annotator" not in dir():
    annotator = "distance_to_camera"  # noqa: F841
if "output_path" not in dir():
    output_path = "/tmp/annotator_data.npy"  # noqa: F841


async def _capture():
    import omni.kit.viewport.utility as viewport_utils

    from isaacsim.test.utils.image_capture import capture_viewport_annotator_data_async
    from isaacsim.test.utils.image_io import save_annotator_data

    viewport_api = viewport_utils.get_active_viewport()
    if viewport_api is None:
        print("ERROR: No active viewport found")
        return

    data = await capture_viewport_annotator_data_async(viewport_api, annotator_name=annotator)
    save_annotator_data(data, output_path)


await _capture()
