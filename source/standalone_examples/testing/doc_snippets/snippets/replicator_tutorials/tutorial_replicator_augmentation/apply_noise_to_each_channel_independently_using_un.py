def gaussian_noise_depth_np(data_in, sigma: float, seed: int):
    np.random.seed(seed)
    result = data_in.astype(np.float32) + np.random.randn(*data_in.shape) * sigma
    return np.clip(result, 0, None).astype(data_in.dtype)


rep.annotators.register_augmentation(
    "gn_depth_np", rep.annotators.Augmentation.from_function(gaussian_noise_depth_np, sigma=0.1, seed=SEED)
)


@wp.kernel
def gaussian_noise_depth_wp(
    data_in: wp.array2d(dtype=wp.float32), data_out: wp.array2d(dtype=wp.float32), sigma: float, seed: int
):
    i, j = wp.tid()
    # Unique ID for random seed per pixel
    scalar_pixel_id = i * data_in.shape[1] + j
    state = wp.rand_init(seed, scalar_pixel_id)
    data_out[i, j] = data_in[i, j] + sigma * wp.randn(state)


rep.annotators.register_augmentation(
    "gn_depth_wp", rep.annotators.Augmentation.from_function(gaussian_noise_depth_wp, sigma=0.1, seed=SEED)
)
