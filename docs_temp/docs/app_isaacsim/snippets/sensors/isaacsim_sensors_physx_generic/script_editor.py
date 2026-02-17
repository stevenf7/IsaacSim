def _test_streaming_data(self):
    # custom pattern generation
    # send data in a batch that are at least large enough to run a few rendering frames without running out of data.
    # if batch_size > (sampling rate/rendering rate), the sensor will process all of the batches and ask for the next batch right before it runs out.
    # if batch_size < (sampling rate/rendering_rate), the sensor will scan only the provided rays in a given frame, which means it will be scanning slower than intended
    batch_size = int(1e6)  # size of each batch of data being processed
    half_batch = int(batch_size / 2)
    # example scanning pattern is a zigzag
    # each ray specified by an azimuth (horizontal angle measured from x-axis) and a zenith angle (vertical angle measured from z-axis)
    frequency = 10
    N_pts = int(batch_size / frequency / 2)
    # azimuth angle zigzag between the limits (frequency) times every batch
    azimuth = np.tile(
        np.append(np.linspace(-np.pi / 4, np.pi / 4, N_pts), np.linspace(np.pi / 4, -np.pi / 4, N_pts)), frequency
    )
    # zenith angle goes up and down once every batch
    zenith = np.append(np.linspace(-np.pi / 4, np.pi / 4, half_batch), np.linspace(np.pi / 4, -np.pi / 4, half_batch))
    # custom pattern must be sent as an array of [azimuth, zenith] angles.
    self.sensor_pattern = np.stack((azimuth, zenith))
