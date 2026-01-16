# Create lights to randomize in the working area using USD API
scene_lights = []
num_scene_lights = capture_config.get("num_scene_lights", 0)
for i in range(num_scene_lights):
    light_prim = stage.DefinePrim(f"/Lights/SphereLight_scene_{i}", "SphereLight")
    scene_lights.append(light_prim)

# Register replicator graph randomizers
infinigen_utils.register_dome_light_randomizer()
infinigen_utils.register_shape_distractors_color_randomizer(shape_distractors)
