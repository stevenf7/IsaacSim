import math

import omni
from omni.syntheticdata import helpers

stage = omni.usd.get_context().get_stage()
viewport_api = omni.kit.viewport.utility.get_active_viewport()
# Set viewport resolution, changes will occur on next frame
viewport_api.set_texture_resolution((512, 512))
# get resolution
width, height = viewport_api.get_texture_resolution()
aspect_ratio = width / height
# get camera prim attached to viewport
camera = stage.GetPrimAtPath(viewport_api.get_active_camera())
focal_length = camera.GetAttribute("focalLength").Get()
horiz_aperture = camera.GetAttribute("horizontalAperture").Get()
vert_aperture = camera.GetAttribute("verticalAperture").Get()
# Pixels are square so we can also do:
# vert_aperture = height / width * horiz_aperture
near, far = camera.GetAttribute("clippingRange").Get()
fov = 2 * math.atan(horiz_aperture / (2 * focal_length))
# helper to compute projection matrix
proj_mat = helpers.get_projection_matrix(fov, aspect_ratio, near, far)

# compute focal point and center
focal_x = height * focal_length / vert_aperture
focal_y = width * focal_length / horiz_aperture
center_x = height * 0.5
center_y = width * 0.5
