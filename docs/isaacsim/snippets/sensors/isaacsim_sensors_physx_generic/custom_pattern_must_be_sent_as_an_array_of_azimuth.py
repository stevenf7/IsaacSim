import numpy as np

# individual rays can have an offset at the origin
# adding random offsets to the origin for the example pattern
self.origin_offsets = 5 * np.random.random((batch_size, 3))
# self.origin_offsets = np.zeros((batch_size,3))                  # no offsets
