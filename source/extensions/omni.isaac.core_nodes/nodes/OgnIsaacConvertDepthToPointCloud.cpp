// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "OgnIsaacConvertDepthToPointCloudDatabase.h"

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
extern "C" void depthToPCLOgn(float3* dest,
                              const cudaTextureObject_t src,
                              const int width,
                              const int height,
                              const float fx,
                              const float fy,
                              const float cx,
                              const float cy);

class OgnIsaacConvertDepthToPointCloud
{

public:
    static bool compute(OgnIsaacConvertDepthToPointCloudDatabase& db)
    {
        if ((carb::graphics::Format)db.inputs.format() != carb::graphics::Format::eR32_SFLOAT)
        {
            db.logError("Input data must have texture format R32_SFLOAT");
            return false;
        }

        auto& height = db.inputs.height();
        auto& width = db.inputs.width();

        auto& state = db.internalState<OgnIsaacConvertDepthToPointCloud>();

        float fx, fy, cx, cy;

        fx = width * db.inputs.focalLength() / db.inputs.horizontalAperture();
        fy = height * db.inputs.focalLength() / db.inputs.verticalAperture();
        cx = width * 0.5f;
        cy = height * 0.5f;
        {
            isaac::utils::ScopedDevice(db.inputs.cudaDeviceIndex());
            uint64_t handle = db.inputs.dataPtr();
            isaac::utils::ScopedCudaTextureObject srcTexObj(reinterpret_cast<cudaMipmappedArray_t>(handle), 0);
            state.mBuffer.resize(db.inputs.width() * db.inputs.height());
            depthToPCLOgn(state.mBuffer.data(), srcTexObj, width, height, fx, fy, cx, cy);
        }

        db.outputs.dataPtr() = reinterpret_cast<uint64_t>(state.mBuffer.data());
        db.outputs.cudaDeviceIndex() = db.inputs.cudaDeviceIndex();
        db.outputs.bufferSize() = static_cast<uint32_t>(state.mBuffer.sizeInBytes());
        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return true;
    }

private:
    isaac::utils::DeviceBufferBase<float3> mBuffer;
};
REGISTER_OGN_NODE()
}
}
}
