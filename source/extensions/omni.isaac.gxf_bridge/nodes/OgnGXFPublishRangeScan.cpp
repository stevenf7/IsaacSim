// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "gems/composite/composite_from_tensor.hpp"
#include "gems/range_scan/range_scan_types.hpp"
#include "gxf/std/tensor.hpp"

#include <plugins/Core/GxfNode.h>

#include <OgnGXFPublishRangeScanDatabase.h>
using namespace omni::isaac::gxf_bridge;

class OgnGXFPublishRangeScan : public GxfNode
{
public:
    static bool compute(OgnGXFPublishRangeScanDatabase& db)
    {
        auto& state = db.internalState<OgnGXFPublishRangeScan>();
        if (!state.getGxfContext())
        {
            if (state.setGxfContext(db.inputs.context()) != GXF_SUCCESS)
            {
                return false;
            }

            return true;
        }

        size_t numBeams = db.inputs.numCols() * db.inputs.numRows();

        auto maybe_message = nvidia::isaac::CreateRangeScanMessage(state.getGxfContext(), state.mAllocator, numBeams);
        auto message = std::move(maybe_message.value());
        message.timestamp->pubtime = static_cast<int64_t>(db.inputs.timeStamp() * 1e9);
        message.timestamp->acqtime = static_cast<int64_t>(db.inputs.timeStamp() * 1e9);
        message.pose_frame_uid->uid =
            state.mAtlas->pose_tree().findFrame(std::string(db.inputs.poseFrame()).c_str()).value();

        const auto horizontalResolutionRad = db.inputs.horizontalResolution() * M_PI / 180.0f;
        const auto verticalResolutionRad = db.inputs.verticalResolution() * M_PI / 180.0f;

        for (int i = 0, ray_idx = 0; i < db.inputs.numCols(); i++)
        {
            for (int j = 0; j < db.inputs.numRows(); j++, ray_idx++)
            {
                auto maybe_beam =
                    nvidia::isaac::CompositeFromTensor<nvidia::isaac::RangeScanView<float>>(message.beams.slice(ray_idx));
                if (!maybe_beam)
                {
                    CARB_LOG_ERROR("could not create RangeScanView for ray %d, %d", ray_idx, maybe_message.error());
                    return false;
                }
                nvidia::isaac::RangeScanView<float>& beam = maybe_beam.value();
                // TODO: fill this from spinning lidar model
                beam.relative_time() = 0.0;
                beam.horizontal_angle() = db.inputs.azimuthRange()[0] + i * horizontalResolutionRad;
                beam.vertical_angle() = -db.inputs.zenithRange()[0] + j * verticalResolutionRad;
                beam.range() = db.inputs.linearDepthData()[ray_idx];
                beam.intensity() = db.inputs.intensitiesData()[ray_idx];
            }
        }

        // Fill in meta data
        message.info->delta_time = 0.0;
        message.info->invalid_range = 0.0;
        message.info->out_of_range = static_cast<double>(db.inputs.depthRange()[1]);

        state.publish(db.inputs.outputEntity(), db.inputs.outputComponent(), std::move(message.entity));
        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return true;
    }

private:
    uint64_t schema_uid_;
};

REGISTER_OGN_NODE()
