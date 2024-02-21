// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#ifdef _WIN32
#    pragma warning(push)
#    pragma warning(disable : 4996)
#endif

// clang-format off
#include <UsdPCH.h>
// clang-format on
#include "omni/isaac/utils/UsdUtilities.h"

#include <include/Ros2Node.h>
#include <omni/isaac/utils/ScopedCudaDevice.h>

#include <OgnROS2PublishPointCloudDatabase.h>


class OgnROS2PublishPointCloud : public Ros2Node
{
public:
    // static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    // {
    //     auto& state = OgnROS2PublishPointCloudDatabase::sPerInstanceState<OgnROS2PublishPointCloud>(nodeObj,
    //     instanceId);
    // }

    static bool compute(OgnROS2PublishPointCloudDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2PublishPointCloud>();

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

            state.mMessage = state.mFactory->CreatePointCloudMessage();

            state.mPublisher =
                state.mFactory->CreatePublisher(state.mNodeHandle.get(), fullTopicName.c_str(),
                                                state.mMessage->getTypeSupportHandle(), db.inputs.queueSize());

            state.mFrameId = db.inputs.frameId();

            return true;
        }

        return state.publishLidar(db);
    }

    bool publishLidar(OgnROS2PublishPointCloudDatabase& db)
    {

        CARB_PROFILE_ZONE(0, "Lidar Point Cloud Pub");

        auto& state = db.perInstanceState<OgnROS2PublishPointCloud>();

        // Check if subscription count is 0
        if (!state.mPublisher.get()->get_subscription_count())
        {
            return false;
        }
        size_t height = 1;
        uint32_t point_step = sizeof(GfVec3f);
        size_t width = 0;
        size_t row_step = 0;

        if (db.inputs.cudaDeviceIndex() == -1)
        {
            if (db.inputs.dataPtr() != 0)
            {
                width = db.inputs.bufferSize() / point_step;
                row_step = db.inputs.bufferSize();
                size_t totalBytes = row_step;
                state.mMessage->fillMetadata(mFrameId, db.inputs.timeStamp(), width, height, point_step);
                // Data is on host as ptr, buffer size matches
                memcpy(state.mMessage->getDataPtr(), reinterpret_cast<void*>(db.inputs.dataPtr()), totalBytes);
            }

            else if (db.inputs.dataPtr() == 0)
            {
                width = db.inputs.data.size();
                row_step = point_step * db.inputs.data.size();
                size_t totalBytes = row_step;
                state.mMessage->fillMetadata(mFrameId, db.inputs.timeStamp(), width, height, point_step);
                // data is on host as ogn data, copy from cpu
                memcpy(state.mMessage->getDataPtr(), reinterpret_cast<const uint8_t*>(db.inputs.data.cpu().data()),
                       totalBytes);
            }
        }
        else
        {
            if (db.inputs.dataPtr() != 0)
            {
                width = db.inputs.bufferSize() / point_step;
                row_step = db.inputs.bufferSize();
                size_t totalBytes = row_step;
                state.mMessage->fillMetadata(mFrameId, db.inputs.timeStamp(), width, height, point_step);

                omni::isaac::utils::ScopedDevice(db.inputs.cudaDeviceIndex());
                auto src = reinterpret_cast<void*>(db.inputs.dataPtr());
                CUDA_CHECK(cudaMemcpy(state.mMessage->getDataPtr(), src, db.inputs.bufferSize(), cudaMemcpyDeviceToHost));
            }
        }
        state.mPublisher.get()->publish(state.mMessage->ptr());

        return true;
    }


    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2PublishPointCloudDatabase::sPerInstanceState<OgnROS2PublishPointCloud>(nodeObj, instanceId);
        state.reset();
    }


    virtual void reset()
    {
        mPublisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }


private:
    std::shared_ptr<Ros2Publisher> mPublisher = nullptr;
    std::shared_ptr<Ros2PointCloudMessage> mMessage = nullptr;

    std::string mFrameId = "sim_lidar";
};

REGISTER_OGN_NODE()

#ifdef _WIN32
#    pragma warning(pop)
#endif
