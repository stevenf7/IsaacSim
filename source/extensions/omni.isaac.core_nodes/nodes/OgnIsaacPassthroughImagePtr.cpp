// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "OgnIsaacPassthroughImagePtrDatabase.h"

#include <cmath>
#include <string>

namespace omni
{
namespace isaac
{
namespace core_nodes
{

/**
 * @brief a node that passes trough pointer without changing it
 *
 */
class OgnIsaacPassthroughImagePtr
{

public:
    static bool compute(OgnIsaacPassthroughImagePtrDatabase& db)
    {
        db.outputs.dataPtr() = db.inputs.dataPtr();
        db.outputs.cudaDeviceIndex() = db.inputs.cudaDeviceIndex();
        db.outputs.width() = db.inputs.width();
        db.outputs.height() = db.inputs.height();
        db.outputs.bufferSize() = db.inputs.bufferSize();
        db.outputs.format() = db.inputs.format();
        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return true;
    }

private:
};
REGISTER_OGN_NODE()
}
}
}
