# Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import ctypes
import sys

import carb
import numpy as np
from omni.syntheticdata._syntheticdata import acquire_syntheticdata_interface


def object_id_to_prim_path(object_id):
    """Given an ObjectId get a Prim Path

    Args:
        object_id (int): object id, like from a RTX sensor return

    Returns:
        prim path string
    """
    return acquire_syntheticdata_interface().get_uri_from_instance_segmentation_id(int(object_id))


class OgnIsaacPrintRTXSensorInfo:
    """
    Print raw RTX sensor data to console. Example of using omni.sensors Python bindings in OmniGraph node.
    """

    @staticmethod
    def compute(db) -> bool:
        """read a pointer and print data from it assuming it is Rtx"""
        if not db.inputs.dataPtr:
            carb.log_warn("invalid data input to OgnIsaacPrintRTXSensorInfo")
            return True

        import omni.sensors.nv.common.bindings._common as common

        # Reach 28 bytes into the GMO data buffer using the pointer address
        size_buffer = (ctypes.c_char * 28).from_address(db.inputs.dataPtr)
        # Resolve bytes 16-23 as a uint64, corresponding to GMO size_in_bytes field
        gmo_size = int(np.frombuffer((size_buffer[16:24]), np.uint64)[0])
        # Use size_in_bytes field to get full GMO buffer
        buffer = (ctypes.c_char * gmo_size).from_address(db.inputs.dataPtr)
        # Retrieve GMO data from buffer as struct with well-defined fields
        gmo_data = common.getModelOutputFromBuffer(buffer)

        print("-------------------- NEW FRAME ------------------------------------------")
        print("-------------------- gmo:")
        print(f"frameId:     {gmo_data.frameId}")
        print(f"timestampNs: {gmo_data.timestampNs}")
        print(f"numElements: {gmo_data.numElements}")
        print(f"auxType: {gmo_data.auxType}")
        if gmo_data.numElements > 0:
            print(f"Return 0:")
            print(f"    timeOffsetNs: {gmo_data.timeOffSetNs[0]}")
            print(f"    azimuth:      {gmo_data.x[0]}")
            print(f"    elevation:    {gmo_data.y[0]}")
            print(f"    range:        {gmo_data.z[0]}")
            print(f"    intensity:    {gmo_data.scalar[0]}")
            print(f"Return {gmo_data.numElements - 1}:")
            print(f"    timeOffsetNs: {gmo_data.timeOffSetNs[gmo_data.numElements - 1]}")
            print(f"    azimuth:      {gmo_data.x[gmo_data.numElements - 1]}")
            print(f"    elevation:    {gmo_data.y[gmo_data.numElements - 1]}")
            print(f"    range:        {gmo_data.z[gmo_data.numElements - 1]}")
            print(f"    intensity:    {gmo_data.scalar[gmo_data.numElements - 1]}")

        # NOTE: Material mapping only valid for Lidar data currently
        if gmo_data.modality == common.Modality.LIDAR and gmo_data.aux_type == common.AuxType.FULL:
            print(f"Prim <-> Material mapping:")
            material_mapping = {}
            for i in range(gmo_data.numElements):
                objId = gmo_data.objId[i]
                matId = gmo_data.matId[i]
                if gmo_data.z[i] > 0.0 and gmo_data.scalar[i] > 0.0:
                    if objId not in material_mapping:
                        material_mapping[objId] = matId

            for obj in material_mapping:
                prim_path = object_id_to_prim_path(obj)
                print(f"objectId {obj} with prim path {prim_path} has material ID {material_mapping[obj]}.")
        return True
