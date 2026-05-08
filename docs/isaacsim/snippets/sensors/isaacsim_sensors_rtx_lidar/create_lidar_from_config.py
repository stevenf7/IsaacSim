from isaacsim.sensors.experimental.rtx import Lidar

# The SICK picoScan100 USD authors two variant sets ("Product" and "Profile"),
# so the variant must be passed as a dict mapping each variant set to its
# selection. For configs whose USD authors a single "sensor" variant set
# (e.g. Ouster OS1), pass a flat string instead -- e.g. variant="OS1_REV6_32ch20hz1024res".
lidar = Lidar.create(
    path="/World/lidar",
    config="picoScan100",
    variant={"Product": "picoScan150Pro", "Profile": "Profile11_15Hz_1p0deg"},
)
