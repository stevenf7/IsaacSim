# CPU noise kernel
def image_gaussian_noise_np(data_in: np.ndarray, seed: int, sigma: float = 25.0):
    np.random.seed(seed)
    return data_in + sigma * np.random.randn(*data_in.shape)
