#pragma once

#include <capnp/compat/json.h>
#include <messages/actor_group.capnp.h>
#include <messages/actuator_group.capnp.h>
#include <messages/alice.capnp.h>
#include <messages/camera.capnp.h>
#include <messages/collision.capnp.h>
#include <messages/composite.capnp.h>
#include <messages/differential_base.capnp.h>
#include <messages/flatscan.capnp.h>
#include <messages/json.capnp.h>
#include <messages/math.capnp.h>
#include <messages/pose_tree.capnp.h>
#include <messages/range_scan.capnp.h>
#include <messages/rigid_body_3_group.capnp.h>
#include <messages/state.capnp.h>
#include <messages/tensor.capnp.h>

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

struct IsaacBuffer
{
    size_t size;
    char* data;
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
static const uint64_t ColorCameraProtoId = 12905539496848989000U;
static const uint64_t CompositeProtoId = 11748931141111337194U;
static const uint64_t DepthCameraProtoId = 12947112471508155621U;
static const uint64_t SegmentationCameraProtoId = 14547487683356910760U;
static const uint64_t FlatscanProtoId = 15101491517973344605U;
static const uint64_t JsonProtoId = 16451265754834835783U;
static const uint64_t Plan2ProtoId = 17863627595039553900U;
static const uint64_t PoseTreeEdgeProtoId = 15616880102797312316U;
static const uint64_t RangeScanProtoId = 11901202900662173387U;
static const uint64_t RigidBody3GroupProtoId = 11014643331508973803U;
static const uint64_t StateProtoId = 13177870757040999364U;

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

/// "image.capnp".ImageProto
typedef ImageProto Image;

/// "camera.capnp".ColorCameraProto
typedef ColorCameraProto ColorCamera;

/// "camera.capnp".ColorCameraProto
typedef ColorCameraProto ColorCamera;

/// "camera.capnp".SegmentationCameraProto
typedef SegmentationCameraProto SegmentationCamera;

/// "camera.capnp".DepthCameraProtoProto
typedef DepthCameraProto DepthCamera;

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
