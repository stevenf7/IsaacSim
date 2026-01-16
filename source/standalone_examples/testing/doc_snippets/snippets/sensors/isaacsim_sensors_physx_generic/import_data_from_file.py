def _test_repeating_data(self):

    batch_size = int(1e6)  # size of each batch of data being processed
    half_batch = int(batch_size / 2)
    frequency = 10
    N_pts = int(batch_size / frequency / 2)
    azimuth = np.tile(
        np.append(np.linspace(-np.pi / 4, np.pi / 4, N_pts), np.linspace(np.pi / 4, -np.pi / 4, N_pts)), frequency
    )
    zenith = np.append(-0.5 * np.ones(half_batch), 0.5 * np.ones(half_batch))
    sensor_pattern = np.stack((azimuth, zenith))

    origin_offsets = 0.05 * np.random.random((batch_size, 3))
