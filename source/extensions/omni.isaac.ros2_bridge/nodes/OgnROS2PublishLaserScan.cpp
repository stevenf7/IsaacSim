// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
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


#include <include/Ros2Node.h>

#include <OgnROS2PublishLaserScanDatabase.h>


class OgnROS2PublishLaserScan : public Ros2Node
{
public:
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state = OgnROS2PublishLaserScanDatabase::sInternalState<OgnROS2PublishLaserScan>(nodeObj);
    // }

    static bool compute(OgnROS2PublishLaserScanDatabase& db)
    {
        auto& state = db.internalState<OgnROS2PublishLaserScan>();

        // spin once calls reset automatically if it was not successful
        const auto& nodeObj = db.abi_node();
        if (!state.spinOnce(
                std::string(nodeObj.iNode->getPrimPath(nodeObj)), db.inputs.nodeNamespace(), db.inputs.context()))
        {
            return false;
        }

        // Publisher was not valid, create a new one
        if (!state.mPublisher)
        {
            // Setup ROS publisher
            const std::string& topicName = db.inputs.topicName();

            std::string fullTopicName = addTopicPrefix(db.inputs.nodeNamespace(), topicName);

            if (!state.mFactory->validateTopic(fullTopicName))
            {
                return false;
            }
            state.mMessage = state.mFactory->CreateLaserScanMessage();

            state.mPublisher =
                state.mFactory->CreatePublisher(state.mNodeHandle.get(), fullTopicName.c_str(),
                                                state.mMessage->getTypeSupportHandle(), db.inputs.queueSize());
            state.mFrameId = db.inputs.frameId();


            return true;
        }

        return state.publishLidar(db);
    }


    bool publishLidar(OgnROS2PublishLaserScanDatabase& db)
    {
        CARB_PROFILE_ZONE(0, "Lidar 2D Pub");

        auto& state = db.internalState<OgnROS2PublishLaserScan>();

        // Check if subscription count is 0
        if (!state.mPublisher.get()->get_subscription_count())
        {
            return false;
        }
        size_t buffSize = db.inputs.numCols() * db.inputs.numRows();
        if (buffSize == 0)
        {
            return false;
        }
        if (db.inputs.numRows() != 1)
        {
            db.logError(
                "Number of rows must be equal to 1. High LOD not supported for LaserScan, only 2D Lidar Supported for LaserScan. Please disable Lidar High LOD setting");
            return false;
        }

        float rotationRate = db.inputs.rotationRate();

        if (!db.inputs.linearDepthData.isValid() || !db.inputs.intensitiesData.isValid())
        {
            db.logError("Buffers are invalid");
            return false;
        }

        if (db.inputs.linearDepthData.size() != db.inputs.intensitiesData.size())
        {
            db.logError("Linear Depth data and Intensities data sizes do not match");
            return false;
        }

        if (buffSize != db.inputs.linearDepthData.size())
        {
            db.logError("Lidar data with %d rows and %d columns does not match input buffer array size of %d",
                        db.inputs.numRows(), db.inputs.numCols(), db.inputs.linearDepthData.size());
            return false;
        }

        const float* rangePoints = static_cast<const float*>(db.inputs.linearDepthData().data());
        float* rangeData = (float*)malloc(sizeof(float) * buffSize);
        memcpy(rangeData, rangePoints, sizeof(float) * buffSize);

        const uint8_t* intensityPointsCpu = static_cast<const uint8_t*>(db.inputs.intensitiesData().data());
        float* intensityData = (float*)malloc(sizeof(float) * buffSize);

        for (size_t i = 0; i < buffSize; i++)
        {
            intensityData[i] = static_cast<float>(intensityPointsCpu[i]);
        }

        state.mMessage->fillData(state.mFrameId, db.inputs.timeStamp(), db.inputs.azimuthRange(), rotationRate,
                                 db.inputs.depthRange(), buffSize, rangeData, intensityData,
                                 db.inputs.horizontalResolution(), db.inputs.horizontalFov());

        state.mPublisher.get()->publish(state.mMessage->ptr());

        return true;
    }

    virtual void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS2PublishLaserScanDatabase::sInternalState<OgnROS2PublishLaserScan>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }


private:
    std::shared_ptr<Ros2Publisher> mPublisher = nullptr;
    std::shared_ptr<Ros2LaserScanMessage> mMessage = nullptr;

    std::string mFrameId = "sim_lidar";
    std::vector<float> range_data;
    std::vector<float> intensities_data;
};

REGISTER_OGN_NODE()
