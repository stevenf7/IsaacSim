// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <UsdPCH.h>
// clang-format on

#include <omni/isaac/utils/BaseResetNode.h>

#include <OgnIsaacReadRTXRawDatabase.h>

namespace omni
{
namespace isaac
{
namespace core_nodes
{

class OgnIsaacReadRTXRaw : public BaseResetNode
{

public:
    static bool compute(OgnIsaacReadRTXRawDatabase& db)
    {

        CARB_PROFILE_ZONE(0, "Read RTX Raw");

        const uint8_t* input = db.inputs.data().data();

        db.outputs.cpuPointer() = reinterpret_cast<uint64_t>(input);
        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return true;
    }

    virtual void reset()
    {
    }
};

REGISTER_OGN_NODE()
} // core_nodes
} // isaac
} // omni
