#!/usr/bin/env python
import numpy as np
from PIL import Image


def line_seg_closest_point(v0, v1, p0):
    d = v1 - v0
    q = p0 - v0

    t = np.dot(q, d) / np.dot(d, d)
    t = np.clip(t, 0, 1)

    return v0 + t * d


def line_seg_distance(v0, v1, p0):
    p = line_seg_closest_point(v0, v1, p0)

    return np.linalg.norm(p0 - p)


# centered at origin, arc starts at 0
def canonical_arc_distance(R, a0, x):
    a = np.arctan2(x[1], x[0])

    if a < 0:
        a = a + 2 * np.pi

    if a > a0:
        if a < a0 / 2 + np.pi:
            a = a0
        else:
            a = 0
    p = R * np.array([np.cos(a), np.sin(a)])

    return np.linalg.norm(x - p)


def arc_distance(c, r, a0, a1, x):
    # Point relative to arc origin
    x0 = x - c

    # Rotate point to canonical angle (where arc starts at 0)
    c = np.cos(-a0)
    s = np.sin(-a0)
    R = np.array([[c, -s], [s, c]])

    x0 = np.dot(R, x0)

    return canonical_arc_distance(r, a1 - a0, x0)


def arc_endpoints(c, r, a0, a1):

    c0 = np.cos(a0)
    s0 = np.sin(a0)
    c1 = np.cos(a1)
    s1 = np.sin(a1)

    return c + r * np.array([[c0, s0], [c1, s1]])


# measurements
m0 = 7.620
m1 = 10.668
m2 = 5.491
m3 = 3.048
m4 = 4.348
m5 = 5.380

# track width
w = 1.22
w_2 = w / 2

# arcs
# bottom left
c0 = np.array([w, w])
r0 = w_2
a0 = [np.pi, np.pi * 1.5]

# top left
c1 = np.array([m3, m0])
r1 = m3 - w_2
a1 = [1.75 * np.pi, 3 * np.pi]
ep1 = arc_endpoints(c1, r1, a1[0], a1[1])


c2 = np.array([m5, m4])
r2 = 0.5 * (2.134 + 0.914)
a2 = [0.75 * np.pi, 1.25 * np.pi]
ep2 = arc_endpoints(c2, r2, a2[0], a2[1])

c3 = np.array([m2, w])
r3 = w_2
a3 = [np.pi * 1.5, np.pi * 2.25]
ep3 = arc_endpoints(c3, r3, a3[0], a3[1])


# line segment points
v0 = np.array([w_2, w])
v1 = np.array([w_2, m0])
v2 = ep1[0]
v3 = ep2[0]
v4 = ep2[1]
v5 = ep3[1]
v6 = np.array([m2, w_2])
v7 = np.array([w, w_2])


def center_line_dist(p):
    p = 0.01 * p  # convert from m to cm
    d0 = line_seg_distance(v0, v1, p)
    d1 = line_seg_distance(v2, v3, p)
    d2 = line_seg_distance(v4, v5, p)
    d3 = line_seg_distance(v6, v7, p)
    d4 = arc_distance(c0, r0, a0[0], a0[1], p)
    d5 = arc_distance(c1, r1, a1[0], a1[1], p)
    d6 = arc_distance(c2, r2, a2[0], a2[1], p)
    d7 = arc_distance(c3, r3, a3[0], a3[1], p)

    return np.min([d0, d1, d2, d3, d4, d5, d6, d7])


def is_racing_forward(prev_pose, curr_pose):
    # LANE_WIDTH = 0.7 #width of track is w = 1.22
    # TRACK_DIMS = [671, 1066] # the track is within (0, 0) to (671.1 cm, 1066.8 cm)
    prev_pose = 0.01 * prev_pose
    curr_pose = 0.01 * curr_pose

    bottom_left_corner = np.array([0, 0])
    top_left_corner = np.array([0, 10.668])
    top_right_corner = np.array([6.711, 10.668])
    bottom_right_corner = np.array([6.711, 0])

    d0 = line_seg_distance(bottom_left_corner, top_left_corner, curr_pose)
    d1 = line_seg_distance(top_left_corner, top_right_corner, curr_pose)
    d2 = line_seg_distance(top_right_corner, bottom_right_corner, curr_pose)
    d3 = line_seg_distance(bottom_right_corner, bottom_left_corner, curr_pose)

    min_d = np.min([d0, d1, d2, d3])

    which_side = np.array([0, 0])
    if min_d == d0:
        which_side = top_left_corner - bottom_left_corner
    elif min_d == d1:
        which_side = top_right_corner - top_left_corner
    elif min_d == d2:
        which_side = bottom_right_corner - top_right_corner
    elif min_d == d3:
        which_side = bottom_left_corner - bottom_right_corner

    which_size_unit = which_side / np.linalg.norm(which_side)

    curr_vel = curr_pose - prev_pose
    curr_vel_unit = curr_vel / np.linalg.norm(curr_vel)

    return np.dot(curr_vel_unit, which_size_unit)


if __name__ == "__main__":

    # scale
    s = 0.02

    H = int(10668 * s)
    W = int(6711 * s)

    d = np.zeros((H, W))

    for i in range(H):
        y = ((i + 0.5) / s) / 1000.0
        if i % 10 == 0:
            print(y)
        for j in range(W):
            x = ((j + 0.5) / s) / 1000.0

            p = np.array([x, y])

            d[i, j] = center_line_dist(p)

    im = Image.fromarray((np.flipud(d) * 255 / np.max(d)).astype("uint8"))
    im.save("dist.png")
    im.show()
