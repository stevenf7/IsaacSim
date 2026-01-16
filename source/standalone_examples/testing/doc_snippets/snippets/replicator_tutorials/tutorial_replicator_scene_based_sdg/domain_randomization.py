# Initialize randomization with seed for reproducibility
rep.set_global_seed(42)
rng = np.random.default_rng(42)

# Spawn forklift at random pose
forklift_prim = prims.create_prim(
    prim_path="/SDG/Forklift",
    position=(rng.uniform(-20, -2), rng.uniform(-1, 3), 0),
    orientation=euler_angles_to_quat([0, 0, rng.uniform(0, math.pi)]),
    usd_path=assets_root_path + config["forklift"]["url"],
    semantic_label=config["forklift"]["class"],
)

# Spawn pallet in front of forklift with random offset
forklift_tf = omni.usd.get_world_transform_matrix(forklift_prim)
pallet_offset_tf = Gf.Matrix4d().SetTranslate(Gf.Vec3d(0, rng.uniform(-1.8, -1.2), 0))
pallet_pos = (pallet_offset_tf * forklift_tf).ExtractTranslation()
forklift_quat = forklift_tf.ExtractRotationQuat()
forklift_quat_xyzw = (forklift_quat.GetReal(), *forklift_quat.GetImaginary())

pallet_prim = prims.create_prim(
    prim_path="/SDG/Pallet",
    position=pallet_pos,
    orientation=forklift_quat_xyzw,
    usd_path=assets_root_path + config["pallet"]["url"],
    semantic_label=config["pallet"]["class"],
)

# Create cardboxes for pallet scattering
cardboxes = []
for i in range(5):
    cardbox = prims.create_prim(
        prim_path=f"/SDG/CardBox_{i}",
        usd_path=assets_root_path + config["cardbox"]["url"],
        semantic_label=config["cardbox"]["class"],
    )
    cardboxes.append(cardbox)

# Create traffic cone for corner placement
cone = prims.create_prim(
    prim_path="/SDG/Cone",
    usd_path=assets_root_path + config["cone"]["url"],
    semantic_label=config["cone"]["class"],
)
