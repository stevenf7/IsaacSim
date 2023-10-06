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

#include <OgnGXFPublishRTXRangeScanDatabase.h>
using namespace omni::isaac::gxf_bridge;

class OgnGXFPublishRTXRangeScan : public GxfNode
{
public:
    static bool compute(OgnGXFPublishRTXRangeScanDatabase& db)
    {
        auto& state = db.internalState<OgnGXFPublishRTXRangeScan>();
        if (!state.getGxfContext())
        {
            if (state.setGxfContext(db.inputs.context()) != GXF_SUCCESS)
            {
                return false;
            }

            return true;
        }

        size_t numBeams = db.inputs.numBeams();
        if (!numBeams)
        {
            return false;
        }

        auto maybe_message = nvidia::isaac::CreateRangeScanMessage(state.getGxfContext(), state.mAllocator, numBeams);
        auto message = std::move(maybe_message.value());

        // Populate message info field
        message.info->delta_time = 5.0E-5 / 32.0; // refer to hesai_constants.cpp
        message.info->invalid_range = 0.05; // hardware config value - currently tuned to Hesai XT-32, 128E3
        message.info->out_of_range = 120.0; // hardware config value - currently tuned to Hesai XT-32, 128E3
        // Set return_mode to dual return mode value.
        message.info->return_mode = nvidia::isaac::RangeScanReturnMode::kRangeScanReturnModeLastFirst;

        // Populate message frame UID
        const std::string frame_name = db.inputs.poseFrame();
        const auto maybe_frame = state.mAtlas->pose_tree().findFrame(frame_name.c_str());
        if (!maybe_frame)
        {
            db.logError("Cannot find frame %s", frame_name.c_str());
            return false;
        }
        message.pose_frame_uid->uid = maybe_frame.value();

        // Populate message beam info
        for (int b = 0; b < numBeams; b++)
        {
            auto maybe_beam =
                nvidia::isaac::CompositeFromTensor<nvidia::isaac::RangeScanView<float>>(message.beams.slice(b));
            if (!maybe_beam)
            {
                CARB_LOG_ERROR("could not create RangeScanView for ray %d.", b);
                return false;
            }
            nvidia::isaac::RangeScanView<float>& beam = maybe_beam.value();
            // Get index of tick containing current beam
            auto t = db.inputs.ticks()[b];
            // Compute time of current tick, relative to time of first tick in this partial scan (ns)
            auto timeSinceFirstTick = db.inputs.tickTimestamps()[t] - db.inputs.tickTimestamps()[0];
            // Compute beam relative time as time of beam relative to time of first tick in this partial scan (s)
            beam.relative_time() = (db.inputs.deltaTimes()[b] + timeSinceFirstTick) / 1.0e9;

            // Isaac defines horizontal angle as CCW about +Z, while the lidar model defines horizontal angle as CW
            // about +Z. Here we invert the lidar model's horizontal angle, then wrap it between [0, 2*M_PI].
            beam.horizontal_angle() = nvidia::isaac::WrapTwoPi(-nvidia::isaac::DegToRad(db.inputs.azimuths()[b]));
            beam.vertical_angle() = nvidia::isaac::DegToRad(db.inputs.elevations()[b]);

            // The lidar model returns invalid beams as having range 0. Beams with range 0 are below the invalid_range
            // specified above and are discarded by the Isaac localizer, causing the scan FOV to drop below the desired
            // threshold. By setting invalid beams from the lidar model as being out-of-range, the localizer can
            // incorporate the full FOV and perform correctly.
            auto distance_b = db.inputs.distances()[b];
            if (distance_b < 1e-5)
            {
                distance_b = message.info->out_of_range;
            }
            beam.range() = distance_b;
            beam.intensity() = db.inputs.intensities()[b];
        }

        // Set message acqtime to "hardware" acquisition time - i.e time of first lidar tick in this frame, which should
        // be time of previous message publication (render step)
        message.timestamp->acqtime = state.prevPubtime;
        // Set message pubtime to sim time at which message was generated.
        message.timestamp->pubtime = state.mClock->timestamp();
        state.prevPubtime = message.timestamp->pubtime;

        state.publish(db.inputs.outputEntity(), db.inputs.outputComponent(), std::move(message.entity));
        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return true;
    }

private:
    int64_t prevPubtime{ 0 };
};

REGISTER_OGN_NODE()
