// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "OgnIsaacConvertRGBAToRGBDatabase.h"

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
extern "C" void rgbaToRgbOgn(uint8_t** dest, const uint8_t** src, const int width, const int height, const int srcStride);


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
        db.outputs.data.resize(db.inputs.width() * db.inputs.height() * 3);

        rgbaToRgbOgn((uint8_t**)db.outputs.data(), (const uint8_t**)db.inputs.data(), db.inputs.width(),
                     db.inputs.height(), db.inputs.width() * 4);
        db.outputs.width() = db.inputs.width();
        db.outputs.height() = db.inputs.height();
        db.outputs.encoding() = db.stringToToken("rgb8");
        db.outputs.bufferSize() = static_cast<uint32_t>(db.outputs.data.size());
        db.outputs.swhFrameNumber() = db.inputs.swhFrameNumber();
        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return true;
    }
};
REGISTER_OGN_NODE()
}
}
}
