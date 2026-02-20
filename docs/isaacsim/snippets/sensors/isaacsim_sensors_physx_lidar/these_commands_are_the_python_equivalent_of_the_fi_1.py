import asyncio

import omni.timeline


async def get_lidar_param():  # Function to retrieve data from the LIDAR
    await omni.kit.app.get_app().next_update_async()  # wait one frame for data
    timeline.pause()  # Pause the simulation to populate the LIDAR's depth buffers
    depth = lidarInterface.get_linear_depth_data("/World" + lidarPath)
    zenith = lidarInterface.get_zenith_data("/World" + lidarPath)
    azimuth = lidarInterface.get_azimuth_data("/World" + lidarPath)
    print("depth", depth)  # Print the data
    print("zenith", zenith)
    print("azimuth", azimuth)


timeline = omni.timeline.get_timeline_interface()
timeline.play()  # Start the Simulation
asyncio.ensure_future(get_lidar_param())  # Only ask for data after sweep is complete
