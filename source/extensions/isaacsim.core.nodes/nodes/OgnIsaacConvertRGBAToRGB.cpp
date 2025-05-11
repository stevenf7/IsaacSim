// SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#include "OgnIsaacConvertRGBAToRGBDatabase.h"

#include <carb/logging/Log.h>

#include <isaacsim/core/includes/Buffer.h>
#include <isaacsim/core/includes/ScopedCudaDevice.h>

#include <cmath>
#include <string>
namespace isaacsim
{
namespace core
{
namespace nodes
{
extern "C" void rgbaToRgbOgn(uint8_t* dest, cudaTextureObject_t src, const int width, const int height, const int srcStride);


/**
 * @brief a node that converts from rgba to rgb
 *
 */
class OgnIsaacConvertRGBAToRGB
{

public:
    static bool compute(OgnIsaacConvertRGBAToRGBDatabase& db)
    {
        if (std::string(db.tokenToString(db.inputs.encoding())).compare(std::string("rgba8")) != 0)
        {
            db.logError("input data must be encoded as rgba8");
            return false;
        }
        // db.outputs.data.resize(db.inputs.width() * db.inputs.height() * 3);
        // CARB_LOG_ERROR(
        //     "BUFFER SIZE: %d %d", db.inputs.width() * db.inputs.height() * 3 * sizeof(uint8_t),
        //     db.inputs.bufferSize());
        // CARB_LOG_ERROR("FORMAT: %lu DEVICE: %d", db.inputs.format(), db.inputs.cudaDeviceIndex());
        auto& state = db.perInstanceState<OgnIsaacConvertRGBAToRGB>();

        // If the data is on host, pass the pointer along

        if (db.inputs.cudaDeviceIndex() == -1)
        {
            db.outputs.dataPtr() = db.inputs.dataPtr();
            db.outputs.bufferSize() = db.inputs.bufferSize();
        }
        else
        {
            isaacsim::core::includes::ScopedDevice scopedDev(db.inputs.cudaDeviceIndex());
            uint64_t handle = db.inputs.dataPtr();
            state.m_buffer.resize(db.inputs.width() * db.inputs.height() * 3);

            isaacsim::core::includes::ScopedCudaTextureObject srcTexObj(
                reinterpret_cast<cudaMipmappedArray_t>(handle), 0);
            rgbaToRgbOgn(state.m_buffer.data(), srcTexObj, db.inputs.width(), db.inputs.height(), db.inputs.width() * 4);
            db.outputs.dataPtr() = reinterpret_cast<uint64_t>(state.m_buffer.data());
            db.outputs.bufferSize() = static_cast<uint32_t>(state.m_buffer.sizeInBytes());
        }
        db.outputs.cudaDeviceIndex() = db.inputs.cudaDeviceIndex();
        db.outputs.width() = db.inputs.width();
        db.outputs.height() = db.inputs.height();
        db.outputs.encoding() = db.stringToToken("rgb8");
        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return true;
    }

    // static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    // {
    //     auto& state = OgnIsaacConvertRGBAToRGBDatabase::sPerInstanceState<OgnIsaacConvertRGBAToRGB>(nodeObj,
    //     instanceId);
    // }

private:
    isaacsim::core::includes::DeviceBuffer m_buffer;
};
REGISTER_OGN_NODE()
}
}
}
