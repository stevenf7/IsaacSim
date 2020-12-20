def update_location(om, start_location, lower_bound, upper_bound):
    om.set_transform(
        (start_location[0], start_location[1], start_location[2]),
        (lower_bound[0], lower_bound[1]),
        (upper_bound[0], upper_bound[1]),
    )
    om.update()


def compute_coordinates(om, cell_size):
    import numpy as np

    min_b = om.get_min_bound()
    max_b = om.get_max_bound()
    scale = cell_size
    half_w = scale * 0.5
    top_left = (max_b[0] - half_w, min_b[1] + half_w)
    top_right = (min_b[0] + half_w, min_b[1] + half_w)
    bottom_left = (max_b[0] - half_w, max_b[1] - half_w)
    bottom_right = (min_b[0] + half_w, max_b[1] - half_w)

    image_coords = np.matrix([[0, 1], [-1, 0]]) * np.matrix([[-top_left[0]], [-top_left[1]]])

    return top_left, top_right, bottom_left, bottom_right, image_coords


def generate_image(om, scale, occupied_col, unknown_col, freespace_col, start_location):
    from PIL import Image, ImageDraw

    points = om.get_occupied_positions()
    if len(points) == 0:
        print("No occupied points, cannot generate image")
        return None
    min_b = om.get_min_bound()
    max_b = om.get_max_bound()

    size = [0, 0, 0]

    size[0] = max_b[0] - min_b[0]
    size[1] = max_b[1] - min_b[1]
    size[2] = max_b[2] - min_b[2]

    image = unknown_col * (int(size[0] / scale) * int(size[1] / scale))
    for p in points:
        index = int(p[1] / scale - min_b[1] / scale) * int(size[0] / scale) + int(p[0] / scale - min_b[0] / scale)
        image[index * 4 + 0] = occupied_col[0]
        image[index * 4 + 1] = occupied_col[1]
        image[index * 4 + 2] = occupied_col[2]
        image[index * 4 + 3] = occupied_col[3]

    start_pix = (int(start_location[0] / scale - min_b[0] / scale), int(start_location[1] / scale - min_b[1] / scale))

    im = Image.frombytes("RGBA", (int(size[0] / scale), int(size[1] / scale)), bytes(image))
    ImageDraw.floodfill(
        im, start_pix, (freespace_col[0], freespace_col[1], freespace_col[2], freespace_col[3]), border=None, thresh=0
    )
    # Flip image to match what SDK expects
    im = im.transpose(Image.FLIP_LEFT_RIGHT)

    return im
