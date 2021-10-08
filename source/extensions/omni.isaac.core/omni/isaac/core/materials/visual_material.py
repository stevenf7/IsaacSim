# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
class VisualMaterial(object):
    def __init__(self, name, prim_path, prim, shaders_list, material) -> None:
        self._shaders_list = shaders_list
        self._material = material
        self._name = name
        self._prim_path = prim_path
        self._prim = prim_path
        return

    @property
    def material(self):
        return self._material

    @property
    def shaders_list(self):
        return self._shaders_list

    @property
    def name(self):
        return self._name

    @property
    def prim_path(self):
        return self._prim_path

    @property
    def prim(self):
        return self._prim
