# Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import ctypes

import carb
from omni.syntheticdata._syntheticdata import acquire_syntheticdata_interface


def object_id_to_prim_path(object_id):
    """Given an ObjectId get a Prim Path

    Args:
        object_id (int): object id, like form a RTX Lidar return

    Returns:
        prim path string
    """
    return acquire_syntheticdata_interface().get_uri_from_instance_segmentation_id(object_id)


class sensorPose(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        # world space translation. [X, Y, Z] in m (trace begin)
        ("posM", ctypes.c_float * 3),
        # world space rotation. [X, Y, Z, W] quaternion (trace begin)
        ("orientation", ctypes.c_float * 4),
    ]


class lidarAsyncParameter(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("numTicks", ctypes.c_uint32),  # number of ticks (sensor positions) in this trace data
        ("scanFrequency", ctypes.c_float),  # ensor frequency in hz
        ("ticksPerScan", ctypes.c_uint32),  # number of ticks of one full scan of the sensor
        (
            "maxSizeBuffer",
            ctypes.c_size_t,
        ),  # maximum possible size of the lidar trace data in bytes (can be used for initialization)
        ("currentSizeBuffer", ctypes.c_size_t),  # current size of the lidar trace data
        ("numChannels", ctypes.c_uint32),  # current size of the lidar trace data
        ("numEchos", ctypes.c_uint8),  # number of echos per detector/laser
        ("padding", ctypes.c_uint8 * 7),
        ("startTimeNs", ctypes.c_uint64),  # start time of the trace data
        ("deltaTimeNs", ctypes.c_uint64),  # delta time of the trace data
        (
            "scanStartTimeNs",
            ctypes.c_uint64,
        ),  # start time of the corresponding scan (i.e. full rotation of a spinning lidar)
        ("startTick", ctypes.c_uint32),  # start tick of this frame/trace
        ("frameStart", sensorPose),  # sensor transformation at frame start
        ("frameEnd", sensorPose),  # sensor transformation at frame end
    ]


def params2string(params):
    print_string = f"numTicks {params.numTicks}, scanFrequency {params.scanFrequency}, ticksPerScan {params.ticksPerScan}, maxSizeBuffer {params.maxSizeBuffer}, currentSizeBuffer {params.currentSizeBuffer}, numChannels {params.numChannels}, numEchos {params.numEchos}, startTimeNs {params.startTimeNs}, deltaTimeNs {params.deltaTimeNs}, scanStartTimeNs {params.scanStartTimeNs}, startTick {params.startTick}, frameStart.posM {params.frameStart.posM[0]}, {params.frameStart.posM[1]}, {params.frameStart.posM[2]}, frameStart.orientation {params.frameStart.orientation[0]}, {params.frameStart.orientation[1]}, {params.frameStart.orientation[2]}, {params.frameStart.orientation[3]}, frameEnd.posM {params.frameEnd.posM[0]}, {params.frameEnd.posM[1]}, {params.frameEnd.posM[2]}, frameEnd.orientation {params.frameEnd.orientation[0]}, {params.frameEnd.orientation[1]}, {params.frameEnd.orientation[2]}, {params.frameEnd.orientation[3]}"
    return print_string


class lidarReturn(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("azimuth", ctypes.c_float),
        ("elevation", ctypes.c_float),
        ("distance", ctypes.c_float),
        ("intensity", ctypes.c_float),
        ("velocity", ctypes.c_float * 3),
        ("hitPointNormal", ctypes.c_float * 3),
        ("deltaTime", ctypes.c_uint32),
        ("emitterId", ctypes.c_uint32),
        ("beamId", ctypes.c_uint32),
        ("materialId", ctypes.c_uint32),
        ("objectId", ctypes.c_uint32),
    ]


class lidarReturns(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("azimuths", ctypes.POINTER(ctypes.c_float)),  # azimuth in deg [-180,180]
        ("elevations", ctypes.POINTER(ctypes.c_float)),  # elevation in deg [-90, 90]
        ("distances", ctypes.POINTER(ctypes.c_float)),  # distance in m
        ("intensities", ctypes.POINTER(ctypes.c_float)),  # intensity [0,1]
        ("velocities", ctypes.POINTER(ctypes.c_float * 3)),  # velocity at hit point in sensor coordinates [m/s]
        ("hitPointNormals", ctypes.POINTER(ctypes.c_float * 3)),  # normal at hit point
        ("deltaTimes", ctypes.POINTER(ctypes.c_uint32)),  # deltatime in ns from the head (relative to tick time)
        ("emitterIds", ctypes.POINTER(ctypes.c_uint32)),  # beam emitter id
        ("beamIds", ctypes.POINTER(ctypes.c_uint32)),  # beam/laser detector id
        ("materialIds", ctypes.POINTER(ctypes.c_uint32)),  # hit point material id
        ("objectIds", ctypes.POINTER(ctypes.c_uint32)),  # hit point object id
    ]


def fillReturns(returns_p, n):
    returns = lidarReturns()
    ptr = returns_p
    returns.azimuths = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_float))
    ptr = ptr + ctypes.sizeof(ctypes.c_float) * n
    returns.elevations = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_float))
    ptr = ptr + ctypes.sizeof(ctypes.c_float) * n
    returns.distances = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_float))
    ptr = ptr + ctypes.sizeof(ctypes.c_float) * n
    returns.intensities = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_float))
    ptr = ptr + ctypes.sizeof(ctypes.c_float) * n
    returns.velocities = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_float * 3))
    ptr = ptr + ctypes.sizeof(ctypes.c_float * 3) * n
    returns.hitPointNormals = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_float * 3))
    ptr = ptr + ctypes.sizeof(ctypes.c_float * 3) * n
    returns.deltaTimes = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_uint32))
    ptr = ptr + ctypes.sizeof(ctypes.c_uint32) * n
    returns.emitterIds = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_uint32))
    ptr = ptr + ctypes.sizeof(ctypes.c_uint32) * n
    returns.beamIds = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_uint32))
    ptr = ptr + ctypes.sizeof(ctypes.c_uint32) * n
    returns.materialIds = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_uint32))
    ptr = ptr + ctypes.sizeof(ctypes.c_uint32) * n
    returns.objectIds = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_uint32))

    return returns


def return2string(re, i, prim):
    print_string = f"azimuth {re.azimuths[i]}, elevation {re.elevations[i]}, distance {re.distances[i]}, intensity {re.intensities[i]}, velocities ({re.velocities[i][0]}, {re.velocities[i][1]}, {re.velocities[i][2]}), hitPointNormal ({re.hitPointNormals[i][0]}, {re.hitPointNormals[i][1]}, {re.hitPointNormals[i][2]}), deltaTime {re.deltaTimes[i]}, emitterId {re.emitterIds[i]} , beamId {re.beamIds[i]}, materialId {re.materialIds[i]}, objectIds {re.objectIds[i]}, prim path {prim}"
    return print_string


class lidarTick(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("azimuth", ctypes.c_float),
        ("state", ctypes.c_uint32),
        ("timestamp", ctypes.c_uint64),
    ]


class lidarTicks(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("azimuths", ctypes.POINTER(ctypes.c_float)),  # azimuth in deg [-180,180]
        ("states", ctypes.POINTER(ctypes.c_uint32)),  # emitter state tick belongs to.
        ("timestamps", ctypes.POINTER(ctypes.c_uint64)),  # timestamp of tick
    ]


def fillTicks(ticks_p, n):
    ticks = lidarTicks()
    ptr = ticks_p
    ticks.azimuths = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_float))
    ptr = ptr + ctypes.sizeof(ctypes.c_float) * n
    ticks.states = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_uint32))
    ptr = ptr + ctypes.sizeof(ctypes.c_uint32) * n
    ticks.timestamps = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_uint64))
    return ticks


def tick2string(tick, i):
    print_string = f"tickAzimuth {tick.azimuths[i]}, state {tick.states[i]}, timestamp {tick.timestamps[i]}"
    return print_string


class OgnIsaacPrintRTXLidarInfo:
    """
    Example to read raw rtx data in python.
    """

    @staticmethod
    def compute(db) -> bool:
        """read a pointer and print data from it assuming it is Rtx"""
        if not db.inputs.dataPtr:
            carb.log_warn("invalid data input to OgnIsaacPrintRTXLidarInfo")
            return True
        # raw dataPtr params start after 36 bytes
        params_p = db.inputs.dataPtr + 36

        params = ctypes.cast(params_p, ctypes.POINTER(lidarAsyncParameter))
        nt = params.contents.numTicks
        nc = params.contents.numChannels
        ne = params.contents.numEchos
        numReturns = nt * nc * ne
        if db.inputs.testMode:
            # print a unique id for the node to see how many are running, and the number of returns for each
            print(f"Print Node ID_{id(db.inputs)} has {numReturns} returns")
            return True

        print("-------------------- NEW FRAME ------------------------------------------")
        print("-------------------- params:")
        print(params2string(params[0]))
        if nt == 0:
            return True
        ticks_p = params_p + ctypes.sizeof(lidarAsyncParameter)
        ticks = fillTicks(ticks_p, params.contents.numTicks)
        print("-------------------- first and last tick:")
        print(tick2string(ticks, 0))
        print(tick2string(ticks, nt - 1))

        # idx =  echo + channel*numEchos + tick * numEchos * numChannels
        returns_p = ticks_p + ctypes.sizeof(lidarTick) * params.contents.numTicks
        returns = fillReturns(returns_p, numReturns)
        print("-------------------- first and last return:")
        print(return2string(returns, 0, object_id_to_prim_path(returns.objectIds[0])))
        print(return2string(returns, numReturns - 1, object_id_to_prim_path(returns.objectIds[numReturns - 1])))

        objId2mats = {}
        num0dist = 0
        num0inte = 0
        maxlen = 0.0
        for t in range(nt):
            for c in range(nc):
                for e in range(ne):
                    x = c * ne + e + t * ne * nc
                    if not returns.distances[x]:
                        num0dist = num0dist + 1
                        continue
                    if not returns.intensities[x]:
                        num0inte = num0inte + 1
                        continue

                    vellen = (
                        returns.velocities[x][0] * returns.velocities[x][0]
                        + returns.velocities[x][1] * returns.velocities[x][1]
                        + returns.velocities[x][2] * returns.velocities[x][2]
                    )
                    if vellen > maxlen:
                        maxlen = vellen
                    oid = returns.objectIds[x]
                    mat = returns.materialIds[x]
                    if oid in objId2mats:
                        if not mat in objId2mats[oid]:
                            objId2mats[oid].append(mat)
                    else:
                        objId2mats[oid] = [mat]

        print(f"num 0 dist = {num0dist}")
        print(f"num 0 inte = {num0inte}")
        print(f"max vel length^2 = {maxlen}")
        for oid in objId2mats:
            print(f"{object_id_to_prim_path(oid)} has mats {objId2mats[oid]}")

        return True
