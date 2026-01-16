def get_random_transform_values(
    loc_min=(0, 0, 0), loc_max=(1, 1, 1), rot_min=(0, 0, 0), rot_max=(360, 360, 360), scale_min_max=(0.1, 1.0)
):
    """Create random transformation values for location, rotation, and scale."""
    location = (
        random.uniform(loc_min[0], loc_max[0]),
        random.uniform(loc_min[1], loc_max[1]),
        random.uniform(loc_min[2], loc_max[2]),
    )
    rotation = (
        random.uniform(rot_min[0], rot_max[0]),
        random.uniform(rot_min[1], rot_max[1]),
        random.uniform(rot_min[2], rot_max[2]),
    )
    scale = tuple([random.uniform(scale_min_max[0], scale_min_max[1])] * 3)
    return location, rotation, scale


def get_random_pose_on_sphere(origin, radius, camera_forward_axis=(0, 0, -1)):
    """Generate a random pose on a sphere looking at the origin."""
    origin = Gf.Vec3f(origin)
    camera_forward_axis = Gf.Vec3f(camera_forward_axis)

    # Generate random angles for spherical coordinates
    theta = np.random.uniform(0, 2 * np.pi)
    phi = np.arcsin(np.random.uniform(-1, 1))

    # Spherical to Cartesian conversion
    x = radius * np.cos(theta) * np.cos(phi)
    y = radius * np.sin(phi)
    z = radius * np.sin(theta) * np.cos(phi)

    location = origin + Gf.Vec3f(x, y, z)

    # Calculate direction vector from camera to look_at point
    direction = origin - location
    direction_normalized = direction.GetNormalized()

    # Calculate rotation from forward direction (rotateFrom) to direction vector (rotateTo)
    rotation = Gf.Rotation(Gf.Vec3d(camera_forward_axis), Gf.Vec3d(direction_normalized))
    orientation = Gf.Quatf(rotation.GetQuat())

    return location, orientation
