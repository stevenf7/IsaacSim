# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tier: spatial.py geometry/pathfinding helpers (numpy + stdlib)."""

from __future__ import annotations

import pytest
from _util import load_module_from_path, skill_path

pytestmark = pytest.mark.unit

pytest.importorskip("numpy")
import numpy as np  # noqa: E402

SPATIAL_PY = skill_path("spatial-reasoning", "scripts", "spatial.py")


@pytest.fixture(scope="module")
def sp():
    return load_module_from_path(SPATIAL_PY)


# --------------------------------------------------------------------------- #
# quaternions
# --------------------------------------------------------------------------- #
def test_euler_to_quat_identity(sp):
    assert sp.euler_to_quat(0, 0, 0) == pytest.approx((1, 0, 0, 0))


def test_euler_to_quat_90z(sp):
    assert sp.euler_to_quat(0, 0, 90) == pytest.approx((0.70710678, 0, 0, 0.70710678))


def test_quat_to_matrix_identity(sp):
    assert sp.quat_to_matrix((1, 0, 0, 0)) == [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


def test_quat_to_matrix_90z(sp):
    m = sp.quat_to_matrix(sp.euler_to_quat(0, 0, 90))
    assert np.allclose(np.array(m), [[0, -1, 0], [1, 0, 0], [0, 0, 1]], atol=1e-6)


def test_slerp_endpoints(sp):
    q0, q1 = (1, 0, 0, 0), sp.euler_to_quat(0, 0, 90)
    assert sp.slerp(q0, q1, 0.0) == pytest.approx(q0)
    assert sp.slerp(q0, q1, 1.0) == pytest.approx(q1)


def test_slerp_midpoint_is_45z(sp):
    mid = sp.slerp((1, 0, 0, 0), sp.euler_to_quat(0, 0, 90), 0.5)
    assert mid == pytest.approx(sp.euler_to_quat(0, 0, 45), abs=1e-6)


# --------------------------------------------------------------------------- #
# transform decomposition
# --------------------------------------------------------------------------- #
def test_decompose_transform(sp):
    # USD matrices are doubles; use floats (in-place normalize needs a float dtype).
    M = [[2.0, 0, 0, 0], [0, 3.0, 0, 0], [0, 0, 4.0, 0], [5.0, 6.0, 7.0, 1.0]]
    t, R, s = sp.decompose_transform(M)
    assert np.allclose(t, [5, 6, 7])
    assert np.allclose(s, [2, 3, 4])
    assert np.allclose(R, np.eye(3))


# --------------------------------------------------------------------------- #
# spatial indices
# --------------------------------------------------------------------------- #
def test_rtree_insert_and_query(sp):
    root = sp.RTreeNode()
    root.insert((0, 0, 1, 1), "a")
    root.insert((5, 5, 6, 6), "b")
    hits = [d for _, d in root.query_range((0.5, 0.5, 0.7, 0.7))]
    assert hits == ["a"]


def test_spatial_grid_placement(sp):
    g = sp.SpatialGrid(20, 20, cell_size=2.0)
    g.insert(0, 0, 2, 2, object())
    assert g.check_placement(0.5, 0.5, 1, 1) is True
    assert g.check_placement(15, 15, 1, 1) is False


# --------------------------------------------------------------------------- #
# collision / pathfinding
# --------------------------------------------------------------------------- #
def test_gjk_disjoint(sp):
    a = [(0, 0), (2, 0), (2, 2), (0, 2)]
    far = [(10, 10), (12, 10), (12, 12), (10, 12)]
    assert sp.gjk_overlap_2d(a, far) is False


def test_gjk_identical_overlap(sp):
    a = [(0, 0), (2, 0), (2, 2), (0, 2)]
    assert sp.gjk_overlap_2d(a, list(a)) is True


def test_astar_open_grid(sp):
    grid = [[0] * 5 for _ in range(5)]
    path = sp.astar_warehouse(grid, (0, 0), (4, 4), cell_size=1.0)
    assert path is not None
    assert path[0] == pytest.approx((0, 0))
    assert path[-1] == pytest.approx((4, 4))


def test_astar_blocked(sp):
    grid = [[0, 0, 0], [1, 1, 1], [0, 0, 0]]
    assert sp.astar_warehouse(grid, (0, 0), (0, 2), cell_size=1.0) is None


# --------------------------------------------------------------------------- #
# splines
# --------------------------------------------------------------------------- #
def test_catmull_rom_endpoints(sp):
    p0, p1, p2, p3 = (0, 0), (1, 1), (2, 0), (3, 1)
    assert sp.catmull_rom_point(p0, p1, p2, p3, 0.0) == pytest.approx(p1, abs=1e-6)
    assert sp.catmull_rom_point(p0, p1, p2, p3, 1.0) == pytest.approx(p2, abs=1e-6)


def test_smooth_path_lengths(sp):
    assert sp.smooth_path([(0, 0), (1, 1), (2, 0)]) == [(0, 0), (1, 1), (2, 0)]  # < 4 -> unchanged
    pts = [(0, 0), (1, 1), (2, 0), (3, 1), (4, 0)]
    assert len(sp.smooth_path(pts, points_per_segment=8)) > len(pts)


# --------------------------------------------------------------------------- #
# bin packing
# --------------------------------------------------------------------------- #
def test_maxrects_pack(sp):
    binp = sp.MaxRectsBinPack(10, 10)
    assert binp.insert(4, 4) == (0, 0)
    assert binp.insert(4, 4) is not None
    assert binp.insert(20, 20) is None
    assert 0 < binp.utilization() <= 1


# --------------------------------------------------------------------------- #
# frustum culling
# --------------------------------------------------------------------------- #
def test_bbox_in_frustum_single_plane(sp):
    planes = [((1.0, 0.0, 0.0), 0.0)]  # keep x >= 0
    assert sp.bbox_in_frustum((1, 1, 1), (2, 2, 2), planes) is True
    assert sp.bbox_in_frustum((-2, -2, -2), (-1, -1, -1), planes) is False


def test_vector_helpers(sp):
    assert sp.dot((1, 2, 3), (4, 5, 6)) == 32
    assert sp.cross((1, 0, 0), (0, 1, 0)) == (0, 0, 1)
    assert sp.add((1, 2, 3), (1, 1, 1)) == (2, 3, 4)
    assert sp.sub((1, 2, 3), (1, 1, 1)) == (0, 1, 2)
    assert sp.neg((1, -2, 3)) == (-1, 2, -3)
    assert sp.scale((1, 2, 3), 2) == (2, 4, 6)
    assert sp.normalize((3, 0, 0)) == pytest.approx((1.0, 0.0, 0.0))
    assert sp.normalize((0, 0, 0)) == (0.0, 0.0, 0.0)


def test_frustum_planes_culls(sp):
    planes = sp.frustum_planes(
        eye=(0.0, 0.0, 0.0), forward=(0.0, 1.0, 0.0), up=(0.0, 0.0, 1.0), fov_h=90.0, fov_v=90.0, near=0.1, far=100.0
    )
    assert len(planes) == 6
    # box in front of the camera (+Y) is visible; box behind it is culled
    assert sp.bbox_in_frustum((-0.5, 4.5, -0.5), (0.5, 5.5, 0.5), planes) is True
    assert sp.bbox_in_frustum((-0.5, -5.5, -0.5), (0.5, -4.5, 0.5), planes) is False


# --------------------------------------------------------------------------- #
# camera distance
# --------------------------------------------------------------------------- #
def test_compute_camera_distance_monotonic(sp):
    small = sp.compute_camera_distance(1.0, 1.0)
    big = sp.compute_camera_distance(2.0, 2.0)
    assert small > 0 and big > small


# --------------------------------------------------------------------------- #
# USD-dependent helper: builds Gf matrices (needs pxr at call time)
# --------------------------------------------------------------------------- #
def test_bake_waypoints_writes_samples(sp):
    pytest.importorskip("pxr")

    samples = {}

    class _Op:
        def Set(self, value, frame):  # noqa: N802 (USD API shape)
            samples[frame] = value

    sp.bake_waypoints(_Op(), [(0, 0), (10, 0)], speed_mps=2.0, fps=30)
    assert samples, "bake_waypoints wrote no timeSamples"
    assert 0 in samples
    assert all(frame % 2 == 0 for frame in samples)
