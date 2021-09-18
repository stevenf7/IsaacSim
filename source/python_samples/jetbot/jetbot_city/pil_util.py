import numpy as np
from PIL import Image, ImageFilter
import math


# Equivalent of cv2.circle
def circle(mask, origin, radius, thickness=1):
    R = radius
    orig = origin

    for row in range(mask.shape[0]):
        for col in range(mask.shape[1]):
            x = col - orig[0]
            y = row - orig[1]
            r = np.round(math.sqrt(x ** 2 + y ** 2))

            if r >= R - thickness // 2 and r <= R + thickness // 2:
                mask[row, col] = 255
            else:
                continue
    return mask


# Equivalent of cv2.line
def line(mask, P1, P2, thickness=1):

    p1 = np.array(P1)
    p2 = np.array(P2)

    # Normalized vector
    d = p2 - p1
    n = p2 - p1
    norm = np.linalg.norm(n)
    if norm > 0:
        n = n / norm

    for row in range(mask.shape[0]):
        for col in range(mask.shape[1]):

            p = np.array([col, row])

            t = np.dot(p - p1, n) / norm
            t = np.clip(t, 0, 1)

            proj = p1 + t * d

            r = np.linalg.norm(p - proj)

            if r <= thickness / 2.0:
                mask[row, col] = 255

    return mask


def Laplacian(image_array):
    PIL_im = Image.fromarray(image_array)
    return np.array(PIL_im.filter(ImageFilter.FIND_EDGES))
