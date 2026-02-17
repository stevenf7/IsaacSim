cosmos_writer.initialize(
    backend=backend,
    use_instance_id=True,
    canny_threshold_low=10,  # Low threshold for hysteresis
    canny_threshold_high=100,  # High threshold for hysteresis
)
