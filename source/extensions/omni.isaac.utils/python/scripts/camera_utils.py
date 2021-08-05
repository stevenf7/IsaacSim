import numpy as np
import omni
from omni.isaac.utils.scripts import lookat_to_quat
from pxr import Gf, UsdGeom, Usd


def get_intrinsics_matrix(viewport):
    """
    Returns the intrisics matrix associated with the specified viewport

    The following image convention is assumed:

    +x should point to the right in the image
    +y should point down in the image
    """
    import omni

    stage = omni.usd.get_context().get_stage()
    prim = stage.GetPrimAtPath(viewport.get_active_camera())
    focal_length = prim.GetAttribute("focalLength").Get()
    horiz_aperture = prim.GetAttribute("horizontalAperture").Get()
    width, height = viewport.get_texture_resolution()
    vert_aperture = height / width * horiz_aperture
    fx = width * focal_length / horiz_aperture
    fy = height * focal_length / vert_aperture
    cx = width * 0.5
    cy = height * 0.5
    return np.array([[fx, 0.0, cx], [0.0, fy, cy], [0.0, 0.0, 1.0]])


def backproject_depth(np_depth_image, viewport, max_clip_depth):
    """
    Backproject depth image to image space
    """
    intrinsics_matrix = get_intrinsics_matrix(viewport)
    fx = intrinsics_matrix[0][0]
    fy = intrinsics_matrix[1][1]
    cx = intrinsics_matrix[0][2]
    cy = intrinsics_matrix[1][2]
    height = np_depth_image.shape[0]
    width = np_depth_image.shape[1]
    input_x = np.arange(width)
    input_y = np.arange(height)
    input_x, input_y = np.meshgrid(input_x, input_y)
    input_x = input_x.flatten()
    input_y = input_y.flatten()
    input_z = np_depth_image.flatten()
    input_z[input_z > max_clip_depth] = 0
    output_x = (input_x * input_z - cx * input_z) / fx
    output_y = (input_y * input_z - cy * input_z) / fy
    raw_pc = np.stack([output_x, output_y, input_z], -1).reshape([height * width, 3])
    return raw_pc


def project_depth_to_worldspace(depth_image: np.array, viewport, max_clip_depth):
    """
    Project depth image to world space
    """
    from pxr import UsdGeom, Usd, Gf
    import omni
    import carb

    stage = omni.usd.get_context().get_stage()
    prim = stage.GetPrimAtPath(viewport.get_active_camera())
    prim_tf = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode())
    units_per_meter = 1.0 / UsdGeom.GetStageMetersPerUnit(stage)

    depth_data = depth_image * units_per_meter
    depth_data = -np.clip(depth_data, 0, max_clip_depth)

    pc = backproject_depth(depth_data, viewport, max_clip_depth)
    points = []
    for pts in pc:
        p = prim_tf.Transform(Gf.Vec3d(-pts[0], pts[1], pts[2]))
        points.append(carb.Float3(p[0], p[1], p[2]))

    return points


class SpringDamperFollower:
    def __init__(
        self, mass, stiffness, damping, current=Gf.Vec3d(0, 0, 0), target=Gf.Vec3d(0, 0, 0), vel=Gf.Vec3d(0, 0, 0)
    ):
        self.m = mass
        self.k = stiffness
        self.c = damping
        self.current = current
        self.target = target
        self.v = vel

    def update(self, step):
        d = self.target - self.current
        a = (self.k * d - self.c * self.v) / self.m
        self.v = self.v + a * step
        self.current = self.current + self.v * step


class DynamicCamera:
    def __init__(self, stage, base_path, camera_name, focal_length=24, f_stop=5, focus_distance=0):
        self._stage = stage
        self._viewport_window = omni.kit.viewport.get_default_viewport_window()
        self.target_follower = SpringDamperFollower(mass=5, stiffness=5, damping=10)
        self.position_follower = SpringDamperFollower(mass=20, stiffness=5, damping=20)
        self.focus_follower = SpringDamperFollower(mass=1, stiffness=10, damping=10, current=10000, target=10000, vel=0)
        self._base_path = base_path
        self._camera_path = base_path + "/" + camera_name
        self.thresh = 0.1

        self.proxy = self._stage.DefinePrim(self._base_path + "/" + camera_name + "_proxy", "Xform")
        xform = UsdGeom.Xformable(self.proxy)
        xform.ClearXformOpOrder()
        xform_op = xform.AddXformOp(UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, "")
        self._timeline = omni.timeline.get_timeline_interface()

        self.prim = self._stage.DefinePrim(base_path + "/" + camera_name + "_proxy/" + camera_name, "Camera")
        self.prim.GetAttribute("focalLength").Set(focal_length)
        self.prim.GetAttribute("fStop").Set(float(f_stop))
        self.prim.GetAttribute("focusDistance").Set(float(focus_distance))
        self.focus = False

    def reset(self):
        self.position_follower.current = self.position_follower.target
        self.target_follower.current = self.target_follower.target
        self.update(1.0 / 60.0)

    def update(self, step, timecode=Usd.TimeCode.Default()):
        self.target_follower.update(step)
        self.position_follower.update(step)

        pos = self.position_follower.current
        target = self.target_follower.current

        orient = lookat_to_quat(target, pos, Gf.Vec3d(0, 0, 1))
        mat = Gf.Matrix4d().SetRotateOnly(orient).SetTranslateOnly(pos)
        # mat_1 = Gf.Matrix4d().SetLookAt(self.position_follower.current, self.target_follower.current, Gf.Vec3d(0, 0, 1))
        # trans = mat_1.ExtractTranslation()
        # mat_1.SetTranslateOnly(Gf.Vec3d(trans[2], trans[0], -trans[1]))
        self.proxy.GetAttribute("xformOp:transform").Set(mat, timecode)

        if self.focus:
            self.focus_follower.target = float((target - pos).GetLength())
        else:
            self.focus_follower.target = 10000
        self.focus_follower.update(step)
        # print("focal", self.focus_follower.current)
        self.prim.GetAttribute("focusDistance").Set(float(self.focus_follower.current), timecode)

    def set_look_target(self, pos):
        self.target_follower.target = pos

    def set_pos_target(self, pos):
        self.position_follower.target = pos

    def set_autofocus_target(self, focus):
        self.focus = focus

    def set_pos_settings(self, mass, stiffness, damping):
        self.position_follower.m = mass
        self.position_follower.k = stiffness
        self.position_follower.c = damping

    def set_target_settings(self, mass, stiffness, damping):
        self.target_follower.m = mass
        self.target_follower.k = stiffness
        self.target_follower.c = damping
