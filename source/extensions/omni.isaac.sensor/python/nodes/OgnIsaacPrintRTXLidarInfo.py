# Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
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
        object_id (int): object id, like from a RTX Lidar return

    Returns:
        prim path string
    """
    return acquire_syntheticdata_interface().get_uri_from_instance_segmentation_id(int(object_id))


class float3(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("z", ctypes.c_float),
    ]


class float4(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("z", ctypes.c_float),
        ("w", ctypes.c_float),
    ]


class FrameAtTime(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("timestampNs", ctypes.c_uint64),
        ("orientation", float4),
        ("posM", float3),
        ("padding", ctypes.c_uint8 * 4),
    ]


class LidarAuxiliaryData(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("scanComplete", ctypes.c_uint32),  # Whether the scan is complete.
        ("azimuthOffset", ctypes.c_float),  # The offset to +x in radians for specific sensors.
        ("filledAuxMembers", ctypes.c_uint32),  # Which auxiliary data is filled.
        ("emitterId", ctypes.POINTER(ctypes.c_uint32)),  # The emitter ID.
        ("channelId", ctypes.POINTER(ctypes.c_uint32)),  # The channel ID.
        ("echoId", ctypes.POINTER(ctypes.c_uint8)),  # The echo ID.
        ("matId", ctypes.POINTER(ctypes.c_uint32)),  # The material ID.
        ("objId", ctypes.POINTER(ctypes.c_uint32)),  # The object ID.
        ("tickId", ctypes.POINTER(ctypes.c_uint32)),  # The tick ID.
        ("tickStates", ctypes.POINTER(ctypes.c_uint8)),  # The tick states.
        ("hitNormals", ctypes.POINTER(ctypes.c_float)),  # The hit normals.
        ("velocities", ctypes.POINTER(ctypes.c_float)),  # The velocities.
    ]


class BasicElements(ctypes.Structure):
    _fields_ = [
        ("timeOffsetNs", ctypes.POINTER(ctypes.c_int32)),  # Time offset from the start of the point cloud
        ("x", ctypes.POINTER(ctypes.c_float)),  # azimuth in degree [-180,180] or cartesian x in m
        ("y", ctypes.POINTER(ctypes.c_float)),  # elevation in degree or cartesian y in m
        ("z", ctypes.POINTER(ctypes.c_float)),  # distance in m or cartesian z in m
        ("scalar", ctypes.POINTER(ctypes.c_float)),  # sensor specific scalar
        ("flags", ctypes.POINTER(ctypes.c_uint8)),  # sensor specific flags
    ]


class GenericModelOutput(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        (
            "magicNumber",
            ctypes.c_uint32,
        ),  # A unique identifier for the output. Should reflect MAGIC_NUMBER_GMO, which is the ASCII for "NGMO".
        ("majorVersion", ctypes.c_uint32),  # The major version number of the model output.
        ("minorVersion", ctypes.c_uint32),  # The minor version number of the model output.
        ("patchVersion", ctypes.c_uint32),  # The number of elements in the array members of the model output.
        ("numElements", ctypes.c_uint32),  # The patch version number of the model output.
        (
            "frameOfReference",
            ctypes.c_uint32,
        ),  # The frame of reference for the model output. The default value is ``FrameOfReference::SENSOR``.
        ("frameId", ctypes.c_uint64),  # The model (simulation) frame ID of the model output.
        ("timestampNs", ctypes.c_uint64),  # The timestamp of the model output in nanoseconds.
        (
            "coordsType",
            ctypes.c_uint32,
        ),  # The type of coordinates used in the model output. The default value is ``CoordsType::SPHERICAL``.
        ("outputType", ctypes.c_uint32),  # The type of output. The default value is ``OutputType::POINTCLOUD``.
        (
            "modelToAppTransform",
            ctypes.c_float * 16,
        ),  # A transformation matrix that transforms from the model's coordinate system to the application's coordinate system.
        (
            "frameStart",
            FrameAtTime,
        ),  # The start frame of the model output. It transforms from the model's coordinate system to the global coordinate system at frame start time.
        (
            "frameEnd",
            FrameAtTime,
        ),  # The end frame of the model output. It transforms from the model's coordinate system to the global coordinate system at frame end time. See below for more information.
        (
            "auxType",
            ctypes.c_uint32,
        ),  # The modality specific type of auxiliary data. The default value is ``AuxType::NONE``. See below for more information.
        ("padding", ctypes.c_uint8 * 4),  # Padding to align the structure to a multiple of 8 bytes.
        ("elements", BasicElements),  # The basic elements of the model output. See below for more information.
        (
            "auxiliaryData",
            ctypes.c_void_p,
        ),  # A pointer to the auxiliary data. This may not be filled. See below for more information.
    ]


class OgnIsaacPrintRTXLidarInfo:
    """
    Example to read raw rtx data in python.
    """

    frameCount = 0

    @staticmethod
    def compute(db) -> bool:
        """read a pointer and print data from it assuming it is Rtx"""
        if not db.inputs.dataPtr:
            carb.log_warn("invalid data input to OgnIsaacPrintRTXLidarInfo")
            return True

        gmo = ctypes.cast(db.inputs.dataPtr, ctypes.POINTER(GenericModelOutput)).contents
        if gmo.magicNumber != int("4E474D4F", 16):
            # print a unique id for the node to see how many are running, and the number of returns for each
            print(f"Print Node ID_{id(db.inputs)} has invalid input")
            return True

        numElements = gmo.numElements
        if db.inputs.testMode:
            # print a unique id for the node to see how many are running, and the number of returns for each
            print(f"Print Node ID_{id(db.inputs)} has {numElements} returns")
            return True

        elemPtr = db.inputs.dataPtr + ctypes.sizeof(GenericModelOutput)
        elements = BasicElements()
        elements.timeOffsetNs = ctypes.cast(elemPtr, ctypes.POINTER(ctypes.c_int32))
        elemPtr = elemPtr + ctypes.sizeof(ctypes.c_int32) * numElements
        elements.x = ctypes.cast(elemPtr, ctypes.POINTER(ctypes.c_float))
        elemPtr = elemPtr + ctypes.sizeof(ctypes.c_float) * numElements
        elements.y = ctypes.cast(elemPtr, ctypes.POINTER(ctypes.c_float))
        elemPtr = elemPtr + ctypes.sizeof(ctypes.c_float) * numElements
        elements.z = ctypes.cast(elemPtr, ctypes.POINTER(ctypes.c_float))
        elemPtr = elemPtr + ctypes.sizeof(ctypes.c_float) * numElements
        elements.scalar = ctypes.cast(elemPtr, ctypes.POINTER(ctypes.c_float))
        elemPtr = elemPtr + ctypes.sizeof(ctypes.c_float) * numElements
        elements.flags = ctypes.cast(elemPtr, ctypes.POINTER(ctypes.c_uint8))
        elemPtr = elemPtr + ctypes.sizeof(ctypes.c_uint8) * numElements

        auxDataPtr = elemPtr
        auxData = LidarAuxiliaryData()
        auxData.scanComplete = ctypes.cast(auxDataPtr, ctypes.POINTER(ctypes.c_uint32)).contents
        auxDataPtr = auxDataPtr + ctypes.sizeof(ctypes.c_uint32)
        auxData.azimuthOffset = ctypes.cast(auxDataPtr, ctypes.POINTER(ctypes.c_float)).contents
        auxDataPtr = auxDataPtr + ctypes.sizeof(ctypes.c_float)
        auxData.filledAuxMembers = ctypes.cast(auxDataPtr, ctypes.POINTER(ctypes.c_uint32)).contents
        auxDataPtr = auxDataPtr + ctypes.sizeof(ctypes.c_uint32)
        if auxData.filledAuxMembers & (1 << 0) == (1 << 0):
            auxData.emitterId = ctypes.cast(auxDataPtr, ctypes.POINTER(ctypes.c_uint32))
            auxDataPtr = auxDataPtr + ctypes.sizeof(ctypes.c_uint32) * numElements
        if auxData.filledAuxMembers & (1 << 1) == (1 << 1):
            auxData.channelId = ctypes.cast(auxDataPtr, ctypes.POINTER(ctypes.c_uint32))
            auxDataPtr = auxDataPtr + ctypes.sizeof(ctypes.c_uint32) * numElements
        if auxData.filledAuxMembers & (1 << 2) == (1 << 2):
            auxData.echoId = ctypes.cast(auxDataPtr, ctypes.POINTER(ctypes.c_uint8))
            auxDataPtr = auxDataPtr + ctypes.sizeof(ctypes.c_uint8) * numElements
        if auxData.filledAuxMembers & (1 << 3) == (1 << 3):
            auxData.matId = ctypes.cast(auxDataPtr, ctypes.POINTER(ctypes.c_uint32))
            auxDataPtr = auxDataPtr + ctypes.sizeof(ctypes.c_uint32) * numElements
        if auxData.filledAuxMembers & (1 << 4) == (1 << 4):
            auxData.objId = ctypes.cast(auxDataPtr, ctypes.POINTER(ctypes.c_uint32))
            auxDataPtr = auxDataPtr + ctypes.sizeof(ctypes.c_uint32) * numElements
        if auxData.filledAuxMembers & (1 << 5) == (1 << 5):
            auxData.tickId = ctypes.cast(auxDataPtr, ctypes.POINTER(ctypes.c_uint32))
            auxDataPtr = auxDataPtr + ctypes.sizeof(ctypes.c_uint32) * numElements
        if auxData.filledAuxMembers & (1 << 6) == (1 << 6):
            auxData.tickStates = ctypes.cast(auxDataPtr, ctypes.POINTER(ctypes.c_uint8))
            auxDataPtr = auxDataPtr + ctypes.sizeof(ctypes.c_uint8)
        if auxData.filledAuxMembers & (1 << 7) == (1 << 7):
            auxData.hitNormals = ctypes.cast(auxDataPtr, ctypes.POINTER(ctypes.c_float))
            auxDataPtr = auxDataPtr + ctypes.sizeof(ctypes.c_float) * 3 * numElements
        if auxData.filledAuxMembers & (1 << 8) == (1 << 8):
            auxData.velocities = ctypes.cast(auxDataPtr, ctypes.POINTER(ctypes.c_float))

        print("-------------------- NEW FRAME ------------------------------------------")
        print("-------------------- gmo:")
        print(f"frameId:     {gmo.frameId}")
        print(f"timestampNs: {gmo.timestampNs}")
        print(f"numElements: {gmo.numElements}")
        print(f"auxType: {gmo.auxType}")
        print(f"auxdataFilled: {auxData.filledAuxMembers}")
        print(f"Return 0:")
        print(f"    timeOffsetNs: {elements.timeOffsetNs[0]}")
        print(f"    azimuth:      {elements.x[0]}")
        print(f"    elevation:    {elements.y[0]}")
        print(f"    range:        {elements.z[0]}")
        print(f"    intensity:    {elements.scalar[0]}")
        print(f"Return {gmo.numElements - 1}:")
        print(f"    timeOffsetNs: {elements.timeOffsetNs[gmo.numElements - 1]}")
        print(f"    azimuth:      {elements.x[gmo.numElements - 1]}")
        print(f"    elevation:    {elements.y[gmo.numElements - 1]}")
        print(f"    range:        {elements.z[gmo.numElements - 1]}")
        print(f"    intensity:    {elements.scalar[gmo.numElements - 1]}")
        print(f"Prim <-> Material mapping:")
        # Test if element is valid AND if auxiliary data contains material IDs AND if auxiliary data contains object IDs
        # not sure what this is fore
        # if (
        #    (elements.flags[i] & 1 << 6)
        #    and auxData.filledAuxMembers & (1 << 3) == (1 << 3)
        #    and auxData.filledAuxMembers & (1 << 4) == (1 << 4)
        # ):
        material_mapping = {}
        for i in range(numElements):
            objId = auxData.objId[i]
            matId = auxData.matId[i]
            if elements.z[i] > 0.0 and elements.scalar[i] > 0.0:
                if objId not in material_mapping:
                    material_mapping[objId] = matId

        # There is a bug that will cause an objId of 31 to be returned even when there is none in the scene,
        # So for now, just skip objId==31
        for obj in material_mapping:
            prim_path = object_id_to_prim_path(obj)
            print(f"objectId {obj} with prim path {prim_path} has material ID {material_mapping[obj]}.")
        return True
