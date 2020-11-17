# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.kit.asyncapi
import omni.kit.usd
import omni.kit.commands
from omni.isaac.dynamic_control import _dynamic_control as dc
import carb.tokens
import os
import carb
import asyncio
import numpy as np
from omni.isaac.utils._isaac_utils import math as mu
from pxr import Usd, UsdLux, UsdGeom, Sdf, Gf, Tf, PhysicsSchema


# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.utils._isaac_utils.surface_grippers import Surface_Gripper_Properties, Surface_Gripper

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestSurfaceGripper(omni.kit.test.AsyncTestCaseFailOnLogError):
    def createRigidCube(self, boxActorPath, mass, scale, position, rotation, color):
        p = Gf.Vec3f(position[0], position[1], position[2])
        orientation = Gf.Quatf(rotation[3], rotation[0], rotation[1], rotation[2])
        color = Gf.Vec3f(color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)
        size = 100.0
        scale = Gf.Vec3f(scale[0], scale[1], scale[2])

        cubeGeom = UsdGeom.Cube.Define(self.stage, boxActorPath)
        cubePrim = self.stage.GetPrimAtPath(boxActorPath)
        cubeGeom.CreateSizeAttr(size)
        cubeGeom.AddTranslateOp().Set(p)
        cubeGeom.AddOrientOp().Set(orientation)
        cubeGeom.AddScaleOp().Set(scale)
        cubeGeom.CreateDisplayColorAttr().Set([color])

        PhysicsSchema.CollisionAPI.Apply(cubePrim)
        if mass > 0:
            massAPI = PhysicsSchema.MassAPI.Apply(cubePrim)
            massAPI.CreateMassAttr(mass)
        physicsAPI = PhysicsSchema.PhysicsAPI.Apply(cubePrim)
        physicsAPI.CreateBodyTypeAttr("rigid")
        print(cubePrim.GetPath().pathString)

    # Helper for setting up the physics stage
    def setup_physics(self, box1_props):
        # Set Up Physics scene

        UsdGeom.SetStageUpAxis(self.stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(self.stage, 0.01)
        scene = PhysicsSchema.PhysicsScene.Define(self.stage, Sdf.Path("/physicsScene"))
        scene.CreateGravityAttr().Set(Gf.Vec3f(0.0, 0.0, -1000.0))

        omni.kit.commands.execute(
            "AddGroundPlaneCommand",
            stage=self.stage,
            planePath="/groundPlane",
            axis="Z",
            size=100.0,
            position=Gf.Vec3f(0),
            color=Gf.Vec3f(0.5),
        )
        self.assertFalse(self._dc.is_simulating())

        # Create two cubes and set them to be rigid bodies

        # box0
        self.createRigidCube(*self.box0_props)
        # Box1
        self.createRigidCube(*box1_props)

        # d6FixedJoint = PhysicsSchema.PhysicsJoint.Define(self.stage, "/box0/d6FixedJoint")
        # d6FixedJoint.CreateBody0Rel().SetTargets(["/box0"])

    # Before running each test
    async def setUp(self):
        self._dc = dc.acquire_dynamic_control_interface()
        self.box0 = "/box0"
        self.box1 = "/box1"
        self.box0_props = [self.box0, 300, [1, 1, 2.0], [-50, 0, 100], [0, 0, 0, 1], [80, 80, 255]]
        self.box1_props = [self.box1, 1.0, [0.1, 0.1, 0.1], [6, 0, 204], [0, 0, 0, 1], [255, 80, 80]]
        self.d6FixedJoint = "/box0/d6FixedJoint"

        self.sgp = Surface_Gripper_Properties()
        self.sgp.d6JointPath = self.d6FixedJoint
        self.sgp.parentPath = self.box0
        self.sgp.offset = dc.Transform()
        self.sgp.offset.p.x = 50.1
        self.sgp.offset.p.z = 100
        self.sgp.gripThreshold = 2
        self.sgp.forceLimit = 1.0e3
        self.sgp.torqueLimit = 1.0e5
        self.sgp.bendAngle = np.pi / 4
        self.sgp.stiffness = 1.0e4
        self.sgp.damping = 1.0e3

        self.surface_gripper = None

        await omni.kit.asyncapi.new_stage()
        self.stage = omni.usd.get_context().get_stage()
        self._timeline = omni.timeline.get_timeline_interface()

        pass

    # After running each test
    async def tearDown(self):
        print("tearing down")
        # Because lifetime for this joint object is managed by the DC plugin and not usd the order
        # that dc and the gripper are cleaned up matters. First remove the surface gripper and
        # then call stop and then cleanup dc
        self.surface_gripper = None
        await omni.kit.asyncapi.next_update()
        self._timeline.stop()
        await omni.kit.asyncapi.next_update()
        pass

    # Actual test, notice it is "async" function, so "await" can be used if needed
    async def test_create_surface_gripper(self):

        self.surface_gripper = Surface_Gripper(self._dc)
        assert self.surface_gripper is not None

        pass

    async def test_initialize_surface_gripper(self):

        self.setup_physics(self.box1_props)
        self.surface_gripper = Surface_Gripper(self._dc)
        # Start Simulation and wait
        self._timeline.play()
        await asyncio.sleep(0.125)
        await omni.kit.asyncapi.next_update()
        self.assertTrue(self._dc.is_simulating())

        print(self._dc.get_rigid_body(self.box0))
        print(self._dc.get_rigid_body(self.box1))
        self.assertTrue(self.surface_gripper.initialize(self.sgp))
        pass

    async def test_close_surface_gripper(self):

        self.setup_physics(self.box1_props)
        self.surface_gripper = Surface_Gripper(self._dc)
        # Start Simulation and wait
        self._timeline.play()

        await asyncio.sleep(0.125)
        await omni.kit.asyncapi.next_update()

        self.sgp.forceLimit = 1.0e10
        self.sgp.torqueLimit = 1.0e10
        self.sgp.stiffness = 1.0e10

        self.surface_gripper.initialize(self.sgp)
        box0 = self._dc.get_rigid_body(self.box0)
        box1 = self._dc.get_rigid_body(self.box1)
        t = dc.Transform()
        t.p = self.box1_props[3]
        t.r = self.box1_props[4]
        self._dc.set_rigid_body_pose(box1, t)
        self._dc.set_rigid_body_linear_velocity(box1, [0.0, 0.0, 0.0])
        self._dc.set_rigid_body_angular_velocity(box1, [0.0, 0.0, 0.0])
        self.assertTrue(self.surface_gripper.close())
        # use 100 instead of 30, to make sure the joint doesn't break
        for i in range(100):
            await omni.kit.asyncapi.next_update()
            self.surface_gripper.update()
            self._dc.wake_up_rigid_body(box1)
        self.assertTrue(self.surface_gripper.is_closed())
        await asyncio.sleep(1.0)
        await omni.kit.asyncapi.next_update()
        tr = self._dc.get_rigid_body_pose(box1)
        self.assertGreater(tr.p.z, 200)

        # Check to make sure that pause and then play does not break joint
        self._timeline.pause()
        await asyncio.sleep(0.125)
        await omni.kit.asyncapi.next_update()
        self._timeline.play()
        await asyncio.sleep(0.5)
        await omni.kit.asyncapi.next_update()
        self.surface_gripper.update()
        tr = self._dc.get_rigid_body_pose(box1)
        self.assertGreater(tr.p.z, 200)
        self.assertTrue(self.surface_gripper.is_closed())
        pass

    async def test_close_stop_close(self):
        await self.test_close_surface_gripper()
        self._timeline.stop()
        await asyncio.sleep(0.5)
        await omni.kit.asyncapi.next_update()

        self._timeline.play()
        await omni.kit.asyncapi.next_update()
        box0 = self._dc.get_rigid_body(self.box0)
        box1 = self._dc.get_rigid_body(self.box1)
        t = dc.Transform()
        t.p = self.box1_props[3]
        t.r = self.box1_props[4]
        self._dc.set_rigid_body_pose(box1, t)
        self._dc.set_rigid_body_linear_velocity(box1, [0.0, 0.0, 0.0])
        self._dc.set_rigid_body_angular_velocity(box1, [0.0, 0.0, 0.0])
        self.assertTrue(self.surface_gripper.close())
        # use 100 instead of 30, to make sure the joint doesn't break
        for i in range(100):
            await omni.kit.asyncapi.next_update()
            self.surface_gripper.update()
            self._dc.wake_up_rigid_body(box1)
        self.assertTrue(self.surface_gripper.is_closed())
        await asyncio.sleep(1.0)
        await omni.kit.asyncapi.next_update()
        tr = self._dc.get_rigid_body_pose(box1)
        self.assertGreater(tr.p.z, 200)

        # Check to make sure that pause and then play does not break joint
        self._timeline.pause()
        await asyncio.sleep(0.125)
        await omni.kit.asyncapi.next_update()
        self._timeline.play()
        await asyncio.sleep(0.5)
        await omni.kit.asyncapi.next_update()
        self.surface_gripper.update()
        tr = self._dc.get_rigid_body_pose(box1)
        self.assertGreater(tr.p.z, 200)
        self.assertTrue(self.surface_gripper.is_closed())
        pass

    async def test_close_surface_gripper_and_move(self):

        self.box0_props[2] = [0.1, 0.1, 0.1]
        self.box0_props[3] = [-5, 0, 5]
        box1_props = [self.box1, 10.0, [0.1, 0.1, 0.1], [6, 0, 5], [0, 0, 0, 1], [255, 80, 80]]

        self.setup_physics(box1_props)
        self.surface_gripper = Surface_Gripper(self._dc)
        # Start Simulation and wait
        self._timeline.play()

        await asyncio.sleep(0.125)
        await omni.kit.asyncapi.next_update()
        self.sgp.offset.p.x = 5.1
        self.sgp.offset.p.z = 0
        self.sgp.gripThreshold = 2
        self.sgp.forceLimit = 1.0e10
        self.sgp.torqueLimit = 1.0e10
        self.sgp.bendAngle = 0
        self.sgp.stiffness = 1.0e10
        self.sgp.damping = 1.0e10

        self.surface_gripper.initialize(self.sgp)
        box0 = self._dc.get_rigid_body(self.box0)
        box1 = self._dc.get_rigid_body(self.box1)
        t = dc.Transform()
        t.p = box1_props[3]
        t.r = box1_props[4]
        self._dc.set_rigid_body_pose(box1, t)
        self._dc.set_rigid_body_linear_velocity(box1, [0.0, 0.0, 0.0])
        self._dc.set_rigid_body_angular_velocity(box1, [0.0, 0.0, 0.0])
        self.assertTrue(self.surface_gripper.close())
        for i in range(600):
            await omni.kit.asyncapi.next_update()
            self._dc.set_rigid_body_linear_velocity(box0, [0, 0.0, 50])
            self._dc.set_rigid_body_angular_velocity(box0, [-20.0, 0.0, 10])
            self.surface_gripper.update()
            self._dc.wake_up_rigid_body(box1)
        self.assertTrue(self.surface_gripper.is_closed())

        v0 = self._dc.get_rigid_body_linear_velocity(box0)
        v1 = self._dc.get_rigid_body_linear_velocity(box1)

        # Check if both objects are moving
        self.assertGreater(np.linalg.norm([v0.x, v0.y, v0.z]), 0.01)
        self.assertGreater(np.linalg.norm([v1.x, v1.y, v1.z]), 0.01)

        pass

    async def test_close_offset_surface_gripper(self):

        self.box0_props[4] = (0, 0, 0.70701, -0.70701)
        self.box1_props = [self.box1, 1.0, [0.1, 0.1, 0.1], [6, 0, 204], [0, 0, 0, 1], [255, 80, 80]]
        self.sgp.offset.p = (0, 50.1, 100)
        self.sgp.offset.r = (0, 0, 0.7071, 0.7071)
        self.sgp.forceLimit = 1.0e10
        self.sgp.torqueLimit = 1.0e10
        self.sgp.stiffness = 1.0e10

        await self.test_close_surface_gripper()
        pass

    async def test_close_out_of_reach_surface_gripper(self):

        box1_props = [self.box1, 1.0, [0.1, 0.1, 0.1], [8, 0, 204], [0, 0, 0, 1], [255, 80, 80]]

        self.setup_physics(box1_props)
        self.surface_gripper = Surface_Gripper(self._dc)
        # Start Simulation and wait
        self._timeline.play()

        await asyncio.sleep(0.125)
        await omni.kit.asyncapi.next_update()
        self.surface_gripper.initialize(self.sgp)
        box0 = self._dc.get_rigid_body(self.box0)
        box1 = self._dc.get_rigid_body(self.box1)
        t = dc.Transform()
        t.p = box1_props[3]
        t.r = box1_props[4]
        self._dc.set_rigid_body_pose(box1, t)
        self._dc.set_rigid_body_linear_velocity(box1, [0.0, 0.0, 0.0])
        self._dc.set_rigid_body_angular_velocity(box1, [0.0, 0.0, 0.0])
        self.assertFalse(self.surface_gripper.close())
        for i in range(100):
            await omni.kit.asyncapi.next_update()
            self.surface_gripper.update()
            self._dc.wake_up_rigid_body(box1)
        self.assertFalse(self.surface_gripper.is_closed())

        tr = self._dc.get_rigid_body_pose(box1)
        self.assertLess(tr.p.z, 200)

        pass

    async def test_open_surface_gripper(self):

        await self.test_close_surface_gripper()

        box1 = self._dc.get_rigid_body(self.box1)
        self.surface_gripper.open()
        await omni.kit.asyncapi.next_update()
        self._dc.wake_up_rigid_body(box1)
        self.surface_gripper.update()
        await asyncio.sleep(0.125)
        await omni.kit.asyncapi.next_update()
        self.assertFalse(self.surface_gripper.is_closed())
        lin_vel = self._dc.get_rigid_body_linear_velocity(box1)
        self.assertGreater(np.linalg.norm([lin_vel.x, lin_vel.y, lin_vel.z]), 0)
        tr = self._dc.get_rigid_body_pose(box1)
        self.assertLess(tr.p.z, 200)

        # Check to make sure that pause and then play does not close joint
        self._timeline.pause()
        await asyncio.sleep(0.125)
        await omni.kit.asyncapi.next_update()
        self._timeline.play()
        await asyncio.sleep(0.5)
        await omni.kit.asyncapi.next_update()
        tr = self._dc.get_rigid_body_pose(box1)
        self.assertLess(tr.p.z, 200)
        self.assertFalse(self.surface_gripper.is_closed())
        pass

    async def test_break_surface_gripper(self):

        box1_props = [self.box1, 10.0, [0.1, 0.1, 0.02], [6, 0, 200.5], [0, 0, 0, 1], [255, 80, 80]]

        self.setup_physics(box1_props)
        self.surface_gripper = Surface_Gripper(self._dc)
        # Start Simulation and wait
        self._timeline.play()
        await asyncio.sleep(0.125)
        await omni.kit.asyncapi.next_update()
        self.assertTrue(self._dc.is_simulating())
        self.surface_gripper.initialize(self.sgp)
        box0 = self._dc.get_rigid_body(self.box0)
        box1 = self._dc.get_rigid_body(self.box1)
        t = dc.Transform()
        t.p = [6, 0, 200.5]
        t.r = box1_props[4]
        self._dc.set_rigid_body_pose(box1, t)
        self._dc.set_rigid_body_linear_velocity(box1, [0.0, 0.0, 0.0])
        self._dc.set_rigid_body_angular_velocity(box1, [0.0, 0.0, 0.0])
        self.assertTrue(self.surface_gripper.close())
        await omni.kit.asyncapi.next_update()

        # self._dc.set_rigid_body_linear_velocity(box1, [0.0, 0.0, 100.0])
        i = 0
        while i < 600:
            i = i + 1
            await omni.kit.asyncapi.next_update()
            self.surface_gripper.update()
            self._dc.wake_up_rigid_body(box1)
            if not self.surface_gripper.is_closed():
                i = 600
        self.assertFalse(self.surface_gripper.is_closed())

        lin_vel = self._dc.get_rigid_body_linear_velocity(box1)
        print(lin_vel)
        self.assertGreater(np.linalg.norm([lin_vel.x, lin_vel.y, lin_vel.z]), 0)
        # Do not stop editor, check if joint cleans up correctly
        pass

    async def test_bend_surface_gripper(self):

        box1_props = [self.box1, 10.0, [0.1, 0.1, 0.1], [6, 0, 204], [0, 0, 0, 1], [255, 80, 80]]

        self.setup_physics(box1_props)
        self.surface_gripper = Surface_Gripper(self._dc)
        # Start Simulation and wait
        self._timeline.play()
        await asyncio.sleep(0.125)
        await omni.kit.asyncapi.next_update()
        self.assertTrue(self._dc.is_simulating())
        self.sgp.forceLimit = 1.0e30
        self.sgp.torqueLimit = 1.0e50
        self.sgp.stiffness = 1.0e5
        self.sgp.damping = 1.0e1
        self.surface_gripper.initialize(self.sgp)
        box1 = self._dc.get_rigid_body(self.box1)
        t = dc.Transform()
        t.p = [6, 0, 204]
        t.r = box1_props[4]
        self._dc.set_rigid_body_pose(box1, t)

        self._dc.set_rigid_body_angular_velocity(box1, [0.0, 0.0, 0.0])
        self.assertTrue(self.surface_gripper.close())
        await omni.kit.asyncapi.next_update()

        i = 0
        rx1 = (1, 0, 0)
        rx2 = (1, 0, 0)
        while i < 300:
            i += 1
            await omni.kit.asyncapi.next_update()
            tr = self._dc.get_rigid_body_pose(box1)
            rx1 = mu.get_basis_vector_x(tr.r)
            rx2 = mu.get_basis_vector_x(t.r)
            self.surface_gripper.update()
            self._dc.wake_up_rigid_body(box1)

        self.assertLess(abs(mu.dot(rx2, rx1)), 0.9)
        self._dc.set_rigid_body_linear_velocity(box1, [0.0, 0.0, 0.0])
        while i < 400:
            i += 1
            await omni.kit.asyncapi.next_update()
            self.surface_gripper.update()
            self._dc.wake_up_rigid_body(box1)

        self.assertTrue(self.surface_gripper.is_closed())
        self.assertGreater(tr.p.z, 190)
        pass

    async def test_fixed_surface_gripper(self):

        box1_props = [self.box1, 10.0, [0.1, 0.1, 0.1], [6, 0, 204], [0, 0, 0, 1], [255, 80, 80]]

        self.setup_physics(box1_props)
        self.surface_gripper = Surface_Gripper(self._dc)
        # Start Simulation and wait
        self._timeline.play()
        await asyncio.sleep(0.125)
        await omni.kit.asyncapi.next_update()
        self.assertTrue(self._dc.is_simulating())
        self.sgp.forceLimit = 1.0e30
        self.sgp.torqueLimit = 1.0e50
        self.sgp.stiffness = 1.0
        self.sgp.damping = 1.0
        self.sgp.bendAngle = 0
        self.surface_gripper.initialize(self.sgp)
        box1 = self._dc.get_rigid_body(self.box1)
        t = dc.Transform()
        t.p = [6, 0, 204]
        t.r = box1_props[4]
        self._dc.set_rigid_body_pose(box1, t)

        self._dc.set_rigid_body_angular_velocity(box1, [0.0, 0.0, 0.0])
        self.assertTrue(self.surface_gripper.close())
        await omni.kit.asyncapi.next_update()

        i = 0
        rx1 = (1, 0, 0)
        rx2 = (1, 0, 0)
        while i < 300:
            i += 1
            await omni.kit.asyncapi.next_update()
            tr = self._dc.get_rigid_body_pose(box1)
            rx1 = mu.get_basis_vector_x(tr.r)
            rx2 = mu.get_basis_vector_x(t.r)
            self.surface_gripper.update()
            self._dc.wake_up_rigid_body(box1)

        self.assertGreater(abs(mu.dot(rx2, rx1)), 0.99)
        self.assertTrue(self.surface_gripper.is_closed())
        self.assertGreater(tr.p.z, 200)
        pass
