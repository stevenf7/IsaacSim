def _create_bin_and_pallet_graph(self):
    # Bin material randomization
    bin_paths = [f"{self.BINS_FOLDER_PATH}/bin_{i}/Visuals/FOF_Mesh_Magenta_Box" for i in range(self._bin_counter + 1)]
    bins_node = rep.get.prim_at_path(bin_paths)

    with rep.trigger.on_frame():
        mats = rep.create.material_omnipbr(
            diffuse=rep.distribution.uniform((0.2, 0.1, 0.3), (0.6, 0.6, 0.7)),
            roughness=rep.distribution.choice([0.1, 0.9]),
            count=10,
        )
        with bins_node:
            rep.randomizer.materials(mats)

    # Camera and pallet texture randomization at a slower rate
    assets_root_path = get_assets_root_path()
    texture_paths = [
        assets_root_path + "/NVIDIA/Materials/Base/Wood/Oak/Oak_BaseColor.png",
        assets_root_path + "/NVIDIA/Materials/Base/Wood/Ash/Ash_BaseColor.png",
        assets_root_path + "/NVIDIA/Materials/Base/Wood/Plywood/Plywood_BaseColor.png",
        assets_root_path + "/NVIDIA/Materials/Base/Wood/Timber/Timber_BaseColor.png",
    ]
    pallet_node = rep.get.prim_at_path(self.PALLET_PRIM_MESH_PATH)
    pallet_prim = pallet_node.get_output_prims()["prims"][0]
    pallet_loc = omni.usd.get_world_transform_matrix(pallet_prim).ExtractTranslation()
    self._rep_camera = rep.create.camera()
    with rep.trigger.on_frame(interval=4):
        with pallet_node:
            rep.randomizer.texture(texture_paths, texture_rotate=rep.distribution.uniform(80, 95))
        with self._rep_camera:
            rep.modify.pose(
                position=rep.distribution.uniform((0, -2, 1), (2, 1, 2)),
                look_at=(pallet_loc[0], pallet_loc[1], pallet_loc[2]),
            )
