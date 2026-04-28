# -- Test setup --
import numpy as np

batch_size = int(1e6)

np.savetxt("filename.csv", np.column_stack([np.linspace(0, 360, 100), np.linspace(-15, 15, 100)]), delimiter=",")


class _Stub:
    _timeline = type("T", (), {"is_playing": lambda self: True})()
    _generic = True
    _pattern_set = True
    _genericPath = "/sensor"
    _sensor = type(
        "S",
        (),
        {
            "send_next_batch": lambda self, p: True,
            "set_next_batch_rays": lambda self, p, d: None,
            "set_next_batch_offsets": lambda self, p, d: None,
        },
    )()
    sensor_pattern = np.zeros((2, batch_size))
    origin_offsets = np.zeros((batch_size, 3))


self = _Stub()
# -- End test setup --


# [streaming-pattern]
def _test_streaming_data(self):
    batch_size = int(1e6)
    half_batch = int(batch_size / 2)
    frequency = 10
    N_pts = int(batch_size / frequency / 2)
    azimuth = np.tile(
        np.append(np.linspace(-np.pi / 4, np.pi / 4, N_pts), np.linspace(np.pi / 4, -np.pi / 4, N_pts)), frequency
    )
    zenith = np.append(np.linspace(-np.pi / 4, np.pi / 4, half_batch), np.linspace(np.pi / 4, -np.pi / 4, half_batch))
    self.sensor_pattern = np.stack((azimuth, zenith))


# [/streaming-pattern]

# [origin-offsets]
import numpy as np

# individual rays can have an offset at the origin
# adding random offsets to the origin for the example pattern
self.origin_offsets = 5 * np.random.random((batch_size, 3))
# self.origin_offsets = np.zeros((batch_size,3))                  # no offsets
# [/origin-offsets]

# [csv-import]
import numpy as np

## import data from file
sensor_pattern = np.loadtxt("filename.csv", delimiter=",")
batch_size = np.shape(sensor_pattern)[0]
sensor_pattern = np.deg2rad(sensor_pattern).T.copy()  ##  MUST USE .copy()
# [/csv-import]


# [repeating-pattern]
def _test_repeating_data(self):

    batch_size = int(1e6)
    half_batch = int(batch_size / 2)
    frequency = 10
    N_pts = int(batch_size / frequency / 2)
    azimuth = np.tile(
        np.append(np.linspace(-np.pi / 4, np.pi / 4, N_pts), np.linspace(np.pi / 4, -np.pi / 4, N_pts)), frequency
    )
    zenith = np.append(-0.5 * np.ones(half_batch), 0.5 * np.ones(half_batch))
    sensor_pattern = np.stack((azimuth, zenith))

    origin_offsets = 0.05 * np.random.random((batch_size, 3))


# [/repeating-pattern]


# [batch-callback]
def _on_editor_step(self, step):
    if not self._timeline.is_playing():
        return

    if self._timeline.is_playing():
        if self._generic:
            if self._pattern_set:
                if self._sensor.send_next_batch(
                    self._genericPath
                ):  # send_next_batch will turn True if the sensor is running out data and needs more
                    self._sensor.set_next_batch_rays(
                        self._genericPath, self.sensor_pattern
                    )  # set the next batch data using set_next_batch_rays()
                    self._sensor.set_next_batch_offsets(
                        self._genericPath, self.origin_offsets
                    )  # (Optional) add individual ray offsets if there are any


# [/batch-callback]
