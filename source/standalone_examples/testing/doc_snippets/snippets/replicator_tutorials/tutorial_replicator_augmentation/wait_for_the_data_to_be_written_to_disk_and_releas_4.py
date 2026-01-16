# Gaussian noise augmentation on rgba data in numpy (CPU) and warp (GPU)
def gaussian_noise_rgb_np(data_in, sigma: float, seed: int):
    np.random.seed(seed)
    data_in = data_in.astype(np.float32)
    data_in[:, :, 0] = data_in[:, :, 0] + np.random.randn(*data_in.shape[:-1]) * sigma
    data_in[:, :, 1] = data_in[:, :, 1] + np.random.randn(*data_in.shape[:-1]) * sigma
    data_in[:, :, 2] = data_in[:, :, 2] + np.random.randn(*data_in.shape[:-1]) * sigma
    data_in = np.clip(data_in, 0, 255).astype(np.uint8)
    return data_in


@wp.kernel
def gaussian_noise_rgb_wp(
    data_in: wp.array3d(dtype=wp.uint8), data_out: wp.array3d(dtype=wp.uint8), sigma: float, seed: int
):
    # Get thread coordinates and image dimensions to calculate unique pixel ID for random generation
    i, j = wp.tid()
    dim_i = data_in.shape[0]
    dim_j = data_in.shape[1]
    pixel_id = i * dim_i + j

    # Use pixel_id as offset to create unique seeds for each pixel and channel (ensure independent noise patterns across R,G,B channels)
    state_r = wp.rand_init(seed, pixel_id + (dim_i * dim_j * 0))
    state_g = wp.rand_init(seed, pixel_id + (dim_i * dim_j * 1))
    state_b = wp.rand_init(seed, pixel_id + (dim_i * dim_j * 2))

    # Apply noise to each channel independently using unique seeds
    data_out[i, j, 0] = wp.uint8(wp.int32(data_in[i, j, 0]) + wp.int32(sigma * wp.randn(state_r)))
    data_out[i, j, 1] = wp.uint8(wp.int32(data_in[i, j, 1]) + wp.int32(sigma * wp.randn(state_g)))
    data_out[i, j, 2] = wp.uint8(wp.int32(data_in[i, j, 2]) + wp.int32(sigma * wp.randn(state_b)))
    data_out[i, j, 3] = data_in[i, j, 3]
