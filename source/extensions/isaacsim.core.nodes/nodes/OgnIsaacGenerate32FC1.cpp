// Copyright (c) 2020-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "OgnIsaacGenerate32FC1Database.h"

#include <carb/graphics/GraphicsTypes.h>
#include <carb/logging/Log.h>

#include <cmath>
#include <string>

namespace isaacsim
{
namespace core
{
namespace nodes
{

/**
 * @brief a node that converts from rgba to rgb
 *
 */
class OgnIsaacGenerate32FC1
{

public:
    static bool compute(OgnIsaacGenerate32FC1Database& db)
    {
        auto& state = db.perInstanceState<OgnIsaacGenerate32FC1>();
        size_t numElements = db.inputs.width() * db.inputs.height();
        state.m_values.resize(numElements);

        std::fill_n(state.m_values.begin(), numElements / 2, db.inputs.value());

        // Fill second hallf of array with different float value for disparity
        std::fill_n(state.m_values.begin() + numElements / 2, numElements / 2, db.inputs.value() / 2);

        size_t buffSize = numElements * sizeof(float);
        db.outputs.data.resize(buffSize);

        memcpy(db.outputs.data().data(), &state.m_values.data()[0], buffSize);

        db.outputs.width() = db.inputs.width();
        db.outputs.height() = db.inputs.height();
        db.outputs.encoding() = db.stringToToken("32FC1");

        return true;
    }

private:
    std::vector<float> m_values;
};
REGISTER_OGN_NODE()
}
}
}
