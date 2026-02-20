segmentation_mapping = {
    "floor": [255, 0, 0, 255],  # Red
    "wall": [0, 255, 0, 255],  # Green
    "rack": [0, 0, 255, 255],  # Blue
}

# Note: This overrides instance ID mode and requires semantic annotations
cosmos_writer.initialize(backend=backend, segmentation_mapping=segmentation_mapping)
