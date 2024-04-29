// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <OgnIsaacTimeSplitterDatabase.h>
#include <cstdint>
#include <cstdlib>

#define DENOMINATOR 1000000000LL


namespace omni
{
namespace isaac
{
namespace core_nodes
{

class OgnIsaacTimeSplitter
{
public:
    static bool compute(OgnIsaacTimeSplitterDatabase& db)
    {
        int32_t seconds = 0;
        uint32_t milliseconds = 0, microseconds = 0, nanoseconds = 0;

        const auto& inputTimeAttr = db.inputs.time();
        switch (inputTimeAttr.type().baseType)
        {
        case BaseDataType::eDouble:
        {
            auto inputTime = inputTimeAttr.get<double>().vectorized(1)[0];
            timeSplit(inputTime, seconds, milliseconds, microseconds, nanoseconds);
            break;
        }
        case BaseDataType::eFloat:
        {
            auto inputTime = inputTimeAttr.get<float>().vectorized(1)[0];
            timeSplit(inputTime, seconds, milliseconds, microseconds, nanoseconds);
            break;
        }
        case BaseDataType::eHalf:
        {
            auto inputTime = static_cast<float>(inputTimeAttr.get<pxr::GfHalf>().vectorized(1)[0]);
            timeSplit(inputTime, seconds, milliseconds, microseconds, nanoseconds);
            break;
        }
        case BaseDataType::eInt:
            seconds = static_cast<int32_t>(inputTimeAttr.get<int32_t>().vectorized(1)[0]);
            break;
        case BaseDataType::eInt64:
            seconds = static_cast<int32_t>(inputTimeAttr.get<int64_t>().vectorized(1)[0]);
            break;
        case BaseDataType::eUInt:
            seconds = static_cast<int32_t>(inputTimeAttr.get<uint32_t>().vectorized(1)[0]);
            break;
        case BaseDataType::eUInt64:
            seconds = static_cast<int32_t>(inputTimeAttr.get<uint64_t>().vectorized(1)[0]);
            break;
        default:
            db.logError("Failed to resolve input type (supported types: double, float, half, int, int64, uint, uint64");
            return false;
        }

        db.outputs.seconds() = seconds;
        db.outputs.milliseconds() = milliseconds;
        db.outputs.microseconds() = microseconds;
        db.outputs.nanoseconds() = nanoseconds;
        return true;
    }

private:
    static void timeSplit(
        const double& time, int32_t& seconds, uint32_t& milliseconds, uint32_t& microseconds, uint32_t& nanoseconds)
    {
        const auto result = std::div(static_cast<long long>(time * 1e9), DENOMINATOR);
        if (result.rem >= 0)
        {
            seconds = static_cast<int32_t>(result.quot);
            nanoseconds = static_cast<uint32_t>(result.rem);
        }
        else
        {
            seconds = static_cast<int32_t>(result.quot - 1);
            nanoseconds = static_cast<uint32_t>(DENOMINATOR + result.rem);
        }
        milliseconds = static_cast<uint32_t>(nanoseconds / 1000000L);
        microseconds = static_cast<uint32_t>(nanoseconds / 1000L);
    }
};

REGISTER_OGN_NODE()
} // core_nodes
} // isaac
} // omni
