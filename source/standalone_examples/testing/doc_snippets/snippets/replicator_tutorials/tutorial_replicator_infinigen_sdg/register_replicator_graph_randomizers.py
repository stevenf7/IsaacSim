# Randomize scene lights properties and locations around the working area
lights_loc_range = infinigen_utils.offset_range((-2, -2, 1, 2, 2, 3), working_area_loc)
infinigen_utils.randomize_lights(
    scene_lights,
    location_range=lights_loc_range,
    intensity_range=(500, 2500),
    color_range=(0.1, 0.1, 0.1, 0.9, 0.9, 0.9),
    rng=rng,
)

# Trigger dome light randomization using OmniGraph events
rep.utils.send_og_event(event_name="randomize_dome_lights")

# Trigger shape distractor color randomization
rep.utils.send_og_event(event_name="randomize_shape_distractor_colors")
