// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "OgnIsaacConvertRGBAToRGBDatabase.h"

#include <carb/cudainterop/CudaInterop.h>
#include <carb/graphics/GraphicsTypes.h>
#include <carb/logging/Log.h>

#include <omni/isaac/utils/Buffer.h>
#include <omni/isaac/utils/ScopedCudaDevice.h>

#include <cmath>
#include <string>
namespace omni
{
namespace isaac
{
namespace core_nodes
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

        // // If the data is on host, copy to device, use default device
        // if (db.inputs.cudaDeviceIndex() == -1)
        // {
        //     state.mBuffer =
        //         isaac::utils::DeviceBuffer(db.inputs.width() * db.inputs.height() * 4, db.inputs.cudaDeviceIndex());
        //     uint64_t handle = db.inputs.dataPtr();
        //     state.mBuffer.copy(
        //         reinterpret_cast<void*>(&handle), db.inputs.width() * db.inputs.height() * 4,
        //         cudaMemcpyHostToDevice);
        //     state.inputBuffer = state.mBuffer.data();
        // }
        // else
        // {
        //     uint64_t handle = db.inputs.dataPtr();
        //     state.inputBuffer = reinterpret_cast<void*>(&handle);
        // }
        {
            isaac::utils::ScopedDevice(db.inputs.cudaDeviceIndex());
            uint64_t handle = db.inputs.dataPtr();
            state.mBuffer.resize(db.inputs.width() * db.inputs.height() * 3);

            isaac::utils::ScopedCudaTextureObject srcTexObj(reinterpret_cast<cudaMipmappedArray_t>(handle), 0);
            rgbaToRgbOgn(state.mBuffer.data(), srcTexObj, db.inputs.width(), db.inputs.height(), db.inputs.width() * 4);
        }
        db.outputs.dataPtr() = reinterpret_cast<uint64_t>(state.mBuffer.data());
        db.outputs.cudaDeviceIndex() = db.inputs.cudaDeviceIndex();
        db.outputs.width() = db.inputs.width();
        db.outputs.height() = db.inputs.height();
        db.outputs.encoding() = db.stringToToken("rgb8");
        db.outputs.bufferSize() = static_cast<uint32_t>(state.mBuffer.sizeInBytes());
        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return true;
    }

    // static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    // {
    //     auto& state = OgnIsaacConvertRGBAToRGBDatabase::sPerInstanceState<OgnIsaacConvertRGBAToRGB>(nodeObj,
    //     instanceId);
    // }

private:
    isaac::utils::DeviceBuffer mBuffer;
};
REGISTER_OGN_NODE()
}
}
}
