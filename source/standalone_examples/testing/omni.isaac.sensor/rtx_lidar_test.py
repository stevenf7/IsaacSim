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
        # add_cube(stage.get_current_stage(), "/World/cxube_x2", (1, 20, 1000), (-5, 0, 500), physics=True)
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

lidar_config = "RPLIDAR_S2E"
lidar_config = "Example_Rotary"
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
    orientation=Gf.Quatd(1, 0, 0, 0),  # Gf.Quatd is w,i,j,k
)

if 0:
    _, sensor2 = omni.kit.commands.execute(
        "IsaacSensorCreateRtxLidar",
        path="/sensor2",
        parent=None,
        config=lidar_config,
        translation=(0, -1, 1.0),
        orientation=Gf.Quatd(1.0, 0.0, 0.0, 0.0),  # Gf.Quatd is w,i,j,k
    )

i = printinc(i)
hydra_texture = rep.create.render_product(sensor.GetPath(), [1, 1], name="Isaac")

# Create the debug draw pipeline in the post process graph
from omni.syntheticdata import sensors

i = printinc(i)
simulation_context = SimulationContext(physics_dt=1.0 / 60.0, rendering_dt=1.0 / 60.0, stage_units_in_meters=1.0)

i = printinc(i)
writer = rep.writers.get("" + "RtxLidar" + "DebugDrawPointCloud" + "Buffer")
# writer.initialize(testMode=True)
# writer = rep.writers.get("RtxLidar" + "DebugDrawPointCloud")
# writer = rep.writers.get("Writer" + "IsaacReadRTXLidarData")

i = printinc(i)
writer.attach([hydra_texture])  # , render_product_path2])


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
    writer.attach([hydra_texture])

annoNames = [
    "RtxSensorCpuIsaacReadRTXLidarData",
    "RtxSensorCpuIsaacComputeRTXLidarPointCloud",
    "RtxSensorCpuIsaacCreateRTXLidarScanBuffer",
    "RtxSensorCpuIsaacComputeRTXLidarFlatScan",
]
annotators = {}
for anno in annoNames:
    annotators[anno] = rep.AnnotatorRegistry.get_annotator(anno)
    # annotators[anno].initialize(keepOnlyPositiveDistance=True)
    annotators[anno].attach([hydra_texture])

while simulation_app.is_running():
    simulation_app.update()
    if simulation_context.is_playing():
        for anno in annotators:
            print(f"~~~{anno} Data~~")
            data = annotators[anno].get_data()
            for entry in data:
                print(f"{entry}: ", end="")
                if hasattr(data[entry], "__len__"):
                    print(f"len {len(data[entry])}::", end="")
                print(data[entry])
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
    orientation=Gf.Quatd(1.0, 0.0, 0.0, 0.0), 
)

hydra_textureR = rep.create.render_product(sensorR.GetPath(), [1, 1], name="Isaac")

import omni.replicator.core as rep
# Create the debug draw pipeline in the post process graph
writerR = rep.writers.get("RtxLidar" + "DebugDrawPointCloud")
writerR.attach([hydra_textureR])


~~~RtxSensorCpuIsaacReadRTXLidarData Data~~
azimuths: len 44314::[177.01157 177.01157 177.01157 ... 242.93082 242.93082 242.93082]
beamIds: len 44314::[  1   2   3 ... 120 121 122]
channels: len 44314::[  1   2   3 ... 120 121 122]
deltaTimes: len 44314::[    0     0     0 ... 24500 24500 24500]
depthRange: len 2::[  1. 200.]
distances: len 44314::[3.0346003 3.0229354 3.0139177 ... 5.07317   5.077657  5.082088 ]
echos: len 44314::[0 0 0 ... 0 0 0]
elevations: len 44314::[-14.19 -13.39 -12.58 ...   4.35   5.16   5.97]
emitterIds: len 44314::[  1   2   3 ... 120 121 122]
hitPointNormals: len 44314::[[ 1.0000000e+00  0.0000000e+00 -1.5259022e-05]
intensities: len 44314::[0.02724689 0.02596358 0.02481198 ... 0.02654433 0.02537464 0.02885798]
materialIds: len 44314::[31 31 31 ... 31 31 31]
numChannels: 128
numEchos: 2
numTicks: 600
objectIds: len 44314::[0 1 0 ... 5 0 5]
tickAzimuths: len 600::[180.01157 180.07787 180.182
ticks: len 44314::[  0   0   0 ... 599 599 599]
tickStates: len 600::[0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
tickTimestamps: len 600::[9069989788 9070017565 9070045343 9070073
velocities: len 44314::[[ 1.0000000e+00  0.0000000e+00 -1.5259022e-05]


~~~RtxSensorCpuIsaacComputeRTXLidarPointCloud Data~~
data: len 88546::[[-2.938008   -0.15337963 -0.7438964 ]
 [-2.9367614  -0.15331456 -0.70004576]
 [-2.9375618  -0.15335634 -0.656439  ]
 ...
 [-2.3034332   4.500231    0.3845605 ]
 [-2.3026571   4.4987154   0.4563726 ]
 [-2.3034947   4.500352    0.5286904 ]]
info: len 5::{'azimuth': array([ 3.0894349,  3.0894349,  3.0894349, ..., -2.043243 , -2.043243 ,
       -2.043243 ], dtype=float32), 'elevation': array([ 3.0894349,  3.0894349,  3.0894349, ..., -2.043243 , -2.043243 ,
       -2.043243 ], dtype=float32), 'intensity': array([0.06, 0.06, 0.06, ..., 0.06, 0.06, 0.07], dtype=float32), 'range': array([3.0346003, 3.0229354, 3.0139177, ..., 5.07317  , 5.077657 ,
       5.082088 ], dtype=float32), 'transform': array([ 1.  ,  0.  ,  0.  ,  0.  ,  0.  ,  1.  ,  0.  ,  0.  ,  0.  ,
        0.  ,  1.  ,  0.  , -0.  , -0.  , -0.04,  1.  ])}
~~~RtxSensorCpuIsaacCreateRTXLidarScanBuffer Data~~
azimuth: len 0::[]
beamId: len 0::[]
data: len 321971::[[ 4.4973907   0.23550124 -1.2467233 ]
 [ 4.5007486   0.23567706 -1.1795878 ]
 [ 4.4981613   0.23554158 -1.1122507 ]
 ...
 [ 4.5021296  -0.22803627  0.624865  ]
 [ 4.496782   -0.22776538  0.68844694]
 [ 4.501388   -0.22799872  0.7547338 ]]
distance: len 321971::[4.6624207 4.648757  4.63019   ... 4.5566673 4.561092  4.5766892]
elevation: len 0::[]
emitterId: len 0::[]
index: len 321971::[     0      2      4 ... 921594 921596 921598]
intensity: len 321971::[0.02719191 0.02366566 0.03149656 ... 0.03051874 0.02764517 0.0292189 ]
materialId: len 0::[]
normal: len 0::[]
objectId: len 0::[]
timestamp: len 0::[]
velocity: len 0::[]
info: len 6::{'numChannels': 128, 'numEchos': 2, 'numReturnsPerScan': 921600, 'renderProductPath': '/Render/RenderProduct_Isaac', 'ticksPerScan': 3600, 'transform': array([ 1.  ,  0.  ,  0.  ,  0.  ,  0.  ,  1.  ,  0.  ,  0.  ,  0.  ,
        0.  ,  1.  ,  0.  , -0.  , -0.  , -0.04,  1.  ])}
~~~RtxSensorCpuIsaacComputeRTXLidarFlatScan Data~~
azimuthRange: len 2::[-0.05235988  6.2308254 ]
depthRange: len 2::[  1. 200.]
horizontalFov: 360.0
horizontalResolution: 0.10000000149011612
intensitiesData: len 3600::[7 7 6 ... 7 7 7]
linearDepthData: len 3600::[4.502088  4.505737  4.5078583 ... 4.500911  4.5038576 4.505473 ]
numCols: 3600
numRows: 1
rotationRate: 10.0
"""
