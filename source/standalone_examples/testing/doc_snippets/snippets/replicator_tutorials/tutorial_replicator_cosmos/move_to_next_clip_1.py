segmentation_mapping = {"floor": [255, 0, 0, 255], "rack": [0, 255, 0, 255]}
cosmos_writer.initialize(backend=backend, segmentation_mapping=segmentation_mapping)  # Overrides instance ID
