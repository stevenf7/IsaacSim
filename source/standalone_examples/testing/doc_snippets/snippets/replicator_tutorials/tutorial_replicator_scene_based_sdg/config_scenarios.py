config = {
    "launch_config": {
        "renderer": "RealTimePathTracing",
        "headless": False,
    },
    "resolution": [512, 512],
    "rt_subframes": 32,
    "num_frames": 10,
    "env_url": "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd",
    "writer": "BasicWriter",
    "backend_type": "DiskBackend",
    "backend_params": {
        "output_dir": "_out_scene_based_sdg",
    },
    "writer_config": {
        "rgb": True,
        "bounding_box_2d_tight": True,
        "semantic_segmentation": True,
        "distance_to_image_plane": True,
        "bounding_box_3d": True,
        "occlusion": True,
    },
    "clear_previous_semantics": True,
    "forklift": {
        "url": "/Isaac/Props/Forklift/forklift.usd",
        "class": "forklift",
    },
    "cone": {
        "url": "/Isaac/Environments/Simple_Warehouse/Props/S_TrafficCone.usd",
        "class": "traffic_cone",
    },
    "pallet": {
        "url": "/Isaac/Environments/Simple_Warehouse/Props/SM_PaletteA_01.usd",
        "class": "pallet",
    },
    "cardbox": {
        "url": "/Isaac/Environments/Simple_Warehouse/Props/SM_CardBoxD_04.usd",
        "class": "cardbox",
    },
    "close_app_after_run": False,
}
