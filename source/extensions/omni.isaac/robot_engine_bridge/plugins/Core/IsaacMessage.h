#pragma once

#include <carb/cuda/CudaRuntime.h>
#include <carb/logging/Log.h>

#include <capnp/compat/json.h>
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


/// Generate JSON message data and buffer data from captured camera data (Color, Depth and
/// Instance).

// static std::string ToJsonMessage(const CameraCapture& data, ulong& proto_id, unsigned char* buffers)
// {
//     // TODO
// }

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

private:
    std::unique_ptr<::capnp::MallocMessageBuilder> mCapnpMessageBuilder;
};

namespace isaac_message
{
static const uint64_t ActorGroupProtoId = 15616880102797312316U;
static const uint64_t CollisionProtoId = 16245352794000411201U;
static const uint64_t ImageProtoId = 16240193334533147313U;
static const uint64_t CameraIntrinsicsProtoId = 17438625575095802085U;
static const uint64_t CompositeProtoId = 11748931141111337194U;
static const uint64_t LabelProtoId = 13706910962019518033U;
static const uint64_t FlatscanProtoId = 15101491517973344605U;
static const uint64_t JsonProtoId = 16451265754834835783U;
static const uint64_t Plan2ProtoId = 17863627595039553900U;
static const uint64_t PoseTreeEdgeProtoId = 15616880102797312316U;
static const uint64_t RangeScanProtoId = 11901202900662173387U;
static const uint64_t RigidBody3GroupProtoId = 11014643331508973803U;
static const uint64_t StateProtoId = 13177870757040999364U;
static const uint64_t Detections2ProtoId = 12576484744224273470U;
static const uint64_t Detections3ProtoId = 16439473061879685265U;
// namespace ElementType
// {
// static const std::string uint8 = "uint8";
// static const std::string uint16 = "uint16";
// static const std::string uint32 = "uint32";
// static const std::string uint64 = "uint64";
// static const std::string int8 = "int8";
// static const std::string int16 = "int16";
// static const std::string int32 = "int32";
// static const std::string int64 = "int64";
// static const std::string float16 = "float16";
// static const std::string float32 = "float32";
// static const std::string float64 = "float64";
// }

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
}
}
}
