from isaacsim import SimulationApp

# Example for creating a RTX lidar sensor and publishing PointCloud2 data
simulation_app = SimulationApp({"headless": False, "extra_args": ["--/rtx-transient/stableIds/enabled=true"]})
