# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core.objects.sphere import VisualSphere
from omni.isaac.core.utils.prims import is_prim_path_valid, delete_prim
from omni.isaac.core.utils.string import find_unique_string_name

from collections import OrderedDict
import yaml
import numpy as np
import carb


class CollisionSphereEditor:
    def __init__(self):
        self.path_2_spheres = {}
        self.path_2_sphere_serial_copy = {}

        self._operations = []

        self._redo = []

        self.sphere_color = np.array([207.0, 184.0, 37.0]) / 255

    def clear_spheres(self, store_op=True):
        sphere_paths = list(self.path_2_spheres.keys())
        if len(sphere_paths) == 0:
            return

        if store_op:
            self.copy_all_sphere_data()
            deleted_spheres = ["DEL"]
            for sphere_path in sphere_paths:
                deleted_spheres.append(self.path_2_sphere_serial_copy[sphere_path])
            self._operations.append(deleted_spheres)

        for sphere_path in sphere_paths:
            self.delete_sphere(sphere_path)

    def delete_sphere(self, sphere_path):
        if is_prim_path_valid(sphere_path):
            delete_prim(sphere_path)

        if sphere_path in self.path_2_spheres:
            del self.path_2_spheres[sphere_path]

    def set_sphere_colors(self, color):
        self.sphere_color = color
        for sphere_path in self.path_2_spheres.keys():
            if is_prim_path_valid(sphere_path):
                sphere = self.path_2_spheres[sphere_path]
                sphere.get_applied_visual_material().set_color(color)

    def copy_all_sphere_data(self):
        sphere_paths = list(self.path_2_spheres.keys())
        deleted_spheres = ["DEL"]
        for sphere_path in sphere_paths:
            if is_prim_path_valid(sphere_path):
                sphere = self.path_2_spheres[sphere_path]
                color = sphere.get_applied_visual_material().get_color()
                self.path_2_sphere_serial_copy[sphere_path] = {
                    "sphere_path": sphere_path,
                    "center": sphere.get_local_pose()[0],
                    "radius": sphere.get_radius(),
                    "color": color,
                }
            else:
                if sphere_path in self.path_2_sphere_serial_copy:
                    deleted_spheres.append(self.path_2_sphere_serial_copy[sphere_path])
                self.delete_sphere(sphere_path)
        if len(deleted_spheres) > 1:
            self._operations.append(deleted_spheres)

    def undo(self):
        if len(self._operations) == 0:
            return

        last_op = self._operations.pop()
        op_type = last_op[0]
        op = last_op[1:]

        if op_type == "ADD":
            redo = ["ADD"]
            for sphere_path in op:
                if is_prim_path_valid(sphere_path):
                    sphere = self.path_2_spheres[sphere_path]
                    redo.append(
                        {
                            "sphere_path": sphere_path,
                            "center": sphere.get_local_pose()[0],
                            "radius": sphere.get_radius(),
                        }
                    )
                self.delete_sphere(sphere_path)
            self._redo.append(redo)

        elif op_type == "DEL":
            redo = ["DEL"]
            for d in op:
                sphere = VisualSphere(
                    d["sphere_path"], translation=d["center"], radius=d["radius"], color=self.sphere_color
                )
                self.path_2_spheres[d["sphere_path"]] = sphere
                redo.append(d)
            self._redo.append(redo)

        elif op_type == "SCALE":
            redo = ["SCALE"]
            for d in op:
                path = d["sphere_path"]
                rad = d["radius"]
                factor = d["factor"]
                if path in self.path_2_spheres and is_prim_path_valid(path):
                    sphere = self.path_2_spheres[path]
                    sphere.set_radius(rad)
                    redo.append({"sphere_path": path, "radius": factor * rad})
            self._redo.append(redo)

    def redo(self):
        if len(self._redo) == 0:
            return

        last_redo = self._redo.pop()
        op_type = last_redo[0]
        op = last_redo[1:]

        if op_type == "ADD":
            added_spheres = ["ADD"]
            for d in op:
                sphere = VisualSphere(
                    d["sphere_path"], translation=d["center"], radius=d["radius"], color=self.sphere_color
                )
                self.path_2_spheres[sphere.prim_path] = sphere
                added_spheres.append(d["sphere_path"])
            self._operations.append(added_spheres)

        elif op_type == "DEL":
            deleted_spheres = ["DEL"]
            for d in op:
                self.delete_sphere(d["sphere_path"])
                deleted_spheres.append(d)
            self._operations.append(deleted_spheres)

        elif op_type == "SCALE":
            for d in op:
                path = d["sphere_path"]
                rad = d["radius"]
                if path in self.path_2_spheres and is_prim_path_valid(path):
                    sphere = self.path_2_spheres[path]
                    sphere.set_radius(rad)

    def add_sphere(self, link_path, center, radius, color=None, store_op=True):
        if not is_prim_path_valid(link_path):
            carb.log_warn("Attempted to add sphere nested under non-existent path")

        if link_path[-1] == "/":
            link_path = link_path[:-1]

        self._redo = []
        prim_path = find_unique_string_name(link_path + "/collision_sphere", lambda x: not is_prim_path_valid(x))
        if color is None:
            color = self.sphere_color

        sphere = VisualSphere(prim_path, translation=center, radius=radius, color=color)
        self.path_2_spheres[sphere.prim_path] = sphere
        if store_op:
            self._operations.append(["ADD", sphere.prim_path])

        return prim_path

    def load_spheres(self, robot, robot_description_file_path):
        self.clear_spheres(store_op=False)
        self._redo = []
        self._operations = []

        with open(robot_description_file_path, "r") as stream:
            try:
                parsed_file = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        sphere_list = parsed_file["collision_spheres"]

        robot_path = robot.prim_path

        added_sphere_paths = ["ADD"]
        for sphere_dict in sphere_list:
            for key, val in sphere_dict.items():
                link_path = robot_path + "/" + key
                if is_prim_path_valid(link_path):
                    for sphere in val:
                        center = np.array(sphere["center"])
                        radius = sphere["radius"]
                        sphere_path = self.add_sphere(link_path, center, radius, store_op=False)
                        added_sphere_paths.append(sphere_path)
                else:
                    carb.log_warn("Could not place sphere from robot description at path: {}".format(link_path))

        self._operations.append(added_sphere_paths)

    def interpolate_spheres(self, path1, path2, num_spheres):
        if not is_prim_path_valid(path1):
            carb.log_warn("{} is not a valid Prim path to a sphere".format(path1))
            return
        elif not is_prim_path_valid(path2):
            carb.log_warn("{} is not a valid Prim path to a sphere".format(path2))

        link_path = self._get_link_path(path1)
        if self._get_link_path(path2) != link_path:
            carb.log_warn(
                "Prim paths {} and {} are not nested under the same link.  They cannot be interpolated.".format(
                    path1, path2
                )
            )

        sphere_1 = self.path_2_spheres[path1]
        sphere_2 = self.path_2_spheres[path2]

        rad_1 = sphere_1.get_radius()
        rad_2 = sphere_2.get_radius()

        t1 = sphere_1.get_local_pose()[0]
        t2 = sphere_2.get_local_pose()[0]

        d = t2 - t1

        rads = np.linspace(rad_1, rad_2, num=num_spheres + 2)

        rad_ratios = rads[:-1] + rads[1:]
        rad_ratios = rad_ratios / np.sum(rad_ratios)

        total = 0
        added_sphere_paths = ["ADD"]
        for i in range(len(rad_ratios) - 1):
            ratio = rad_ratios[i]
            total += ratio
            sphere_path = self.add_sphere(link_path, t1 + total * d, rads[i + 1], store_op=False)
            added_sphere_paths.append(sphere_path)
        self._operations.append(added_sphere_paths)

    def scale_spheres(self, path, factor):
        scaled_spheres = ["SCALE"]
        path_len = len(path)

        for p in self.path_2_spheres.keys():
            if is_prim_path_valid(p) and p[:path_len] == path:
                sphere = self.path_2_spheres[p]
                rad = sphere.get_radius()
                sphere.set_radius(factor * rad)
                scaled_spheres.append({"sphere_path": p, "radius": rad, "factor": factor})
        self._operations.append(scaled_spheres)

    def save_spheres(self, robot, file_path):
        link_to_spheres = OrderedDict()
        robot_path_split = robot.prim_path.split("/")
        for sphere in self.path_2_spheres.values():
            prim_path = sphere.prim_path
            if is_prim_path_valid(prim_path):
                s = prim_path.split("/")
                if s[:-2] != robot_path_split:
                    carb.log_warn(
                        "Not sphere at path {} to file because it is not nested under the robot Articulation".format(
                            prim_path
                        )
                    )
                    continue
                link_name = s[-2]
                link_spheres = link_to_spheres.get(link_name, [])
                sphere_pose = self._round_list_floats(sphere.get_local_pose()[0])
                link_spheres.append({"center": sphere_pose, "radius": round(sphere.get_radius(), 3)})
                link_to_spheres[link_name] = link_spheres

        with open(file_path, "w") as f:
            f.write("collision_spheres:\n")
            for link_name, sphere_list in link_to_spheres.items():
                f.write("  - {}:\n".format(link_name))
                for sphere in sphere_list:
                    f.write('    - "center": {}\n'.format(sphere["center"]))
                    f.write('      "radius": {}\n'.format(sphere["radius"]))

    def _round_list_floats(self, l, decimals=3):
        r = []
        for f in l:
            r.append(round(f, decimals))
        return r

    def _get_link_path(self, sphere_path):
        # Remove last element of Prim path to sphere

        slash_ind = -1
        for i in range(len(sphere_path) - 1, -1, -1):
            if sphere_path[i] == "/":
                slash_ind = i
                break

        link_path = sphere_path[:slash_ind]
        return link_path
