import omni.kit.test


class TestPhysics(omni.kit.test.AsyncTestCaseFailOnLogError):
    # simple fastcache smoke test
    async def test_fast_cache(self):
        from pxr import UsdGeom, Sdf, UsdPhysics
        import carb
        import numpy as np
        import omni.physx

        await omni.usd.get_context().new_stage_async()
        stage = omni.usd.get_context().get_stage()
        carb.settings.get_settings().set_int("persistent/physics/useFastCache", True)

        scene = UsdPhysics.Scene.Define(stage, Sdf.Path("/World/physicsScene"))

        cubePath = "/World/Cube"
        cubeGeom = UsdGeom.Cube.Define(stage, cubePath)
        cubeGeom.CreateSizeAttr(100)
        cubePrim = stage.GetPrimAtPath(cubePath)
        rigidBodyAPI = UsdPhysics.RigidBodyAPI.Apply(cubePrim)

        omni.timeline.get_timeline_interface().play()
        await omni.kit.app.get_app().next_update_async()
        omni.timeline.get_timeline_interface().stop()
        pass

    async def test_fast_cache_no_usd_updates(self):
        from pxr import UsdGeom, Sdf, UsdPhysics
        import carb
        import omni.physx

        await omni.usd.get_context().new_stage_async()
        stage = omni.usd.get_context().get_stage()
        carb.settings.get_settings().set_int("persistent/physics/useFastCache", True)
        carb.settings.get_settings().set_int("persistent/physics/updateToUsd", False)

        UsdPhysics.Scene.Define(stage, Sdf.Path("/World/physicsScene"))

        cubePath = "/World/Cube"
        cubeGeom = UsdGeom.Cube.Define(stage, cubePath)
        cubeGeom.CreateSizeAttr(100)
        cubePrim = stage.GetPrimAtPath(cubePath)
        UsdPhysics.RigidBodyAPI.Apply(cubePrim)

        omni.timeline.get_timeline_interface().play()
        for frame in range(60):
            await omni.kit.app.get_app().next_update_async()
        physx_interface = omni.physx.acquire_physx_interface()
        position = physx_interface.get_rigidbody_transformation("/World/Cube")["position"]
        self.assertNotAlmostEqual(position[2], 0, 0)
        usd_position = omni.usd.utils.get_world_transform_matrix(cubePrim).ExtractTranslation()
        self.assertAlmostEqual(usd_position[2], 0, 0)
        # carb.settings.get_settings().set_int("persistent/physics/updateToUsd", True)
        # await omni.kit.app.get_app().next_update_async()
        # calling this forces the pose to update
        physx_interface.update_transformations(True, True, True, False)
        await omni.kit.app.get_app().next_update_async()
        usd_position = omni.usd.utils.get_world_transform_matrix(cubePrim).ExtractTranslation()
        self.assertNotAlmostEqual(usd_position[2], 0, 0)
        omni.timeline.get_timeline_interface().pause()
        pass

    async def test_fast_cache_with_usd_updates(self):
        from pxr import UsdGeom, Sdf, UsdPhysics
        import carb
        import numpy as np
        import omni.physx

        await omni.usd.get_context().new_stage_async()
        stage = omni.usd.get_context().get_stage()
        carb.settings.get_settings().set_int("persistent/physics/useFastCache", True)
        carb.settings.get_settings().set_int("persistent/physics/updateToUsd", True)

        scene = UsdPhysics.Scene.Define(stage, Sdf.Path("/World/physicsScene"))

        cubePath = "/World/Cube"
        cubeGeom = UsdGeom.Cube.Define(stage, cubePath)
        cubeGeom.CreateSizeAttr(100)
        cubePrim = stage.GetPrimAtPath(cubePath)
        rigidBodyAPI = UsdPhysics.RigidBodyAPI.Apply(cubePrim)

        omni.timeline.get_timeline_interface().play()
        for frame in range(60):
            await omni.kit.app.get_app().next_update_async()
        # check to make sure that the cube fell due to gravity
        position = np.array(omni.usd.utils.get_world_transform_matrix(cubePrim).ExtractTranslation())
        self.assertNotAlmostEqual(position[2], 0, 0)
        omni.timeline.get_timeline_interface().stop()
        pass

    async def test_rigid_body(self):
        from pxr import UsdGeom, Sdf, UsdPhysics, Gf
        import carb
        import numpy as np
        import omni.physx

        carb.settings.get_settings().set_int("persistent/physics/useFastCache", True)
        carb.settings.get_settings().set_int("persistent/physics/updateToUsd", True)
        await omni.usd.get_context().new_stage_async()
        stage = omni.usd.get_context().get_stage()

        # force editor and physics to have the same rate (should be 60)
        physics_rate = carb.settings.get_settings().get("/physics/timeStepsPerSecond")

        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(physics_rate))
        carb.settings.get_settings().set_int("persistent/physics/maxNumSteps", int(1))
        dt = 1.0 / physics_rate

        def physics_update(dt):
            print("physics update step:", dt, "seconds")

        physics_sub = omni.physx.acquire_physx_interface().subscribe_physics_step_events(physics_update)

        # add scene
        scene = UsdPhysics.Scene.Define(stage, Sdf.Path("/World/physicsScene"))
        scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
        scene.CreateGravityMagnitudeAttr().Set(981.0)

        # Add a cube
        cubePath = "/World/Cube"
        cubeGeom = UsdGeom.Cube.Define(stage, cubePath)
        cubeGeom.CreateSizeAttr(100)
        cubePrim = stage.GetPrimAtPath(cubePath)
        rigidBodyAPI = UsdPhysics.RigidBodyAPI.Apply(cubePrim)

        # test acceleration, velocity, position
        omni.timeline.get_timeline_interface().play()
        # warm up simulation
        await omni.kit.app.get_app().next_update_async()
        # get initial position
        p_0 = np.array(omni.usd.utils.get_world_transform_matrix(cubePrim).ExtractTranslation())
        v_0 = np.array(rigidBodyAPI.GetVelocityAttr().Get())
        # simulate for one second
        time_elapsed = 0
        for frame in range(60):
            print(frame)
            await omni.kit.app.get_app().next_update_async()
            time_elapsed += dt
        p_1 = np.array(omni.usd.utils.get_world_transform_matrix(cubePrim).ExtractTranslation())
        v_1 = np.array(rigidBodyAPI.GetVelocityAttr().Get())
        print("time elapsed", time_elapsed)
        # check that acceleration matches gravity
        a = (v_1 - v_0) / time_elapsed
        self.assertAlmostEqual(a[2], -981.0, 0)

        # check that analytical position matches expected
        p_expected = p_0 + v_0 * time_elapsed + 0.5 * a * time_elapsed ** 2

        self.assertAlmostEqual(p_1[2], p_expected[2], 0)
        omni.timeline.get_timeline_interface().stop()
        pass
