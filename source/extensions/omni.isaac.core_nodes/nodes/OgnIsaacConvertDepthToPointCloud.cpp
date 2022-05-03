// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
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

#include <cmath>
#include <string>

namespace omni
{
namespace isaac
{
namespace core_nodes
{
extern "C" void depthToPCLOgn(GfVec3f** dest,
                              const uint8_t** src,
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

        db.outputs.pointCloudData.resize(db.inputs.data.size() / sizeof(float));

        float fx, fy, cx, cy;

        fx = width * db.inputs.focalLength() / db.inputs.horizontalAperture();
        fy = height * db.inputs.focalLength() / db.inputs.verticalAperture();
        cx = width * 0.5f;
        cy = height * 0.5f;

        depthToPCLOgn(
            (GfVec3f**)db.outputs.pointCloudData(), (const uint8_t**)db.inputs.data(), width, height, fx, fy, cx, cy);

        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return true;
    }
};
REGISTER_OGN_NODE()
}
}
}
