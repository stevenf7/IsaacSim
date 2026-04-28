# Example: a per-point timestamp pulled from a PointCloud2 message field.
# In a real subscriber you'd read these from points["timestamp_0"] and
# points["timestamp_1"] (uint32 each).
timestamp_0 = 0xCAFEBABE  # low 32 bits
timestamp_1 = 0x12345678  # high 32 bits

# Recombine to a single uint64 nanosecond value.
ts_uint64_ns = (int(timestamp_1) << 32) | int(timestamp_0)
