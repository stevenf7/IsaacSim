# Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

# This file is meant as a tool for the isaac sim developers to test and debug.
# It is not meant for users, so use at your own risk.
import sys

import carb
from omni.isaac.kit import SimulationApp

simulation_app = SimulationApp({"headless": False})
import omni
import omni.kit.viewport.utility
import omni.replicator.core as rep
from omni.isaac.core import SimulationContext
from omni.isaac.core.utils import nucleus, stage
from omni.isaac.core.utils.render_product import create_hydra_texture
from pxr import Gf, Sdf, UsdGeom, UsdPhysics


def printinc(i):
    print(f"{i}")
    return i + 1


i = 0

i = printinc(i)


def add_cube(stage, path, scale, offset, physics=False):
    cubeGeom = UsdGeom.Cube.Define(stage, path)
    cubePrim = stage.GetPrimAtPath(path)
    cubeGeom.CreateSizeAttr(1.0)
    cubeGeom.AddTranslateOp().Set(offset)
    cubeGeom.AddScaleOp().Set(scale)
    if physics:
        rigid_api = UsdPhysics.RigidBodyAPI.Apply(cubePrim)
        rigid_api.CreateRigidBodyEnabledAttr(True)

    UsdPhysics.CollisionAPI.Apply(cubePrim)
    return cubePrim


i = printinc(i)
simulation_app.update()

# Locate Isaac Sim assets folder to load environment and robot stages
assets_root_path = nucleus.get_assets_root_path()
if assets_root_path is None:
    carb.log_error("Could not find Isaac Sim assets folder")
    simulation_app.close()
    sys.exit()

i = printinc(i)
simulation_app.update()

geo_type = "cubes"
if len(sys.argv) >= 2:
    geo_type = sys.argv[1]

if 1:
    if geo_type == "warehouse":
        # Loading the simple_room environment
        stage.add_reference_to_stage(
            assets_root_path + "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd", "/background"
        )
    elif geo_type == "cubes":
        add_cube(stage.get_current_stage(), "/World/cxube_x1", (1, 20, 5), (5, 0, 0), physics=False)
        add_cube(stage.get_current_stage(), "/World/cxube_x2", (1, 20, 1), (-5, 0, 0), physics=False)
        add_cube(stage.get_current_stage(), "/World/cxube_x3", (20, 1, 1), (0, 5, 0), physics=False)
        add_cube(stage.get_current_stage(), "/World/cxube_x4", (20, 1, 1), (0, -5, 0), physics=False)
        add_cube(stage.get_current_stage(), "/World/cxube_x5", (20, 1, 1), (-5, -5, 0), physics=False)
        add_cube(
            stage.get_current_stage(),
            "/World/cube_5",
            (0.1764972, 2.0025313, 1.5832705),
            (-3.0258131660928367, 0, 0),
            physics=False,
        )
        # omni.kit.commands.execute('CreateAndBindMdlMaterialFromLibrary',
        #    mdl_name='OmniGlass.mdl',
        #    mtl_name='glass',
        #    mtl_created_list=['/World/Looks/glass'],
        #    bind_selected_prims=['/World/cube_5'])
        omni.kit.commands.execute(
            "CreateMdlMaterialPrim",
            mtl_url="omniverse://ov-isaac-dev/NVIDIA/Materials/OmniSurface/Glass/OmniSurface_Glass.mdl",
            mtl_name="OmniSurface_Glass",
            mtl_path="/World/Looks/OmniSurface_Glass",
        )
        omni.kit.commands.execute(
            "BindMaterialCommand",
            prim_path=["/World/cube_5"],
            material_path=Sdf.Path("/World/Looks/OmniSurface_Glass"),
            strength=None,
        )

        # omni.kit.commands.execute('CreateUsdAttributeOnPath',
        #    attr_path=Sdf.Path('/World/Looks/OmniSurface_Glass.SensorMaterialIndex'),
        #    attr_type=Sdf.ValueTypeNames.Int,
        #    custom=False,
        #    variability=Sdf.VariabilityUniform,
        #    attr_value=5)

    elif geo_type == "sphere":
        omni.kit.commands.execute(
            "CreatePrimWithDefaultXform",
            prim_type="Sphere",
            attributes={"radius": 5, "extent": [(-5, -5, -5), (5, 5, 5)]},
        )

lidar_config = "Example_Rotary"
lidar_config = "RPLIDAR_S2E"
if len(sys.argv) >= 3:
    lidar_config = sys.argv[2]

omni.kit.commands.execute(
    "CreatePrim", prim_type="DomeLight", attributes={"inputs:intensity": 1000, "inputs:texture:format": "latlong"}
)

i = printinc(i)
simulation_app.update()

# Create the lidar sensor that generates data into "RtxSensorCpu"
# Sensor needs to be rotated 90 degrees about X so that its Z up

# Possible options are Example_Rotary and Example_Solid_State
# drive sim applies 0.5,-0.5,-0.5,w(-0.5), we have to apply the reverse

i = printinc(i)
_, sensor = omni.kit.commands.execute(
    "IsaacSensorCreateRtxLidar",
    path="/sensor",
    parent=None,
    config=lidar_config,
    translation=(0, 0, -0.04),
    orientation=Gf.Quatd(0.5, 0.5, -0.5, -0.5),  # Gf.Quatd is w,i,j,k
)

if 0:
    _, sensor2 = omni.kit.commands.execute(
        "IsaacSensorCreateRtxLidar",
        path="/sensor2",
        parent=None,
        config=lidar_config,
        translation=(0, -1, 1.0),
        orientation=Gf.Quatd(0.5, 0.5, -0.5, -0.5),  # Gf.Quatd is w,i,j,k
    )

i = printinc(i)
_, render_product_path = create_hydra_texture([1, 1], sensor.GetPath().pathString)
# _, render_product_path2 = create_hydra_texture([1, 1], sensor2.GetPath().pathString)

# Create the debug draw pipeline in the post process graph
from omni.syntheticdata import sensors

i = printinc(i)
simulation_context = SimulationContext(physics_dt=1.0 / 60.0, rendering_dt=1.0 / 60.0, stage_units_in_meters=1.0)
writer = None
if 1:
    i = printinc(i)
    writer = rep.writers.get("RtxLidar" + "DebugDrawPointCloud" + "Buffer")
    # writer.initialize(testMode=True)
    # writer = rep.writers.get("RtxLidar" + "DebugDrawPointCloud")
    # writer = rep.writers.get("Writer" + "IsaacReadRTXLidarData")

    i = printinc(i)
    writer.attach([render_product_path])  # , render_product_path2])
    # writer2 = rep.writers.get("Writer" + "IsaacPrintRTXLidarInfo" + "")
    # writer2.attach([render_product_path])  # , render_product_path2])
else:
    # print("try RtxSensorCpuExportRaw")

    sensors.get_synthetic_data().activate_node_template(
        "RtxSensorCpu" + "IsaacComputeRTXLidarPointCloud",
        # "RtxSensorCpu" + "ExportRaw",
        # "RtxLidar" + "DebugDrawPointCloud",
        # "RtxSensorCpuIsaacReadRTXLidarData",
        0,
        [render_product_path],
    )


# disable_extension("omni.replicator.core")
i = printinc(i)
simulation_app.update()
simulation_app.update()


# omni.kit.commands.execute(
#    "ChangeProperty",
#    prop_path=Sdf.Path("/Render/PostProcess/SDGPipeline/DispatchSync.inputs:enabled"),
#    value=True,
#    prev=None,
# )

i = printinc(i)
simulation_context.play()

i = printinc(i)
if 0:
    # Use custom writer to see what the output of the annotator looks like
    class MyCustomWriter(rep.Writer):
        def __init__(self, output_dir: str):
            self.version = "0.0.2"
            self._frame_id = 0
            self.annotators = ["RtxSensorCpuIsaacCreateRTXLidarScanBuffer"]

        def on_final_frame(self):
            self.backend.sync_pending_paths()

        def write(self, data):
            print("Frame number - {}".format(self._frame_id))
            all_data = data["RtxSensorCpuIsaacCreateRTXLidarScanBuffer"]
            vel = ["velocity"]
            print(all_data)  # ["data"])
            print("*****************")
            self._frame_id += 1

    rep.WriterRegistry.register(MyCustomWriter)

    writer = rep.WriterRegistry.get("MyCustomWriter")
    writer.initialize(output_dir="")
    writer.attach([render_product_path])


# annotator = rep.AnnotatorRegistry.get_annotator("RtxSensorCpuIsaacCreateRTXLidarScanBuffer")
# annotator.attach([render_product_path])
annotatorFlat = rep.AnnotatorRegistry.get_annotator("RtxSensorCpuIsaacComputeRTXLidarFlatScan")
annotatorFlat.attach([render_product_path])
# annotatorLaser = rep.AnnotatorRegistry.get_annotator("RtxSensorCpuIsaacCreateRTXLidarLaserScan")
# annotatorLaser.attach([render_product_path])
while simulation_app.is_running():
    simulation_app.update()
    dataFlat = annotatorFlat.get_data()
    print("___Flat Data___")
    print(f'Len Flat {len(dataFlat["linearDepthData"])}')
    print(dataFlat)
    # dataLaser = annotatorLaser.get_data()
    # print("~~~Laser Data~~")
    # print(f'Len Laser {len(dataLaser["linearDepthData"])}')
    # print(dataLaser)
    # break

# cleanup and shutdown

i = printinc(i)
simulation_context.stop()

i = printinc(i)
simulation_app.close()
"""
# Snippet of similar code to use in script editor.
from omni.isaac.core.utils import stage
from pxr import UsdGeom, Gf

#omni.kit.commands.execute('ToolbarPlayButtonClicked')

UsdGeom.Cube.Define(stage.get_current_stage(), "/World/cube_1").AddTranslateOp().Set((5, 5, 0))
import omni.kit.commands
_, sensorR = omni.kit.commands.execute(
    "IsaacSensorCreateRtxLidar",
    path="/sensorR",
    parent=None,
    config="Example_Solid_State",
    translation=(0, 0, 1.0),
    orientation=Gf.Quatd(0.5, 0.5, -0.5, -0.5), 
)
from omni.isaac.core.utils.render_product import create_hydra_texture
_, render_product_pathR = create_hydra_texture([1, 1], sensorR.GetPath().pathString)


import omni.replicator.core as rep
# Create the debug draw pipeline in the post process graph
writerR = rep.writers.get("RtxLidar" + "DebugDrawPointCloud")
writerR.attach([render_product_pathR])

"""
