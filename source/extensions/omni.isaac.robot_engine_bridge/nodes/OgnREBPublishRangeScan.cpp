// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// #include "ros/ros.h"

#include <omni/isaac/robot_engine_bridge/RebNode.h>

#include <OgnREBPublishRangeScanDatabase.h>
using namespace omni::isaac::robot_engine_bridge;

class OgnREBPublishRangeScan : public RebNode
{
public:
    static bool compute(OgnREBPublishRangeScanDatabase& db)
    {
        auto& state = db.internalState<OgnREBPublishRangeScan>();
        if (!state.initializeHandles())
        {
            return false;
        }
        state.updateTimestamp(db.inputs.timeStamp(), db.inputs.timeOffset());

        IsaacMessage<isaac_message::RangeScan> scanMessage;

        auto scanMessageProto = scanMessage.initProto();

        int numBeams = db.inputs.numCols() * db.inputs.numRows();

        // Initialize the ranges tensor
        auto rangesTensor = scanMessageProto.initRanges();
        rangesTensor.setElementType(ElementType::UINT16);
        rangesTensor.initSizes(2);
        rangesTensor.setSizes({ db.inputs.numCols(), db.inputs.numRows() });
        rangesTensor.setScanlineStride(0);
        rangesTensor.setDataBufferIndex(0);

        // Initialize the intensities tensor
        auto intensities = scanMessageProto.initIntensities();
        intensities.setElementType(ElementType::UINT8);
        intensities.initSizes(1);
        intensities.setSizes({ 0 });
        intensities.setScanlineStride(0);
        intensities.setDataBufferIndex(1);

        state.theta.resize(db.inputs.numCols());
        state.phi.resize(db.inputs.numRows());
        state.depth.resize(numBeams);
        for (int col = 0; col < db.inputs.numCols(); col++)
            state.theta[col] =
                float((db.inputs.azimuthRange()[0] + col * db.inputs.horizontalResolution()) * M_PI / 180.0f);

        for (int row = 0; row < db.inputs.numRows(); row++)
            state.phi[row] = float((db.inputs.zenithRange()[0] + row * db.inputs.verticalResolution()) * M_PI / 180.0f);

        for (int beam = 0; beam < numBeams; beam++)
        {
            state.depth[beam] =
                static_cast<uint16_t>((db.inputs.linearDepthData()[beam]) * 1.0 / db.inputs.depthRange()[1] * 65535.0f);
        }

        scanMessageProto.setTheta(kj::ArrayPtr<const float>(state.theta.data(), state.theta.data() + db.inputs.numCols()));
        scanMessageProto.setPhi(kj::ArrayPtr<const float>(state.phi.data(), state.phi.data() + db.inputs.numCols()));

        scanMessageProto.setRangeDenormalizer(db.inputs.depthRange()[1]);
        scanMessageProto.setIntensityDenormalizer(1.0f);
        scanMessageProto.setDeltaTime(0);
        scanMessageProto.setInvalidRangeThreshold(0.0);
        scanMessageProto.setOutOfRangeThreshold(db.inputs.depthRange()[1]);

        std::vector<std::unique_ptr<IsaacBuffer>> buffers(1);
        buffers[0] = std::make_unique<IsaacHostBuffer>(numBeams * sizeof(uint16_t));
        std::memcpy(buffers[0]->data(), state.depth.data(), numBeams * sizeof(uint16_t));
        state.publish(db.inputs.outputComponent(), db.inputs.outputChannel(), scanMessage, buffers);

        return true;
    }

private:
    std::vector<float> theta;
    std::vector<float> phi;
    std::vector<uint16_t> depth;
};

REGISTER_OGN_NODE()
