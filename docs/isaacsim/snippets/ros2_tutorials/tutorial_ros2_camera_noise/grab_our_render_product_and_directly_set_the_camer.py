import warp as wp


# GPU Noise Kernel for illustrative purposes, input is rgba, outputs rgb
@wp.kernel
def image_gaussian_noise_warp(
    data_in: wp.array3d(dtype=wp.uint8), data_out: wp.array3d(dtype=wp.uint8), seed: int, sigma: float = 0.5
):
    i, j = wp.tid()
    dim_i = data_out.shape[0]
    dim_j = data_out.shape[1]
    pixel_id = i * dim_i + j
    state_r = wp.rand_init(seed, pixel_id + (dim_i * dim_j * 0))
    state_g = wp.rand_init(seed, pixel_id + (dim_i * dim_j * 1))
    state_b = wp.rand_init(seed, pixel_id + (dim_i * dim_j * 2))

    data_out[i, j, 0] = wp.uint8(float(data_in[i, j, 0]) + (255.0 * sigma * wp.randn(state_r)))
    data_out[i, j, 1] = wp.uint8(float(data_in[i, j, 1]) + (255.0 * sigma * wp.randn(state_g)))
    data_out[i, j, 2] = wp.uint8(float(data_in[i, j, 2]) + (255.0 * sigma * wp.randn(state_b)))
