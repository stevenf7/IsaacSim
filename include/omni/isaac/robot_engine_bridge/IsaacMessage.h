// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <carb/cuda/CudaRuntime.h>
#include <carb/logging/Log.h>

#include <capnp/compat/json.h>
#include <capnp/serialize.h>
#include <messages/actor_group.capnp.h>
#include <messages/alice.capnp.h>
#include <messages/camera.capnp.h>
#include <messages/collision.capnp.h>
#include <messages/composite.capnp.h>
#include <messages/detections.capnp.h>
#include <messages/differential_base.capnp.h>
#include <messages/flatscan.capnp.h>
#include <messages/image.capnp.h>
#include <messages/json.capnp.h>
#include <messages/label.capnp.h>
#include <messages/math.capnp.h>
#include <messages/pose_tree.capnp.h>
#include <messages/range_scan.capnp.h>
#include <messages/rigid_body_3_group.capnp.h>
#include <messages/state.capnp.h>
#include <messages/tensor.capnp.h>
#include <omni/isaac/robot_engine_bridge/IsaacCApi.h>

#include <cuda.h>
#include <memory>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string>
#include <unordered_map>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{


namespace isaac_message
{
static capnp::JsonCodec gJsonCodec;

/// "math.capnp".Vector2dProto
typedef Vector2dProto Vector2d;

/// "math.capnp".SO2dProto
typedef SO2dProto SO2d;

/// "math.capnp".Pose2dProto
typedef Pose2dProto Pose2d;

/// "math.capnp".Vector3dProto
typedef Vector3dProto Vector3d;

/// "math.capnp".QuaterniondProto
typedef QuaterniondProto Quaterniond;

/// "math.capnp".SO3d
typedef SO3dProto SO3d;

/// "math.capnp".Pose3dProto
typedef Pose3dProto Pose3d;

/// "math.capnp".PoseTreeEdgeProto
typedef PoseTreeEdgeProto PoseTreeEdge;

/// "composite.capnp".CompositeProto
typedef CompositeProto Composite;

/// "camera.capnp".PinholeProto
typedef PinholeProto Pinhole;

/// "math.capnp".VectorXdProto
typedef VectorXdProto VectorXd;

/// "camera.capnp".DistortionProto
typedef DistortionProto Distortion;

/// "camera.capnp".CameraIntrinsicsProto
typedef CameraIntrinsicsProto CameraIntrinsics;

/// "image.capnp".ImageProto
typedef ImageProto Image;

/// "label.capnp".LabelProto
typedef LabelProto Labels;

/// "detections.capnp".Detections2Proto
typedef Detections2Proto Detections2;

/// "detections.capnp".Detections3Proto
typedef Detections3Proto Detections3;

enum CameraCaptureType
{
    Rgba32Color = 0,
    DepthFloat = 1,
    InstanceLabel32 = 2
};

typedef std::unordered_map<std::string, int> HashTable;
// Helper structures for ToJsonMessage() to handle camera data
struct CameraCapture
{
    int width;
    int height;
    unsigned char* image;
    CameraCaptureType type;
    HashTable labels;
    Pinhole pinhole;
    Vector2d depth_range;
};

/// "range_scan.capnp".RangeScanProto
typedef RangeScanProto RangeScan;

/// "flatscan.capnp".FlatscanProto
typedef FlatscanProto Flatscan;

/// "tensor.capnp".TensorProto
typedef TensorProto Tensor;

// struct TensorStruct
// {
//     std::string elementType;
//     std::vector<int> sizes;
//     uint scanlineStride;
//     uint dataBufferIndex;
// };

// static TensorStruct CreateTensor(std::string elementType, const std::vector<int>& sizes, uint bufferIndex)
// {
//     return TensorStruct{
//         elementType,
//         sizes,
//         0,
//         bufferIndex,
//     };
// }

/// "state.capnp".StateProto
typedef StateProto State;

// struct StateStruct
// {
//     TensorStruct pack;
//     std::string schema;
//     double* data;
// };

/// "rigid_body_3_group.capnp".RigidBody3Proto
typedef RigidBody3Proto RigidBody3;

/// "rigid_body_3_group.capnp".RigidBody3GroupProto
typedef RigidBody3GroupProto RigidBody3Group;

/// "collision.capnp".CollisionProto
typedef CollisionProto Collision;

/// "actor_group.capnp".ActorGroupProto
typedef ActorGroupProto ActorGroup;

/// "differential_base.capnp".Plan2Proto
typedef Plan2Proto Plan2;

/// "json.capnp".JsonProto
typedef JsonProto Json;
}


namespace
{
constexpr uint16_t word_length = sizeof(capnp::word);
}

struct MessageHeader
{
    isaac_uuid_t uuid;
    int64_t acqtime;
    int64_t pubtime;
};

class IsaacBuffer
{
public:
    virtual ~IsaacBuffer()
    {
    }
    virtual void resize(size_t size) = 0;
    virtual uint8_t* data() const = 0;
    virtual size_t size() const = 0;
    virtual isaac_memory_t type() const
    {
        return mMemoryType;
    }

protected:
    isaac_memory_t mMemoryType;
};

class IsaacDeviceBuffer : public IsaacBuffer
{
public:
    IsaacDeviceBuffer(size_t size = 0)
    {
        mMemoryType = isaac_memory_t::isaac_memory_cuda;
        resize(size);
    }
    virtual ~IsaacDeviceBuffer()
    {
        CUDA_CHECK(cudaFree(mBuffer));
        mBuffer = nullptr;
    }
    virtual void resize(size_t size)
    {
        if (size != mSize)
        {
            if (mBuffer)
            {
                CUDA_CHECK(cudaFree(mBuffer));
                mBuffer = nullptr;
            }
            if (size > 0)
            {
                CUDA_CHECK(cudaMalloc(&mBuffer, size));
            }
            mSize = size;
        }
    }
    virtual uint8_t* data() const
    {
        return mBuffer;
    }
    virtual size_t size() const
    {
        return mSize;
    }

private:
    uint8_t* mBuffer = nullptr;
    size_t mSize = 0;
};

class IsaacHostBuffer : public IsaacBuffer
{
public:
    IsaacHostBuffer(size_t size = 0)
    {
        mMemoryType = isaac_memory_t::isaac_memory_host;
        resize(size);
    }
    virtual void resize(size_t size)
    {
        mBuffer.resize(size);
    }
    virtual uint8_t* data() const
    {
        return (uint8_t*)mBuffer.data();
    }
    virtual size_t size() const
    {
        return mBuffer.size();
    }

    std::vector<uint8_t> mBuffer;
};


/**
 * @brief A wrapper around proto messages to make construction easier
 *
 * @tparam Proto
 */
template <typename Proto>
class IsaacMessage
{
public:
    typename Proto::Builder initProto()
    {

        mCapnpMessageBuilder.reset(new ::capnp::MallocMessageBuilder());
        return mCapnpMessageBuilder->initRoot<Proto>();
    }

    typename Proto::Reader getProto()
    {
        return mCapnpMessageBuilder->getRoot<Proto>();
    }

    void capnpSegmentsToFlatArray()
    {
        segments = mCapnpMessageBuilder->getSegmentsForOutput();
        segment_ptrs.resize(segments.size());
        segment_sizes.resize(segments.size());
        constexpr uint16_t word_length = sizeof(capnp::word);
        for (uint64_t i = 0; i < segments.size(); ++i)
        {
            segment_ptrs[i] = reinterpret_cast<const uint8_t*>(segments[i].begin());
            segment_sizes[i] = segments[i].size() * word_length;
        }
    }

    void flatArrayToCapnpBuffer()
    {
        kj_segments.resize(segment_ptrs.size());
        for (uint64_t i = 0; i < segment_ptrs.size(); i++)
        {
            kj_segments[i] = (kj::ArrayPtr<const ::capnp::word>(
                reinterpret_cast<const ::capnp::word*>(segment_ptrs[i]),
                reinterpret_cast<const ::capnp::word*>(segment_ptrs[i] + segment_sizes[i])));
        }

        ::capnp::ReaderOptions options;
        options.traversalLimitInWords = kj::maxValue;
        segments = kj::ArrayPtr<const kj::ArrayPtr<const ::capnp::word>>(kj_segments.data(), kj_segments.size());
        mCapnpSegmentMessageReader.reset(new ::capnp::SegmentArrayMessageReader(segments, options));
        // Copy the data to a builder so it cannot go out of scope
        mCapnpMessageBuilder.reset(new ::capnp::MallocMessageBuilder());
        mCapnpMessageBuilder->setRoot(mCapnpSegmentMessageReader->getRoot<Proto>());
    }
    void printJson()
    {
        kj::String message_json = isaac_message::gJsonCodec.encode(getProto());
        CARB_LOG_ERROR("Message json: %s", message_json.cStr());
    }
    bool checkType(const int64_t type)
    {
        return ::capnp::typeId<Proto>() == static_cast<uint64_t>(type);
    }
    int64_t protoId()
    {
        return ::capnp::typeId<Proto>();
    }
    std::vector<const uint8_t*> segment_ptrs;
    std::vector<uint64_t> segment_sizes;

private:
    std::unique_ptr<::capnp::MallocMessageBuilder> mCapnpMessageBuilder;
    std::unique_ptr<::capnp::SegmentArrayMessageReader> mCapnpSegmentMessageReader;
    std::vector<kj::ArrayPtr<const ::capnp::word>> kj_segments;
    kj::ArrayPtr<const kj::ArrayPtr<const ::capnp::word>> segments;
};

}
}
}
