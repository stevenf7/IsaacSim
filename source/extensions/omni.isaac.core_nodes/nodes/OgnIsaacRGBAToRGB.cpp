// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "OgnIsaacRGBAToRGBDatabase.h"

#include <carb/graphics/GraphicsTypes.h>
#include <carb/logging/Log.h>

#include <cmath>

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
class OgnIsaacRGBAToRGB
{

public:
    static bool compute(OgnIsaacRGBAToRGBDatabase& db)
    {
        db.outputs.data.resize(db.inputs.width() * db.inputs.height() * 3);

        rgbaToRgbOgn((uint8_t**)db.outputs.data(), (const uint8_t**)db.inputs.data(), db.inputs.width(),
                     db.inputs.height(), db.inputs.width() * 4);

        return true;
    }
};
REGISTER_OGN_NODE()
}
}
}
