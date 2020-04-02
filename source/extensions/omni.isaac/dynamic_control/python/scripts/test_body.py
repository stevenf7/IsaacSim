import carb


def test_body(dc):

    body_path = "/boxActor"
    print("Registering body '%s'" % body_path)

    # body = dc.register_rigid_body(ctx, body_path, "SomeBody")
    body = dc.get_rigid_body(body_path)
    print("Got body:", body)

    f = carb.Float3(10000, 0, 0)
    p = carb.Float3(0, 0, 0)

    dc.apply_body_force(body, f, p)
