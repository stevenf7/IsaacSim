// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#ifndef _WIN32
#    include <include/ipc_buffer_manager.hpp>
#endif

#include <carb/graphics/GraphicsTypes.h>
#include <carb/profiler/Profile.h>
#include <carb/tasking/ITasking.h>
#include <carb/tasking/TaskingUtils.h>

#include <include/Ros2Node.h>
#include <omni/isaac/utils/Buffer.h>
#include <omni/isaac/utils/ScopedCudaDevice.h>

#include <OgnROS2PublishImageDatabase.h>

extern "C" void textureFloatCopyToRawBuffer(cudaTextureObject_t, uint8_t*, uint32_t, uint32_t, cudaStream_t);


class OgnROS2PublishImage : public Ros2Node
{
public:
    // static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    // {
    //     auto& state = OgnROS2PublishImageDatabase::sPerInstanceState<OgnROS2PublishImage>(nodeObj, instanceId);
    // }

    static bool compute(OgnROS2PublishImageDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2PublishImage>();
        // spin once calls reset automatically if it was not successful
        const auto& nodeObj = db.abi_node();
        if (!state.spinOnce(
                std::string(nodeObj.iNode->getPrimPath(nodeObj)), db.inputs.nodeNamespace(), db.inputs.context()))
        {
            db.logError("Unable to create ROS2 node, please check that namespace is valid");
            return false;
        }

        // Publisher was not valid, create a new one
        if (!state.mPublisher)
        {
            CARB_PROFILE_ZONE(0, "setup publisher");
            // Setup ROS publisher
            const std::string& topicName = db.inputs.topicName();

            std::string fullTopicName = addTopicPrefix(state.mNamespaceName, topicName);

            if (!state.mFactory->validateTopic(fullTopicName))
            {
                db.logError("Unable to create ROS2 publisher, invalid topic name");
                return false;
            }

            state.mMessage = state.mFactory->CreateImageMessage();
            state.mNitrosBridgeMessage = state.mFactory->CreateNitrosBridgeImageMessage();
            Ros2QoSProfile qos;

            const std::string& qosProfile = db.inputs.qosProfile();
            if (qosProfile == "")
            {
                qos.depth = db.inputs.queueSize();
            }
            else
            {
                if (!jsonToRos2QoSProfile(qos, qosProfile))
                {
                    return false;
                }
            }
            state.mPublisher = state.mFactory->CreatePublisher(
                state.mNodeHandle.get(), fullTopicName.c_str(), state.mMessage->getTypeSupportHandle(), qos);

            if (state.mNitrosBridgeMessage && state.mNitrosBridgeMessage->ptr())
            {
                state.mNitrosBridgePublisher =
                    state.mFactory->CreatePublisher(state.mNodeHandle.get(), (fullTopicName + "/nitros_bridge").c_str(),
                                                    state.mNitrosBridgeMessage->getTypeSupportHandle(), qos);
            }
            else
            {
                CARB_LOG_INFO(
                    "isaac_ros_nitros_bridge_interfaces NitrosBridgeImage message type not found. The NITROS bridge publisher was not created");
            }

            state.mFrameId = db.inputs.frameId();

            return true;
        }

        bool status = state.publishImage(db);
        if (state.mNitrosBridgePublisher)
            status = state.publishNitrosBridgeImage(db) && status;
        return status;
    }


    bool publishImage(OgnROS2PublishImageDatabase& db)
    {
        CARB_PROFILE_ZONE(1, "publish image function");
        auto& state = db.perInstanceState<OgnROS2PublishImage>();
        auto tasking = carb::getCachedInterface<carb::tasking::ITasking>();

        {
            CARB_PROFILE_ZONE(1, "wait for previous publish");
            // wait for last message to publish before starting next
            state.mTasks.wait();
        }
        // Check if subscription count is 0
        if (!mPublishWithoutVerification && !state.mPublisher.get()->get_subscription_count())
        {
            return false;
        }


        state.mMessage->fillHeader(db.inputs.timeStamp(), state.mFrameId);

        if (db.inputs.width() == 0 || db.inputs.height() == 0)
        {
            db.logError("Width %d or height %d is not valid", db.inputs.width(), db.inputs.height());
            return false;
        }

        std::string encoding = db.tokenToString(db.inputs.encoding());
        state.mMessage->generateBuffer(db.inputs.height(), db.inputs.width(), encoding);
        size_t totalBytes = state.mMessage->getTotalBytes();
        void* dataPtr = state.mMessage->getDataPtr();

        if (db.inputs.cudaDeviceIndex() == -1)
        {
            CARB_PROFILE_ZONE(1, "Data on host");
            if (db.inputs.dataPtr() != 0 && totalBytes == db.inputs.bufferSize())
            {
                // Data is on host as ptr, buffer size matches
                memcpy(dataPtr, reinterpret_cast<void*>(db.inputs.dataPtr()), totalBytes);
            }
            else if (db.inputs.dataPtr() == 0 && totalBytes == db.inputs.data.size())
            {
                // data is on host as ogn data, copy from cpu
                memcpy(dataPtr, reinterpret_cast<const uint8_t*>(db.inputs.data.cpu().data()), totalBytes);
            }
            else
            {
                db.logError("image format and expected size %d bytes does not match input buffer Size of %d bytes",
                            totalBytes, db.inputs.bufferSize());
                db.logError("dataPtr null and expected size %d bytes does not match input data Size of %d bytes",
                            totalBytes, db.inputs.data.size());
                return false;
            }
            tasking->addTask(carb::tasking::Priority::eHigh, state.mTasks,
                             [&state]
                             {
                                 CARB_PROFILE_ZONE(1, "image publisher publish");
                                 state.mPublisher.get()->publish(state.mMessage->ptr());
                             });
        }
        else
        {

            // In order to get the benefits of using a separate stream, doo all of the work in a new thread
            tasking->addTask(
                carb::tasking::Priority::eHigh, state.mTasks,
                [&state, &db, totalBytes, dataPtr]
                {
                    CARB_PROFILE_ZONE(1, "Publish Image Thread");
                    omni::isaac::utils::ScopedDevice scopedDev(db.inputs.cudaDeviceIndex());


                    // if the device doesn't match and we have created a stream, destroy it
                    if (state.mStreamDevice != db.inputs.cudaDeviceIndex() && state.mStreamNotCreated == false)
                    {
                        CARB_PROFILE_ZONE(1, "Destroy stream");
                        cudaEventDestroy(state.mStop);
                        cudaStreamDestroy(state.mStream);
                        state.mStreamNotCreated = true;
                        state.mStreamDevice = -1;
                    }
                    // create a stream if it does not exist
                    if (state.mStreamNotCreated)
                    {
                        CARB_PROFILE_ZONE(1, "Create stream");
                        cudaStreamCreate(&state.mStream);
                        cudaEventCreate(&state.mStop);
                        state.mStreamNotCreated = false;
                        state.mStreamDevice = db.inputs.cudaDeviceIndex();
                    }


                    if (db.inputs.bufferSize() == 0)
                    {
                        CARB_PROFILE_ZONE(1, "data in gpu texture");


                        cudaArray_t levelArray = 0;
                        CUDA_CHECK(cudaGetMipmappedArrayLevel(
                            &levelArray, reinterpret_cast<cudaMipmappedArray_t>(db.inputs.dataPtr()), 0));
                        switch (static_cast<carb::graphics::Format>(db.inputs.format()))
                        {
                        case carb::graphics::Format::eR32_SFLOAT:
                            if (db.inputs.width() * db.inputs.height() * sizeof(float) != totalBytes)
                            {
                                CARB_LOG_ERROR("totalBytes doesn't match eR32_SFLOAT %zu %zu",
                                               db.inputs.width() * db.inputs.height() * sizeof(float), totalBytes);
                            }
                            else
                            {
                                CUDA_CHECK(cudaMemcpy2DFromArrayAsync(
                                    dataPtr, db.inputs.width() * sizeof(float), levelArray, 0, 0,
                                    db.inputs.width() * sizeof(float), db.inputs.height(), cudaMemcpyDeviceToHost,
                                    state.mStream));
                                cudaEventRecord(state.mStop, state.mStream);
                                cudaEventSynchronize(state.mStop);
                                CUDA_CHECK(cudaGetLastError());
                            }
                            break;

                        default:
                            CARB_LOG_ERROR("SdRenderVarToRawArray : input texture format (%d) is not supported.",
                                           static_cast<int>(db.inputs.format()));
                            return;
                        }
                    }
                    else
                    {
                        CARB_PROFILE_ZONE(1, "data in cuda memory");
                        CUDA_CHECK(cudaMemcpyAsync(dataPtr, reinterpret_cast<void*>(db.inputs.dataPtr()),
                                                   db.inputs.bufferSize(), cudaMemcpyDeviceToHost, state.mStream));
                        cudaEventRecord(state.mStop, state.mStream);
                        cudaEventSynchronize(state.mStop);
                    }


                    {
                        CARB_PROFILE_ZONE(1, "image publisher publish");
                        state.mPublisher.get()->publish(state.mMessage->ptr());
                    }
                });
            return true;
        }


        return true;
    }

    bool publishNitrosBridgeImage(OgnROS2PublishImageDatabase& db)
    {
#ifndef _WIN32
        CARB_PROFILE_ZONE(1, "publish nitros bridge image function");
        auto& state = db.perInstanceState<OgnROS2PublishImage>();
        auto tasking = carb::getCachedInterface<carb::tasking::ITasking>();

        {
            CARB_PROFILE_ZONE(1, "wait for previous publish");
            // wait for last message to publish before starting next
            state.mNitrosBridgeTasks.wait();
        }
        // Check if subscription count is 0
        if (!mPublishWithoutVerification && !state.mNitrosBridgePublisher.get()->get_subscription_count())
        {
            return false;
        }

        state.mNitrosBridgeMessage->fillHeader(db.inputs.timeStamp(), state.mFrameId);

        if (db.inputs.width() == 0 || db.inputs.height() == 0)
        {
            db.logError("Width %d or height %d is not valid", db.inputs.width(), db.inputs.height());
            return false;
        }

        std::string encoding = db.tokenToString(db.inputs.encoding());
        state.mNitrosBridgeMessage->generateBuffer(db.inputs.height(), db.inputs.width(), encoding);
        size_t totalBytes = state.mNitrosBridgeMessage->getTotalBytes();

        // IPC manager
        if (!state.mIPCBufferManager)
            state.mIPCBufferManager = std::make_shared<IPCBufferManager>(40, totalBytes);
        void* dataPtr = (void*)state.mIPCBufferManager->get_cur_buffer_ptr();

        // data on host
        if (db.inputs.cudaDeviceIndex() == -1)
        {
            CARB_PROFILE_ZONE(1, "Data on host");
            // data is on host as ptr, buffer size matches
            if (db.inputs.dataPtr() != 0 && totalBytes == db.inputs.bufferSize())
            {
                CUDA_CHECK(cudaMemcpy(
                    dataPtr, reinterpret_cast<const void*>(db.inputs.dataPtr()), totalBytes, cudaMemcpyHostToDevice));
            }
            // data is on host as ogn data, copy from CPU
            else if (db.inputs.dataPtr() == 0 && totalBytes == db.inputs.data.size())
            {
                CUDA_CHECK(cudaMemcpy(dataPtr, reinterpret_cast<const uint8_t*>(db.inputs.data.cpu().data()),
                                      totalBytes, cudaMemcpyHostToDevice));
            }
            else
            {
                db.logError("image format and expected size %d bytes does not match input buffer Size of %d bytes",
                            totalBytes, db.inputs.bufferSize());
                db.logError("dataPtr null and expected size %d bytes does not match input data Size of %d bytes",
                            totalBytes, db.inputs.data.size());
                return false;
            }

            state.mNitrosBridgeMessage->setData(state.mIPCBufferManager->get_cur_ipc_mem_handle());
            state.mIPCBufferManager->next();

            tasking->addTask(carb::tasking::Priority::eHigh, state.mNitrosBridgeTasks,
                             [&state]
                             {
                                 CARB_PROFILE_ZONE(1, "nitros image publisher publish");
                                 state.mNitrosBridgePublisher.get()->publish(state.mNitrosBridgeMessage->ptr());
                             });
        }
        // data on device
        else
        {
            // in order to get the benefits of using a separate stream, doo all of the work in a new thread
            tasking->addTask(
                carb::tasking::Priority::eHigh, state.mNitrosBridgeTasks,
                [&state, &db, totalBytes, dataPtr]
                {
                    CARB_PROFILE_ZONE(1, "publish nitros image thread");
                    omni::isaac::utils::ScopedDevice scopedDev(db.inputs.cudaDeviceIndex());

                    // if the device doesn't match and we have created a stream, destroy it
                    if (state.mNitrosBridgeStreamDevice != db.inputs.cudaDeviceIndex() &&
                        state.mNitrosBridgeStreamNotCreated == false)
                    {
                        CARB_PROFILE_ZONE(1, "Destroy stream");
                        cudaEventDestroy(state.mNitrosBridgeStop);
                        cudaStreamDestroy(state.mNitrosBridgeStream);
                        state.mNitrosBridgeStreamNotCreated = true;
                        state.mNitrosBridgeStreamDevice = -1;
                    }
                    // create a stream if it does not exist
                    if (state.mNitrosBridgeStreamNotCreated)
                    {
                        CARB_PROFILE_ZONE(1, "Create stream");
                        cudaStreamCreate(&state.mNitrosBridgeStream);
                        cudaEventCreate(&state.mNitrosBridgeStop);
                        state.mNitrosBridgeStreamNotCreated = false;
                        state.mNitrosBridgeStreamDevice = db.inputs.cudaDeviceIndex();
                    }

                    // data in gpu texture
                    if (db.inputs.bufferSize() == 0)
                    {
                        CARB_PROFILE_ZONE(1, "data in gpu texture");
                        cudaArray_t levelArray = 0;
                        CUDA_CHECK(cudaGetMipmappedArrayLevel(
                            &levelArray, reinterpret_cast<cudaMipmappedArray_t>(db.inputs.dataPtr()), 0));
                        switch (static_cast<carb::graphics::Format>(db.inputs.format()))
                        {
                        case carb::graphics::Format::eR32_SFLOAT:
                            if (db.inputs.width() * db.inputs.height() * sizeof(float) != totalBytes)
                            {
                                CARB_LOG_ERROR("totalBytes doesn't match eR32_SFLOAT %zu %zu",
                                               db.inputs.width() * db.inputs.height() * sizeof(float), totalBytes);
                            }
                            else
                            {
                                CUDA_CHECK(cudaMemcpy2DFromArrayAsync(
                                    dataPtr, db.inputs.width() * sizeof(float), levelArray, 0, 0,
                                    db.inputs.width() * sizeof(float), db.inputs.height(), cudaMemcpyDeviceToDevice,
                                    state.mNitrosBridgeStream));
                                CUDA_CHECK(cudaGetLastError());
                                cudaEventRecord(state.mNitrosBridgeStop, state.mNitrosBridgeStream);
                                cudaEventSynchronize(state.mNitrosBridgeStop);
                            }
                            break;
                        default:
                            CARB_LOG_ERROR("SdRenderVarToRawArray : input texture format (%d) is not supported.",
                                           static_cast<int>(db.inputs.format()));
                            return;
                        }
                    }
                    // data in CUDA memory
                    else
                    {
                        CARB_PROFILE_ZONE(1, "data in cuda memory");
                        CUDA_CHECK(cudaMemcpyAsync(dataPtr, reinterpret_cast<void*>(db.inputs.dataPtr()),
                                                   db.inputs.bufferSize(), cudaMemcpyDeviceToDevice,
                                                   state.mNitrosBridgeStream));
                        cudaEventRecord(state.mNitrosBridgeStop, state.mNitrosBridgeStream);
                        cudaEventSynchronize(state.mNitrosBridgeStop);
                    }

                    state.mNitrosBridgeMessage->setData(state.mIPCBufferManager->get_cur_ipc_mem_handle());
                    state.mIPCBufferManager->next();

                    {
                        CARB_PROFILE_ZONE(1, "nitros image publisher publish");
                        state.mNitrosBridgePublisher.get()->publish(state.mNitrosBridgeMessage->ptr());
                    }
                });
        }
#endif
        return true;
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2PublishImageDatabase::sPerInstanceState<OgnROS2PublishImage>(nodeObj, instanceId);
        state.reset();
    }

    virtual void reset()
    {
        {
            CARB_PROFILE_ZONE(1, "wait for previous publish");
            // wait for last message to publish before starting next
            mTasks.wait();
            mNitrosBridgeTasks.wait();
        }
        if (mStreamNotCreated == false)
        {
            omni::isaac::utils::ScopedDevice scopedDev(mStreamDevice);
            cudaEventDestroy(mStop);
            cudaStreamDestroy(mStream);
            mStreamDevice = -1;
            mStreamNotCreated = true;
        }
        if (mNitrosBridgeStreamNotCreated == false)
        {
            omni::isaac::utils::ScopedDevice scopedDev(mNitrosBridgeStreamDevice);
            cudaEventDestroy(mNitrosBridgeStop);
            cudaStreamDestroy(mNitrosBridgeStream);
            mNitrosBridgeStreamDevice = -1;
            mNitrosBridgeStreamNotCreated = true;
        }

#ifndef _WIN32
        mIPCBufferManager.reset();
        mIPCBufferManager = nullptr;
#endif
        mNitrosBridgePublisher.reset();
        mNitrosBridgePublisher = nullptr;

        mPublisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }

private:
    std::shared_ptr<Ros2Publisher> mPublisher = nullptr;
    std::shared_ptr<Ros2ImageMessage> mMessage = nullptr;

#ifndef _WIN32
    std::shared_ptr<IPCBufferManager> mIPCBufferManager = nullptr; // CUDA IPC memory pool manager
#endif
    std::shared_ptr<Ros2Publisher> mNitrosBridgePublisher = nullptr;
    std::shared_ptr<Ros2NitrosBridgeImageMessage> mNitrosBridgeMessage = nullptr;

    std::string mFrameId = "sim_camera";

    carb::tasking::TaskGroup mTasks;
    cudaStream_t mStream;
    cudaEvent_t mStop;
    int mStreamDevice = -1;
    bool mStreamNotCreated = true;

    carb::tasking::TaskGroup mNitrosBridgeTasks;
    cudaStream_t mNitrosBridgeStream;
    cudaEvent_t mNitrosBridgeStop;
    int mNitrosBridgeStreamDevice = -1;
    bool mNitrosBridgeStreamNotCreated = true;
};

REGISTER_OGN_NODE()
