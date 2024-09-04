// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#if !defined(_WIN32) && !defined(ROS2_BACKEND_FOXY)
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

class PublishImageThreadData
{
public:
    PublishImageThreadData()
    {
    }

    void* mInputDataPtr;
    void* mOutputDataPtr;
    carb::graphics::Format mFormat;
    int mWidth;
    int mHeight;
    size_t mBufferSize;
    size_t mTotalBytes; // Should be the same as mBufferSize, need to refactor this
    int mCudaDeviceIndex;

    cudaStream_t* mStream;
    int* mStreamDevice;
    bool* mStreamNotCreated;

    std::shared_ptr<Ros2Publisher> mPublisher;
    std::shared_ptr<Ros2ImageMessage> mMessage;
};

class PublishNitrosBridgeImageThreadData
{
public:
    PublishNitrosBridgeImageThreadData()
    {
    }

    void* mInputDataPtr;
    void* mOutputDataPtr;
    carb::graphics::Format mFormat;
    int mWidth;
    int mHeight;
    size_t mBufferSize;
    size_t mTotalBytes; // Should be the same as mBufferSize, need to refactor this
    int mCudaDeviceIndex;

    cudaStream_t* mNitrosBridgeStream;
    int* mNitrosBridgeStreamDevice;
    bool* mNitrosBridgeStreamNotCreated;

#if !defined(_WIN32) && !defined(ROS2_BACKEND_FOXY)
    std::shared_ptr<IPCBufferManager> mIPCBufferManager;
#endif

    std::shared_ptr<Ros2Publisher> mNitrosBridgePublisher;
    std::shared_ptr<Ros2NitrosBridgeImageMessage> mNitrosBridgeMessage;
};


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

            // Get extension param setting for multithreading
            carb::settings::ISettings* threadSettings = carb::getCachedInterface<carb::settings::ISettings>();
            static constexpr char thread_disable[] = "/exts/omni.isaac.ros2_bridge/publish_multithreading_disabled";
            state.mMultithreadingDisabled = threadSettings->getAsBool(thread_disable);

            return true;
        }

        bool status;
        status = state.publishImage(db);
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
            if (state.mMultithreadingDisabled)
            {
                CARB_PROFILE_ZONE(1, "image publisher publish");
                state.mPublisher.get()->publish(state.mMessage->ptr());
            }
            else
            {
                tasking->addTask(carb::tasking::Priority::eHigh, state.mTasks,
                                 [&state]
                                 {
                                     CARB_PROFILE_ZONE(1, "image publisher publish");
                                     state.mPublisher.get()->publish(state.mMessage->ptr());
                                 });
            }
        }
        else
        {
            PublishImageThreadData publishImageThreadData = buildThreadData(db, state, dataPtr, totalBytes);

            if (state.mMultithreadingDisabled)
            {
                return publishImageHelper(publishImageThreadData);
            }
            else
            {
                // In order to get the benefits of using a separate stream, do the work in a new thread
                tasking->addTask(carb::tasking::Priority::eHigh, state.mTasks,
                                 [data = publishImageThreadData]() mutable { return publishImageHelper(data); });
            }
        }

        return true;
    }

    PublishImageThreadData buildThreadData(OgnROS2PublishImageDatabase& db,
                                           OgnROS2PublishImage& state,
                                           void* dataPtr,
                                           size_t totalBytes)
    {
        PublishImageThreadData threadData;

        threadData.mInputDataPtr = reinterpret_cast<void*>(db.inputs.dataPtr());
        threadData.mOutputDataPtr = dataPtr;
        threadData.mFormat = static_cast<carb::graphics::Format>(db.inputs.format());
        threadData.mWidth = db.inputs.width();
        threadData.mHeight = db.inputs.height();
        threadData.mBufferSize = db.inputs.bufferSize();
        threadData.mTotalBytes = totalBytes;
        threadData.mCudaDeviceIndex = db.inputs.cudaDeviceIndex();

        threadData.mStream = &state.mStream;
        threadData.mStreamDevice = &state.mStreamDevice;
        threadData.mStreamNotCreated = &state.mStreamNotCreated;

        threadData.mPublisher = state.mPublisher;
        threadData.mMessage = state.mMessage;

        return threadData;
    }

    static bool publishImageHelper(PublishImageThreadData& data)
    {

        CARB_PROFILE_ZONE(1, "Publish Image Thread");

        omni::isaac::utils::ScopedDevice scopedDev(data.mCudaDeviceIndex);

        // if the device doesn't match and we have created a stream, destroy it
        if (*data.mStreamDevice != data.mCudaDeviceIndex && *data.mStreamNotCreated == false)
        {
            CARB_PROFILE_ZONE(1, "Destroy stream");
            CUDA_CHECK(cudaStreamDestroy(*data.mStream));
            *data.mStreamNotCreated = true;
            *data.mStreamDevice = -1;
        }
        // create a stream if it does not exist
        if (*data.mStreamNotCreated)
        {
            CARB_PROFILE_ZONE(1, "Create stream");
            CUDA_CHECK(cudaStreamCreate(data.mStream));
            *data.mStreamNotCreated = false;
            *data.mStreamDevice = data.mCudaDeviceIndex;
        }


        if (data.mBufferSize == 0)
        {
            CARB_PROFILE_ZONE(1, "data in gpu texture");
            cudaArray_t levelArray = 0;
            CUDA_CHECK(
                cudaGetMipmappedArrayLevel(&levelArray, reinterpret_cast<cudaMipmappedArray_t>(data.mInputDataPtr), 0));
            switch (static_cast<carb::graphics::Format>(data.mFormat))
            {
            case carb::graphics::Format::eR32_SFLOAT:
                if (data.mWidth * data.mHeight * sizeof(float) != data.mTotalBytes)
                {
                    CARB_LOG_ERROR("totalBytes doesn't match eR32_SFLOAT %zu %zu",
                                   data.mWidth * data.mHeight * sizeof(float), data.mTotalBytes);
                }
                else
                {
                    CUDA_CHECK(cudaMemcpy2DFromArrayAsync(data.mOutputDataPtr, data.mWidth * sizeof(float), levelArray,
                                                          0, 0, data.mWidth * sizeof(float), data.mHeight,
                                                          cudaMemcpyDeviceToHost, *data.mStream));
                    CUDA_CHECK(cudaStreamSynchronize(*data.mStream));
                }
                break;

            default:
                CARB_LOG_ERROR("SdRenderVarToRawArray : input texture format (%d) is not supported.",
                               static_cast<int>(data.mFormat));
                return false;
            }
        }
        else
        {
            CARB_PROFILE_ZONE(1, "data in cuda memory");
            // xprintf("CPY %p %p %d %p", data.mOutputDataPtr, data.mInputDataPtr, data.mBufferSize, data.mStream);
            CUDA_CHECK(cudaMemcpyAsync(data.mOutputDataPtr, reinterpret_cast<void*>(data.mInputDataPtr),
                                       data.mBufferSize, cudaMemcpyDeviceToHost, *data.mStream));
            CUDA_CHECK(cudaStreamSynchronize(*data.mStream));
        }

        {
            CARB_PROFILE_ZONE(1, "image publisher publish");
            data.mPublisher.get()->publish(data.mMessage->ptr());
        }
        return true;
    }

    PublishNitrosBridgeImageThreadData buildNitrosBridgeThreadData(OgnROS2PublishImageDatabase& db,
                                                                   OgnROS2PublishImage& state,
                                                                   void* dataPtr,
                                                                   size_t totalBytes)
    {
        PublishNitrosBridgeImageThreadData threadData;

        threadData.mInputDataPtr = reinterpret_cast<void*>(db.inputs.dataPtr());
        threadData.mOutputDataPtr = dataPtr;
        threadData.mFormat = static_cast<carb::graphics::Format>(db.inputs.format());
        threadData.mWidth = db.inputs.width();
        threadData.mHeight = db.inputs.height();
        threadData.mBufferSize = db.inputs.bufferSize();
        threadData.mTotalBytes = totalBytes;
        threadData.mCudaDeviceIndex = db.inputs.cudaDeviceIndex();

        threadData.mNitrosBridgeStream = &state.mNitrosBridgeStream;
        threadData.mNitrosBridgeStreamDevice = &state.mNitrosBridgeStreamDevice;
        threadData.mNitrosBridgeStreamNotCreated = &state.mNitrosBridgeStreamNotCreated;

#if !defined(_WIN32) && !defined(ROS2_BACKEND_FOXY)
        threadData.mIPCBufferManager = state.mIPCBufferManager;
#endif

        threadData.mNitrosBridgePublisher = state.mNitrosBridgePublisher;
        threadData.mNitrosBridgeMessage = state.mNitrosBridgeMessage;

        return threadData;
    }

    bool publishNitrosBridgeImage(OgnROS2PublishImageDatabase& db)
    {
#if !defined(_WIN32) && !defined(ROS2_BACKEND_FOXY)
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

            if (state.mMultithreadingDisabled)
            {
                CARB_PROFILE_ZONE(1, "nitros image publisher publish");
                state.mNitrosBridgePublisher.get()->publish(state.mNitrosBridgeMessage->ptr());
            }
            else
            {
                tasking->addTask(carb::tasking::Priority::eHigh, state.mNitrosBridgeTasks,
                                 [&state]
                                 {
                                     CARB_PROFILE_ZONE(1, "nitros image publisher publish");
                                     state.mNitrosBridgePublisher.get()->publish(state.mNitrosBridgeMessage->ptr());
                                 });
            }
        }
        // data on device
        else
        {
            PublishNitrosBridgeImageThreadData publishNitrosBridgeImageThreadData =
                buildNitrosBridgeThreadData(db, state, dataPtr, totalBytes);

            if (state.mMultithreadingDisabled)
            {
                return publishNitrosBridgeHelper(publishNitrosBridgeImageThreadData);
            }
            else
            {
                // in order to get the benefits of using a separate stream, do all of the work in a new thread
                tasking->addTask(carb::tasking::Priority::eHigh, state.mTasks,
                                 [data = publishNitrosBridgeImageThreadData]() mutable
                                 { return publishNitrosBridgeHelper(data); });
            }
        }
#endif
        return true;
    }

    static bool publishNitrosBridgeHelper(PublishNitrosBridgeImageThreadData& data)
    {
#if !defined(_WIN32) && !defined(ROS2_BACKEND_FOXY)
        CARB_PROFILE_ZONE(1, "publish nitros image thread");
        omni::isaac::utils::ScopedDevice scopedDev(data.mCudaDeviceIndex);

        // if the device doesn't match and we have created a stream, destroy it
        if (*data.mNitrosBridgeStreamDevice != data.mCudaDeviceIndex && *data.mNitrosBridgeStreamNotCreated == false)
        {
            CARB_PROFILE_ZONE(1, "Destroy stream");
            cudaStreamDestroy(*data.mNitrosBridgeStream);
            *data.mNitrosBridgeStreamNotCreated = true;
            *data.mNitrosBridgeStreamDevice = -1;
        }
        // create a stream if it does not exist
        if (*data.mNitrosBridgeStreamNotCreated)
        {
            CARB_PROFILE_ZONE(1, "Create stream");
            cudaStreamCreate(&*data.mNitrosBridgeStream);
            *data.mNitrosBridgeStreamNotCreated = false;
            *data.mNitrosBridgeStreamDevice = data.mCudaDeviceIndex;
        }

        // data in gpu texture
        if (data.mBufferSize == 0)
        {
            CARB_PROFILE_ZONE(1, "data in gpu texture");
            cudaArray_t levelArray = 0;
            CUDA_CHECK(
                cudaGetMipmappedArrayLevel(&levelArray, reinterpret_cast<cudaMipmappedArray_t>(data.mInputDataPtr), 0));
            switch (static_cast<carb::graphics::Format>(data.mFormat))
            {
            case carb::graphics::Format::eR32_SFLOAT:
                if (data.mWidth * data.mHeight * sizeof(float) != data.mTotalBytes)
                {
                    CARB_LOG_ERROR("totalBytes doesn't match eR32_SFLOAT %zu %zu",
                                   data.mWidth * data.mHeight * sizeof(float), data.mTotalBytes);
                }
                else
                {
                    CUDA_CHECK(cudaMemcpy2DFromArrayAsync(data.mOutputDataPtr, data.mWidth * sizeof(float), levelArray,
                                                          0, 0, data.mWidth * sizeof(float), data.mHeight,
                                                          cudaMemcpyDeviceToDevice, *data.mNitrosBridgeStream));
                    CUDA_CHECK(cudaStreamSynchronize(*data.mNitrosBridgeStream));
                }
                break;
            default:
                CARB_LOG_ERROR("SdRenderVarToRawArray : input texture format (%d) is not supported.",
                               static_cast<int>(data.mFormat));
                return false;
            }
        }
        // data in CUDA memory
        else
        {
            CARB_PROFILE_ZONE(1, "data in cuda memory");
            CUDA_CHECK(cudaMemcpyAsync(data.mOutputDataPtr, reinterpret_cast<void*>(data.mInputDataPtr),
                                       data.mBufferSize, cudaMemcpyDeviceToDevice, *data.mNitrosBridgeStream));
            CUDA_CHECK(cudaStreamSynchronize(*data.mNitrosBridgeStream));
        }

        data.mNitrosBridgeMessage->setData(data.mIPCBufferManager->get_cur_ipc_mem_handle());
        data.mIPCBufferManager->next();

        {
            CARB_PROFILE_ZONE(1, "nitros image publisher publish");
            data.mNitrosBridgePublisher.get()->publish(data.mNitrosBridgeMessage->ptr());
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
            CUDA_CHECK(cudaStreamDestroy(mStream));
            mStreamDevice = -1;
            mStreamNotCreated = true;
        }
        if (mNitrosBridgeStreamNotCreated == false)
        {
            omni::isaac::utils::ScopedDevice scopedDev(mNitrosBridgeStreamDevice);
            CUDA_CHECK(cudaStreamDestroy(mNitrosBridgeStream));
            mNitrosBridgeStreamDevice = -1;
            mNitrosBridgeStreamNotCreated = true;
        }

#if !defined(_WIN32) && !defined(ROS2_BACKEND_FOXY)
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

#if !defined(_WIN32) && !defined(ROS2_BACKEND_FOXY)
    std::shared_ptr<IPCBufferManager> mIPCBufferManager = nullptr; // CUDA IPC memory pool manager
#endif
    std::shared_ptr<Ros2Publisher> mNitrosBridgePublisher = nullptr;
    std::shared_ptr<Ros2NitrosBridgeImageMessage> mNitrosBridgeMessage = nullptr;

    std::string mFrameId = "sim_camera";

    carb::tasking::TaskGroup mTasks;
    cudaStream_t mStream;
    int mStreamDevice = -1;
    bool mStreamNotCreated = true;

    carb::tasking::TaskGroup mNitrosBridgeTasks;
    cudaStream_t mNitrosBridgeStream;
    int mNitrosBridgeStreamDevice = -1;
    bool mNitrosBridgeStreamNotCreated = true;

    bool mMultithreadingDisabled = false;
};

REGISTER_OGN_NODE()
