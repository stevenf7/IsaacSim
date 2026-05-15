from isaacsim.sensors.rtx import get_gmo_data

# rawPtr is a raw GMO buffer pointer obtained from a deprecated
# OgnIsaacReadRTXLidarData OmniGraph node (removed in Isaac Sim 5.0).
gmo = get_gmo_data(rawPtr)  # noqa: F821
