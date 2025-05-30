# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ctypes
import os
from dataclasses import dataclass
from typing import Literal, Tuple

import carb
import isaacsim.sensors.rtx.generic_model_output as gmo_utils
import numpy as np
import omni.kit.test
import omni.replicator.core as rep
from isaacsim.core.api import World
from isaacsim.core.api.objects import VisualCuboid
from isaacsim.core.utils.stage import create_new_stage_async, update_stage_async
from isaacsim.sensors.rtx import get_gmo_data
from isaacsim.storage.native import get_assets_root_path
from pxr import Gf, Usd

# Number of extra frames to render to ensure sensor generates returns. Note increasing this number will increase the time it takes to run the tests.
NUM_EXTRA_FRAMES = 8


class TestRTXSensorAnnotator(omni.kit.test.AsyncTestCase):
    """Test class for RTX sensor annotators"""

    # This class is not meant to be run as a test, but rather to be used as a base class for other tests
    __test__ = False
    _assets_root_path = get_assets_root_path()
    _accumulate_returns = False

    async def setUp(self):
        """Setup test environment with a cube and lidar"""
        await create_new_stage_async()
        self.my_world = World(stage_units_in_meters=1.0)
        await self.my_world.initialize_simulation_context_async()
        await update_stage_async()

        # TODO (adevalla): Clean up how octant dimensions are defined and map to the sarcophagus.
        # For now ordering octants in binary order, such that octant 0 is +++, octant 1 is ++-, etc. for XYZ.
        self._octant_dimensions = [
            (10, 10, 5),
            (10, 10, 7),
            (25, 25, 17),
            (25, 25, 19),
            (15, 15, 9),
            (15, 15, 11),
            (20, 20, 13),
            (20, 20, 15),
        ]

        # Autogenerate sarcophagus
        dims = [(10, 5, 7), (15, 9, 11), (20, 13, 15), (25, 17, 19)]
        i = 0
        for l, h1, h2 in dims:
            h = h1 + h2
            x_sign = -1 if 0 < i < 3 else 1
            y_sign = -1 if i > 1 else 1
            signs = np.array([x_sign, y_sign, 1])
            VisualCuboid(
                prim_path=f"/World/cube_{i*4}",
                name=f"cube_{i*4}",
                position=np.multiply(signs, np.array([l + 0.5, l / 2, h1 - h / 2])),
                scale=np.array([1, l, h]),
            )
            VisualCuboid(
                prim_path=f"/World/cube_{i*4+1}",
                name=f"cube_{i*4+1}",
                position=np.multiply(signs, np.array([l / 2, l + 0.5, h1 - h / 2])),
                scale=np.array([l, 1, h]),
            )
            VisualCuboid(
                prim_path=f"/World/cube_{i*4+2}",
                name=f"cube_{i*4+2}",
                position=np.multiply(signs, np.array([l / 2, l / 2, h1 + 0.5])),
                scale=np.array([l, l, 1]),
            )
            VisualCuboid(
                prim_path=f"/World/cube_{i*4+3}",
                name=f"cube_{i*4+3}",
                position=np.multiply(signs, np.array([l / 2, l / 2, -h2 - 0.5])),
                scale=np.array([l, l, 1]),
            )
            i += 1

        self._timeline = omni.timeline.get_timeline_interface()
        self._annotator_data = None

    async def _test_annotator_result(self):
        """Tests the annotator result."""
        self.assertIn("gmoBufferPointer", self._annotator_data)
        self.assertIn("gmoDeviceIndex", self._annotator_data)
        self.assertNotEqual(self._annotator_data["gmoBufferPointer"], 0, "Expected nonzero GMO buffer pointer.")

        gmo = get_gmo_data(self._annotator_data["gmoBufferPointer"])
        await self._test_returns(az_vals=gmo.x, el_vals=gmo.y, r_vals=gmo.z, flags=gmo.flags)
        return

    async def _test_returns(
        self, az_vals: np.array, el_vals: np.array, r_vals: np.array, flags: np.array, cartesian: bool = False
    ) -> None:
        """Tests sensor returns stored in GMO buffer against expected range, for a given set of azimuth and elevation values.

        Args:
            az_vals (np.array): azimuth values (degrees)
            el_vals (np.array): elevation values (degrees)
            r_vals (np.array): range values (meters)
            cartesian (bool): If True, assumes inpus are in Cartesian coordinates - az = x, el = y, r = z, all in meters. Default False.
        """
        # NOTE: if an element of unit_vecs is 0, indicating the return vector is parallel to the plane, the result of np.divide will be inf
        # Suppress the error
        np.seterr(divide="ignore")

        # Test for invalid returns
        is_return_invalid = np.bitwise_and(flags, 64) == 0
        num_returns = np.size(flags)
        num_invalid_returns = np.sum(is_return_invalid)
        num_valid_returns = num_returns - num_invalid_returns
        carb.log_warn(
            f"There are {num_invalid_returns} invalid returns out of {num_returns} returns - {num_invalid_returns/num_returns*100}% are invalid."
        )
        # self.assertLessEqual(num_invalid_returns/np.length(flags), 1e-2, "Expected fewer than 1% of returns to be invalid.")

        # Remove invalid returns
        az_vals = az_vals[np.logical_not(is_return_invalid)]
        el_vals = el_vals[np.logical_not(is_return_invalid)]
        r_vals = r_vals[np.logical_not(is_return_invalid)]

        if not cartesian:
            # Get cartesian unit vectors from spherical coordinates
            azr = np.deg2rad(az_vals)
            elr = np.deg2rad(el_vals)
            x = np.multiply(np.cos(azr), np.cos(elr))
            y = np.multiply(np.sin(azr), np.cos(elr))
            z = np.sin(elr)
            unit_vecs = np.concatenate((x[..., None], y[..., None], z[..., None]), axis=1)
        else:
            unit_vecs = np.concatenate((az_vals[..., None], el_vals[..., None], r_vals[..., None]), axis=1)
            r_vals = np.linalg.norm(unit_vecs, axis=1)
            # Normalize unit vectors
            unit_vecs = np.divide(unit_vecs, np.repeat(r_vals[:, None], 3, axis=1))
            # Get spherical coordinates from cartesian unit vectors
            az_vals = np.arctan2(unit_vecs[:, 1], unit_vecs[:, 0])
            el_vals = np.arcsin(unit_vecs[:, 2])

        # Get octant dimensions and indices
        octant = (unit_vecs[:, 0] < 0) * 4 + (unit_vecs[:, 1] < 0) * 2 + (unit_vecs[:, 2] < 0)
        dims = np.array([self._octant_dimensions[o] for o in octant])

        # Let alpha be the angle between the normal to the plane and the return vector
        # Let the distance from the origin of the return vector along the normal vector to the plane be l =  dims(idx)
        # Let expected range R be the distance along the return vector to the point of intersection with the plane
        # Then, cos(alpha) = l / R
        # Next, observe cos(alpha) = n-hat dot r-hat, where n-hat is the unit normal vector to the plane
        # and r-hat is the unit return vector
        # Therefore, R = l / (n-hat dot r-hat)
        # n-hat dot r-hat is simply the index of the unit return vector corresponding to the plane
        # This simplifies the computation of expected range to elementwise-division of the dimensions by the unit return vectors
        # The minimum of these values is the expected range to the first plane the return vector will intersect
        expected_range = np.min(np.divide(dims, np.abs(unit_vecs)), axis=1)

        # Compute percent differences, and count the number of returns that exceed the threshold of 1%
        percent_diffs = np.divide(np.abs(expected_range - r_vals), expected_range)

        # Find where returns were not within 0.5deg of an octant edge
        not_near_edge = [
            not (abs(a) > 0.5 or abs(a - 90) < 0.5 or abs(a - 180) < 0.5 or abs(a + 180) < 0.5) for a in az_vals
        ]

        # Compute the number of returns that exceed the threshold of 1%, beyond edges of the octants
        num_exceeding_threshold = np.sum(np.logical_and(percent_diffs > 1e-2, np.array(not_near_edge)))
        pct_exceeding_threshold = num_exceeding_threshold / num_valid_returns * 100
        self.assertLessEqual(
            pct_exceeding_threshold,
            1.0,
            f"Expected fewer than 1% of returns to differ from expected range by more than 1%. {num_exceeding_threshold} of {num_valid_returns} valid returns exceeded threshold.",
        )


class TestIsaacComputeRTXLidarFlatScan(TestRTXSensorAnnotator):
    """Test the Isaac Compute RTX Lidar Flat Scan annotator"""

    __test__ = True
    _annotator = rep.AnnotatorRegistry.get_annotator("IsaacComputeRTXLidarFlatScan")
    _accumulate_returns = True

    async def _test_annotator_result(self):
        """Tests the annotator result."""

        # Test that all expected keys are present in the annotator data, then copy those values to the test class attributes
        for expected_key in [
            "azimuthRange",
            "depthRange",
            "horizontalFov",
            "horizontalResolution",
            "intensitiesData",
            "linearDepthData",
            "numCols",
            "numRows",
            "rotationRate",
        ]:
            self.assertIn(expected_key, self._annotator_data)
            setattr(self, expected_key, self._annotator_data[expected_key])

        # Confirm default values for 3D lidar
        if not self._is_2d_lidar:
            self.assertTrue(np.allclose(np.zeros([1, 2]), self.azimuthRange))
            self.assertTrue(np.allclose(np.zeros([1, 2]), self.depthRange))
            self.assertEqual(0.0, self.horizontalFov)
            self.assertEqual(0.0, self.horizontalResolution)
            self.assertEqual(0, self.intensitiesData.size)
            self.assertEqual(0, self.linearDepthData.size)
            self.assertEqual(0, self.numCols)
            self.assertEqual(1, self.numRows)
            self.assertEqual(0.0, self.rotationRate)
            return

        # Construct azimuth and elevation vectors, then test returns
        num_elements = self.numCols
        self.assertGreater(num_elements, 0, "Expecting more than zero elements in output.")
        azimuth_vals = np.linspace(self.azimuthRange[0], self.azimuthRange[1], num_elements)
        elevation_vals = np.zeros_like(azimuth_vals)
        flags = np.ones_like(azimuth_vals, dtype=np.int8) * 64
        # Assume all returns are valid
        await self._test_returns(az_vals=azimuth_vals, el_vals=elevation_vals, r_vals=self.linearDepthData, flags=flags)


class TestIsaacExtractRTXSensorPointCloudNoAccumulator(TestRTXSensorAnnotator):
    """Test the Isaac Extract RTX Sensor Point Cloud annotator without accumulator"""

    __test__ = True
    _annotator = rep.AnnotatorRegistry.get_annotator("IsaacExtractRTXSensorPointCloud" + "NoAccumulator")

    async def _test_annotator_result(self):
        """Tests the annotator result."""
        # Test that all expected keys are present in the annotator data, then copy those values to the test class attributes
        self.assertIn("data", self._annotator_data)
        self.data = self._annotator_data["data"]

        self.assertIn("info", self._annotator_data)
        for expected_key in [
            "transform",
            "sensorOutputBuffer",
        ]:
            self.assertIn(expected_key, self._annotator_data["info"])
            setattr(self, expected_key, self._annotator_data["info"][expected_key])

        # Test returns
        self.assertNotEqual(self.sensorOutputBuffer, 0, "Expected nonzero GMO buffer pointer.")
        gmo = get_gmo_data(self.sensorOutputBuffer)
        await self._test_returns(az_vals=gmo.x, el_vals=gmo.y, r_vals=gmo.z, flags=gmo.flags)

        # Test transform
        posM = Gf.Vec3d(gmo.frameEnd.posM[0], gmo.frameEnd.posM[1], gmo.frameEnd.posM[2])
        pose = Gf.Quatd(
            gmo.frameEnd.orientation[3],
            gmo.frameEnd.orientation[0],
            gmo.frameEnd.orientation[1],
            gmo.frameEnd.orientation[2],
        )
        expected_transform = Gf.Transform(posM, Gf.Rotation(pose))
        self.assertTrue(np.allclose(np.reshape(self.transform, [4, 4]), expected_transform.GetMatrix()))

        # Test data (cartesian)
        self.assertEqual(self.data.shape[0], gmo.numElements)
        self.assertEqual(self.data.shape[1], 3)
        await self._test_returns(self.data[:, 0], self.data[:, 1], self.data[:, 2], flags=gmo.flags, cartesian=True)

        # # Test buffer size
        # self.assertEqual(self.bufferSize, gmo.numElements * 3 * 8)

        # # Test height and width
        # self.assertEqual(self.height, 1)
        # self.assertEqual(self.width, gmo.numElements)

        return


class TestIsaacExtractRTXSensorPointCloud(TestIsaacExtractRTXSensorPointCloudNoAccumulator):
    """Test the Isaac Extract RTX Sensor Point Cloud annotator"""

    __test__ = True
    _annotator = rep.AnnotatorRegistry.get_annotator("IsaacExtractRTXSensorPointCloud")
    _accumulate_returns = True


# Map annotator classes to their corresponding sensor types
annotators = {
    TestIsaacComputeRTXLidarFlatScan: ["lidar"],
    TestIsaacExtractRTXSensorPointCloudNoAccumulator: ["lidar", "radar"],
    TestIsaacExtractRTXSensorPointCloud: ["lidar"],
}


@dataclass
class SensorConfig:
    asset_path: str
    rotation_rate: float
    is_2d_lidar: bool
    expected_returns: int


# Map sensor types to a list of tuples, specifying the config, rotation rate, whether the sensor is 2D, and expected returns per frame.
# For lidars, expected returns per frame is number of emitters * returns per emitter * reportRateBaseHz * time step (s)
# time step is assumed to be 1/60s
sensor_configs = {
    "lidar": [
        SensorConfig("/Isaac/Sensors/HESAI/Hesai_XT32_SD10.usda", 10.0, False, 21333),
        # SensorConfig("/Isaac/Sensors/NVIDIA/Debug_Rotary.usda", 10.0, True, 7), # TODO (adevalla): ISIM-3547
        SensorConfig(
            "/Isaac/Sensors/NVIDIA/Example_Rotary_2D.usda", 10.0, False, 533
        ),  # Despite the name, this config's emitter is at elevation -2 degrees, so it won't trigger flatscan
        # SensorConfig("/Isaac/Sensors/NVIDIA/Example_Rotary_BEAMS.usda", 10.0, False, 153600), # TODO (adevalla): ISIM-3548
        SensorConfig("/Isaac/Sensors/NVIDIA/Example_Rotary.usda", 10.0, False, 153600),
        SensorConfig("/Isaac/Sensors/NVIDIA/Simple_Example_Solid_State.usda", 10.0, False, 12),
        SensorConfig("/Isaac/Sensors/Ouster/OS0/OS0_REV6_128ch10hz1024res.usda", 10.0, False, 43690),
        SensorConfig("/Isaac/Sensors/Ouster/OS0/OS0_REV6_128ch10hz2048res.usda", 10.0, False, 87380),
        SensorConfig("/Isaac/Sensors/Ouster/OS0/OS0_REV6_128ch10hz512res.usda", 10.0, False, 21845),
        SensorConfig("/Isaac/Sensors/Ouster/OS0/OS0_REV6_128ch20hz1024res.usda", 20.0, False, 87380),
        SensorConfig("/Isaac/Sensors/Ouster/OS0/OS0_REV6_128ch20hz512res.usda", 20.0, False, 43690),
        SensorConfig("/Isaac/Sensors/Ouster/OS0/OS0_REV7_128ch10hz1024res.usda", 10.0, False, 43690),
        SensorConfig("/Isaac/Sensors/Ouster/OS0/OS0_REV7_128ch10hz2048res.usda", 10.0, False, 87380),
        SensorConfig("/Isaac/Sensors/Ouster/OS0/OS0_REV7_128ch10hz512res.usda", 10.0, False, 21845),
        SensorConfig("/Isaac/Sensors/Ouster/OS0/OS0_REV7_128ch20hz1024res.usda", 20.0, False, 87380),
        SensorConfig("/Isaac/Sensors/Ouster/OS0/OS0_REV7_128ch20hz512res.usda", 20.0, False, 43690),
        SensorConfig("/Isaac/Sensors/Ouster/OS1/OS1_REV6_128ch10hz1024res.usda", 10.0, False, 43690),
        SensorConfig("/Isaac/Sensors/Ouster/OS1/OS1_REV6_128ch10hz2048res.usda", 10.0, False, 87380),
        SensorConfig("/Isaac/Sensors/Ouster/OS1/OS1_REV6_128ch10hz512res.usda", 10.0, False, 21845),
        SensorConfig("/Isaac/Sensors/Ouster/OS1/OS1_REV6_128ch20hz1024res.usda", 20.0, False, 87380),
        SensorConfig("/Isaac/Sensors/Ouster/OS1/OS1_REV6_128ch20hz512res.usda", 20.0, False, 43690),
        SensorConfig("/Isaac/Sensors/Ouster/OS1/OS1_REV6_32ch10hz1024res.usda", 10.0, False, 43690),
        SensorConfig("/Isaac/Sensors/Ouster/OS1/OS1_REV6_32ch10hz2048res.usda", 10.0, False, 87380),
        SensorConfig("/Isaac/Sensors/Ouster/OS1/OS1_REV6_32ch10hz512res.usda", 10.0, False, 21845),
        SensorConfig("/Isaac/Sensors/Ouster/OS1/OS1_REV6_32ch20hz1024res.usda", 20.0, False, 87380),
        SensorConfig("/Isaac/Sensors/Ouster/OS1/OS1_REV6_32ch20hz512res.usda", 20.0, False, 43690),
        SensorConfig("/Isaac/Sensors/Ouster/OS1/OS1_REV7_128ch10hz1024res.usda", 10.0, False, 43690),
        SensorConfig("/Isaac/Sensors/Ouster/OS1/OS1_REV7_128ch10hz2048res.usda", 10.0, False, 87380),
        SensorConfig("/Isaac/Sensors/Ouster/OS1/OS1_REV7_128ch10hz512res.usda", 10.0, False, 21845),
        SensorConfig("/Isaac/Sensors/Ouster/OS1/OS1_REV7_128ch20hz1024res.usda", 20.0, False, 87380),
        SensorConfig("/Isaac/Sensors/Ouster/OS1/OS1_REV7_128ch20hz512res.usda", 20.0, False, 43690),
        SensorConfig("/Isaac/Sensors/Ouster/OS2/OS2_REV6_128ch10hz1024res.usda", 10.0, False, 43690),
        SensorConfig("/Isaac/Sensors/Ouster/OS2/OS2_REV6_128ch10hz2048res.usda", 10.0, False, 87380),
        SensorConfig("/Isaac/Sensors/Ouster/OS2/OS2_REV6_128ch10hz512res.usda", 10.0, False, 21845),
        SensorConfig("/Isaac/Sensors/Ouster/OS2/OS2_REV6_128ch20hz1024res.usda", 20.0, False, 87380),
        SensorConfig("/Isaac/Sensors/Ouster/OS2/OS2_REV6_128ch20hz512res.usda", 20.0, False, 43690),
        SensorConfig("/Isaac/Sensors/Ouster/OS2/OS2_REV7_128ch10hz1024res.usda", 10.0, False, 43690),
        SensorConfig("/Isaac/Sensors/Ouster/OS2/OS2_REV7_128ch10hz2048res.usda", 10.0, False, 87380),
        SensorConfig("/Isaac/Sensors/Ouster/OS2/OS2_REV7_128ch10hz512res.usda", 10.0, False, 21845),
        SensorConfig("/Isaac/Sensors/Ouster/OS2/OS2_REV7_128ch20hz1024res.usda", 20.0, False, 87380),
        SensorConfig("/Isaac/Sensors/Ouster/OS2/OS2_REV7_128ch20hz512res.usda", 20.0, False, 43690),
        SensorConfig("/Isaac/Sensors/SICK/SICK_microscan3_ABAZ90ZA1P01.usda", 20.0, True, 917),
        SensorConfig("/Isaac/Sensors/SICK/SICK_multiScan136.usda", 20.0, False, 3600),
        SensorConfig("/Isaac/Sensors/SICK/SICK_multiScan165.usda", 20.0, False, 3840),
        SensorConfig("/Isaac/Sensors/SICK/SICK_picoScan150.usda", 20.0, True, 920),
        SensorConfig("/Isaac/Sensors/SICK/SICK_tim781.usda", 10.0, True, 203),
        SensorConfig("/Isaac/Sensors/Slamtec/RPLIDAR_S2E.usda", 10.0, True, 533),
        SensorConfig("/Isaac/Sensors/Velodyne/vls-128/Velodyne_VLS128.usda", 10.0, False, 80047),
        SensorConfig("/Isaac/Sensors/ZVISION/ZVISION_ML30S.usda", 10.0, False, 17067),
        SensorConfig("/Isaac/Sensors/ZVISION/ZVISION_MLXS.usda", 10.0, False, 36000),
    ],
    "radar": [],
}


def _create_test_for_annotator(
    sensor_type: Literal["lidar", "radar"] = "lidar",
    prim_type: Literal["sensor", "camera"] = "sensor",
    config: str = None,
    data_source: Literal["cpu", "gpu"] = "cpu",
    rotation_rate: float = 10.0,
    is_2d_lidar: bool = False,
    expected_returns: int = -1,
):
    """_summary_

    Args:
        sensor_type (Literal[&quot;lidar&quot;, &quot;radar&quot;], optional): _description_. Defaults to "lidar".
        prim_type (Literal[&quot;sensor&quot;, &quot;camera&quot;], optional): _description_. Defaults to "sensor".
        config (str, optional): _description_. Defaults to None.
        data_source (Literal[&quot;cpu&quot;, &quot;gpu&quot;], optional): _description_. Defaults to "cpu".
        rotation_rate (int, optional): _description_. Defaults to 5.
    """

    async def test_function(self):

        # # Set the data source setting
        # carb.settings.get_settings().set_bool(f"/app/sensors/nv/{sensor_type}/outputBufferOnGPU", data_source == "gpu")

        # Create sensor prim
        kwargs = {
            "path": f"/{sensor_type}",
            "parent": None,
            "translation": Gf.Vec3d(0.0, 0.0, 0.0),
            "orientation": Gf.Quatd(1.0, 0.0, 0.0, 0.0),
            "config": config,
            "force_camera_prim": prim_type == "camera",
        }

        if prim_type == "sensor":
            expected_prim_type = f"Omni{sensor_type.capitalize()}"
        else:
            expected_prim_type = "Camera"

        _, self.sensor = omni.kit.commands.execute(f"IsaacSensorCreateRtx{sensor_type.capitalize()}", **kwargs)
        self.assertIsNotNone(self.sensor)

        # Create render product and attach to sensor
        self.hydra_texture = rep.create.render_product(
            self.sensor.GetPath(),
            [32, 32],
            name="RtxSensorRenderProduct",
            render_vars=["GenericModelOutput", "RtxSensorMetadata"],
        )
        # Attach annotator to render product
        self._annotator.attach([self.hydra_texture.path])

        # Define some convenient test parameters
        self._is_2d_lidar = is_2d_lidar
        self._expected_returns = expected_returns
        self._num_frames_for_test = (int(60.0 / rotation_rate) if self._accumulate_returns else 1) + NUM_EXTRA_FRAMES
        carb.log_warn("Rendering {} frames for test.".format(self._num_frames_for_test))

        # Render to get annotator result
        await self.my_world.reset_async()
        self._timeline.play()
        await omni.syntheticdata.sensors.next_render_simulation_async(
            self.hydra_texture.path, self._num_frames_for_test
        )
        self._timeline.stop()

        # Call the main test method
        self._annotator_data = self._annotator.get_data()
        await self._test_annotator_result()

    return test_function


# Based on maps above, dynamically generate test methods for each annotator
for test_class in annotators:
    for sensor_type in annotators[test_class]:
        for sensor_config in sensor_configs[sensor_type]:
            profile_name = os.path.basename(sensor_config.asset_path).split(".")[0]
            for data_source in ["cpu"]:
                # for data_source in ["cpu", "gpu"]: # TODO (adevalla): GPU fails - ISIM-1994
                for prim_type in ["sensor", "camera"]:
                    # Create test function using sensor prim
                    test_func = _create_test_for_annotator(
                        sensor_type=sensor_type,
                        prim_type=prim_type,
                        config=profile_name,
                        data_source=data_source,
                        rotation_rate=sensor_config.rotation_rate,
                        is_2d_lidar=sensor_config.is_2d_lidar,
                        expected_returns=sensor_config.expected_returns,
                    )
                    # Set proper function name and docstring
                    config_for_doc = sensor_config.asset_path
                    if config_for_doc.endswith(".usda"):
                        config_for_doc = os.path.basename(config_for_doc)[:-5]
                    test_name = f"{sensor_type}_{prim_type}_{config_for_doc}_{data_source}"
                    test_func.__name__ = f"test_{test_name}"
                    test_func.__doc__ = f"Test {test_class.__name__} annotator results using {sensor_type} as {prim_type} prim, with config {config_for_doc} and data on {data_source.upper()}."

                    setattr(test_class, test_func.__name__, test_func)
