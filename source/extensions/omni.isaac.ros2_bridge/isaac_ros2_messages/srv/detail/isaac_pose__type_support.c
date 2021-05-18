// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from isaac_ros2_messages:srv/IsaacPose.idl
// generated code does not contain a copyright notice

#include "isaac_ros2_messages/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "isaac_ros2_messages/srv/detail/isaac_pose__functions.h"
#include "isaac_ros2_messages/srv/detail/isaac_pose__rosidl_typesupport_introspection_c.h"
#include "isaac_ros2_messages/srv/detail/isaac_pose__struct.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"

#include <stddef.h>


// Include directives for member types
// Member `header`
#include "std_msgs/msg/header.h"
// Member `header`
#include "std_msgs/msg/detail/header__rosidl_typesupport_introspection_c.h"
// Member `names`
#include "rosidl_runtime_c/string_functions.h"
// Member `poses`
#include "geometry_msgs/msg/pose.h"
// Member `poses`
#include "geometry_msgs/msg/detail/pose__rosidl_typesupport_introspection_c.h"
// Member `velocities`
#include "geometry_msgs/msg/twist.h"
// Member `velocities`
#include "geometry_msgs/msg/detail/twist__rosidl_typesupport_introspection_c.h"
// Member `scales`
#include "geometry_msgs/msg/vector3.h"
// Member `scales`
#include "geometry_msgs/msg/detail/vector3__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

    void IsaacPose_Request__rosidl_typesupport_introspection_c__IsaacPose_Request_init_function(
        void* message_memory, enum rosidl_runtime_c__message_initialization _init)
    {
        // TODO(karsten1987): initializers are not yet implemented for typesupport c
        // see https://github.com/ros2/ros2/issues/397
        (void)_init;
        isaac_ros2_messages__srv__IsaacPose_Request__init(message_memory);
    }

    void IsaacPose_Request__rosidl_typesupport_introspection_c__IsaacPose_Request_fini_function(void* message_memory)
    {
        isaac_ros2_messages__srv__IsaacPose_Request__fini(message_memory);
    }

    size_t IsaacPose_Request__rosidl_typesupport_introspection_c__size_function__Pose__poses(const void* untyped_member)
    {
        const geometry_msgs__msg__Pose__Sequence* member = (const geometry_msgs__msg__Pose__Sequence*)(untyped_member);
        return member->size;
    }

    const void* IsaacPose_Request__rosidl_typesupport_introspection_c__get_const_function__Pose__poses(
        const void* untyped_member, size_t index)
    {
        const geometry_msgs__msg__Pose__Sequence* member = (const geometry_msgs__msg__Pose__Sequence*)(untyped_member);
        return &member->data[index];
    }

    void* IsaacPose_Request__rosidl_typesupport_introspection_c__get_function__Pose__poses(void* untyped_member,
                                                                                           size_t index)
    {
        geometry_msgs__msg__Pose__Sequence* member = (geometry_msgs__msg__Pose__Sequence*)(untyped_member);
        return &member->data[index];
    }

    bool IsaacPose_Request__rosidl_typesupport_introspection_c__resize_function__Pose__poses(void* untyped_member,
                                                                                             size_t size)
    {
        geometry_msgs__msg__Pose__Sequence* member = (geometry_msgs__msg__Pose__Sequence*)(untyped_member);
        geometry_msgs__msg__Pose__Sequence__fini(member);
        return geometry_msgs__msg__Pose__Sequence__init(member, size);
    }

    size_t IsaacPose_Request__rosidl_typesupport_introspection_c__size_function__Twist__velocities(const void* untyped_member)
    {
        const geometry_msgs__msg__Twist__Sequence* member = (const geometry_msgs__msg__Twist__Sequence*)(untyped_member);
        return member->size;
    }

    const void* IsaacPose_Request__rosidl_typesupport_introspection_c__get_const_function__Twist__velocities(
        const void* untyped_member, size_t index)
    {
        const geometry_msgs__msg__Twist__Sequence* member = (const geometry_msgs__msg__Twist__Sequence*)(untyped_member);
        return &member->data[index];
    }

    void* IsaacPose_Request__rosidl_typesupport_introspection_c__get_function__Twist__velocities(void* untyped_member,
                                                                                                 size_t index)
    {
        geometry_msgs__msg__Twist__Sequence* member = (geometry_msgs__msg__Twist__Sequence*)(untyped_member);
        return &member->data[index];
    }

    bool IsaacPose_Request__rosidl_typesupport_introspection_c__resize_function__Twist__velocities(void* untyped_member,
                                                                                                   size_t size)
    {
        geometry_msgs__msg__Twist__Sequence* member = (geometry_msgs__msg__Twist__Sequence*)(untyped_member);
        geometry_msgs__msg__Twist__Sequence__fini(member);
        return geometry_msgs__msg__Twist__Sequence__init(member, size);
    }

    size_t IsaacPose_Request__rosidl_typesupport_introspection_c__size_function__Vector3__scales(const void* untyped_member)
    {
        const geometry_msgs__msg__Vector3__Sequence* member =
            (const geometry_msgs__msg__Vector3__Sequence*)(untyped_member);
        return member->size;
    }

    const void* IsaacPose_Request__rosidl_typesupport_introspection_c__get_const_function__Vector3__scales(
        const void* untyped_member, size_t index)
    {
        const geometry_msgs__msg__Vector3__Sequence* member =
            (const geometry_msgs__msg__Vector3__Sequence*)(untyped_member);
        return &member->data[index];
    }

    void* IsaacPose_Request__rosidl_typesupport_introspection_c__get_function__Vector3__scales(void* untyped_member,
                                                                                               size_t index)
    {
        geometry_msgs__msg__Vector3__Sequence* member = (geometry_msgs__msg__Vector3__Sequence*)(untyped_member);
        return &member->data[index];
    }

    bool IsaacPose_Request__rosidl_typesupport_introspection_c__resize_function__Vector3__scales(void* untyped_member,
                                                                                                 size_t size)
    {
        geometry_msgs__msg__Vector3__Sequence* member = (geometry_msgs__msg__Vector3__Sequence*)(untyped_member);
        geometry_msgs__msg__Vector3__Sequence__fini(member);
        return geometry_msgs__msg__Vector3__Sequence__init(member, size);
    }

    static rosidl_typesupport_introspection_c__MessageMember
        IsaacPose_Request__rosidl_typesupport_introspection_c__IsaacPose_Request_message_member_array[5] = {
            {
                "header", // name
                rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE, // type
                0, // upper bound of string
                NULL, // members of sub message (initialized later)
                false, // is array
                0, // array size
                false, // is upper bound
                offsetof(isaac_ros2_messages__srv__IsaacPose_Request, header), // bytes offset in struct
                NULL, // default value
                NULL, // size() function pointer
                NULL, // get_const(index) function pointer
                NULL, // get(index) function pointer
                NULL // resize(index) function pointer
            },
            {
                "names", // name
                rosidl_typesupport_introspection_c__ROS_TYPE_STRING, // type
                0, // upper bound of string
                NULL, // members of sub message
                true, // is array
                0, // array size
                false, // is upper bound
                offsetof(isaac_ros2_messages__srv__IsaacPose_Request, names), // bytes offset in struct
                NULL, // default value
                NULL, // size() function pointer
                NULL, // get_const(index) function pointer
                NULL, // get(index) function pointer
                NULL // resize(index) function pointer
            },
            {
                "poses", // name
                rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE, // type
                0, // upper bound of string
                NULL, // members of sub message (initialized later)
                true, // is array
                0, // array size
                false, // is upper bound
                offsetof(isaac_ros2_messages__srv__IsaacPose_Request, poses), // bytes offset in struct
                NULL, // default value
                IsaacPose_Request__rosidl_typesupport_introspection_c__size_function__Pose__poses, // size() function
                                                                                                   // pointer
                IsaacPose_Request__rosidl_typesupport_introspection_c__get_const_function__Pose__poses, // get_const(index)
                                                                                                        // function
                                                                                                        // pointer
                IsaacPose_Request__rosidl_typesupport_introspection_c__get_function__Pose__poses, // get(index) function
                                                                                                  // pointer
                IsaacPose_Request__rosidl_typesupport_introspection_c__resize_function__Pose__poses // resize(index)
                                                                                                    // function pointer
            },
            {
                "velocities", // name
                rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE, // type
                0, // upper bound of string
                NULL, // members of sub message (initialized later)
                true, // is array
                0, // array size
                false, // is upper bound
                offsetof(isaac_ros2_messages__srv__IsaacPose_Request, velocities), // bytes offset in struct
                NULL, // default value
                IsaacPose_Request__rosidl_typesupport_introspection_c__size_function__Twist__velocities, // size()
                                                                                                         // function
                                                                                                         // pointer
                IsaacPose_Request__rosidl_typesupport_introspection_c__get_const_function__Twist__velocities, // get_const(index)
                                                                                                              // function
                                                                                                              // pointer
                IsaacPose_Request__rosidl_typesupport_introspection_c__get_function__Twist__velocities, // get(index)
                                                                                                        // function
                                                                                                        // pointer
                IsaacPose_Request__rosidl_typesupport_introspection_c__resize_function__Twist__velocities // resize(index)
                                                                                                          // function
                                                                                                          // pointer
            },
            {
                "scales", // name
                rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE, // type
                0, // upper bound of string
                NULL, // members of sub message (initialized later)
                true, // is array
                0, // array size
                false, // is upper bound
                offsetof(isaac_ros2_messages__srv__IsaacPose_Request, scales), // bytes offset in struct
                NULL, // default value
                IsaacPose_Request__rosidl_typesupport_introspection_c__size_function__Vector3__scales, // size()
                                                                                                       // function
                                                                                                       // pointer
                IsaacPose_Request__rosidl_typesupport_introspection_c__get_const_function__Vector3__scales, // get_const(index)
                                                                                                            // function
                                                                                                            // pointer
                IsaacPose_Request__rosidl_typesupport_introspection_c__get_function__Vector3__scales, // get(index)
                                                                                                      // function
                                                                                                      // pointer
                IsaacPose_Request__rosidl_typesupport_introspection_c__resize_function__Vector3__scales // resize(index)
                                                                                                        // function
                                                                                                        // pointer
            }
        };

    static const rosidl_typesupport_introspection_c__MessageMembers
        IsaacPose_Request__rosidl_typesupport_introspection_c__IsaacPose_Request_message_members = {
            "isaac_ros2_messages__srv", // message namespace
            "IsaacPose_Request", // message name
            5, // number of fields
            sizeof(isaac_ros2_messages__srv__IsaacPose_Request),
            IsaacPose_Request__rosidl_typesupport_introspection_c__IsaacPose_Request_message_member_array, // message
                                                                                                           // members
            IsaacPose_Request__rosidl_typesupport_introspection_c__IsaacPose_Request_init_function, // function to
                                                                                                    // initialize
                                                                                                    // message memory
                                                                                                    // (memory has to be
                                                                                                    // allocated)
            IsaacPose_Request__rosidl_typesupport_introspection_c__IsaacPose_Request_fini_function // function to
                                                                                                   // terminate message
                                                                                                   // instance (will not
                                                                                                   // free memory)
        };

    // this is not const since it must be initialized on first access
    // since C does not allow non-integral compile-time constants
    static rosidl_message_type_support_t
        IsaacPose_Request__rosidl_typesupport_introspection_c__IsaacPose_Request_message_type_support_handle = {
            0,
            &IsaacPose_Request__rosidl_typesupport_introspection_c__IsaacPose_Request_message_members,
            get_message_typesupport_handle_function,
        };

    ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_isaac_ros2_messages const rosidl_message_type_support_t* ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
        rosidl_typesupport_introspection_c, isaac_ros2_messages, srv, IsaacPose_Request)()
    {
        IsaacPose_Request__rosidl_typesupport_introspection_c__IsaacPose_Request_message_member_array[0].members_ =
            ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
                rosidl_typesupport_introspection_c, std_msgs, msg, Header)();
        IsaacPose_Request__rosidl_typesupport_introspection_c__IsaacPose_Request_message_member_array[2].members_ =
            ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
                rosidl_typesupport_introspection_c, geometry_msgs, msg, Pose)();
        IsaacPose_Request__rosidl_typesupport_introspection_c__IsaacPose_Request_message_member_array[3].members_ =
            ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
                rosidl_typesupport_introspection_c, geometry_msgs, msg, Twist)();
        IsaacPose_Request__rosidl_typesupport_introspection_c__IsaacPose_Request_message_member_array[4].members_ =
            ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
                rosidl_typesupport_introspection_c, geometry_msgs, msg, Vector3)();
        if (!IsaacPose_Request__rosidl_typesupport_introspection_c__IsaacPose_Request_message_type_support_handle
                 .typesupport_identifier)
        {
            IsaacPose_Request__rosidl_typesupport_introspection_c__IsaacPose_Request_message_type_support_handle
                .typesupport_identifier = rosidl_typesupport_introspection_c__identifier;
        }
        return &IsaacPose_Request__rosidl_typesupport_introspection_c__IsaacPose_Request_message_type_support_handle;
    }
#ifdef __cplusplus
}
#endif

// already included above
// #include <stddef.h>
// already included above
// #include "isaac_ros2_messages/srv/detail/isaac_pose__rosidl_typesupport_introspection_c.h"
// already included above
// #include "isaac_ros2_messages/msg/rosidl_typesupport_introspection_c__visibility_control.h"
// already included above
// #include "rosidl_typesupport_introspection_c/field_types.h"
// already included above
// #include "rosidl_typesupport_introspection_c/identifier.h"
// already included above
// #include "rosidl_typesupport_introspection_c/message_introspection.h"
// already included above
// #include "isaac_ros2_messages/srv/detail/isaac_pose__functions.h"
// already included above
// #include "isaac_ros2_messages/srv/detail/isaac_pose__struct.h"


#ifdef __cplusplus
extern "C"
{
#endif

    void IsaacPose_Response__rosidl_typesupport_introspection_c__IsaacPose_Response_init_function(
        void* message_memory, enum rosidl_runtime_c__message_initialization _init)
    {
        // TODO(karsten1987): initializers are not yet implemented for typesupport c
        // see https://github.com/ros2/ros2/issues/397
        (void)_init;
        isaac_ros2_messages__srv__IsaacPose_Response__init(message_memory);
    }

    void IsaacPose_Response__rosidl_typesupport_introspection_c__IsaacPose_Response_fini_function(void* message_memory)
    {
        isaac_ros2_messages__srv__IsaacPose_Response__fini(message_memory);
    }

    static rosidl_typesupport_introspection_c__MessageMember
        IsaacPose_Response__rosidl_typesupport_introspection_c__IsaacPose_Response_message_member_array[1] = { {
            "structure_needs_at_least_one_member", // name
            rosidl_typesupport_introspection_c__ROS_TYPE_UINT8, // type
            0, // upper bound of string
            NULL, // members of sub message
            false, // is array
            0, // array size
            false, // is upper bound
            offsetof(isaac_ros2_messages__srv__IsaacPose_Response, structure_needs_at_least_one_member), // bytes offset
                                                                                                         // in struct
            NULL, // default value
            NULL, // size() function pointer
            NULL, // get_const(index) function pointer
            NULL, // get(index) function pointer
            NULL // resize(index) function pointer
        } };

    static const rosidl_typesupport_introspection_c__MessageMembers
        IsaacPose_Response__rosidl_typesupport_introspection_c__IsaacPose_Response_message_members = {
            "isaac_ros2_messages__srv", // message namespace
            "IsaacPose_Response", // message name
            1, // number of fields
            sizeof(isaac_ros2_messages__srv__IsaacPose_Response),
            IsaacPose_Response__rosidl_typesupport_introspection_c__IsaacPose_Response_message_member_array, // message
                                                                                                             // members
            IsaacPose_Response__rosidl_typesupport_introspection_c__IsaacPose_Response_init_function, // function to
                                                                                                      // initialize
                                                                                                      // message memory
                                                                                                      // (memory has to
                                                                                                      // be allocated)
            IsaacPose_Response__rosidl_typesupport_introspection_c__IsaacPose_Response_fini_function // function to
                                                                                                     // terminate
                                                                                                     // message instance
                                                                                                     // (will not free
                                                                                                     // memory)
        };

    // this is not const since it must be initialized on first access
    // since C does not allow non-integral compile-time constants
    static rosidl_message_type_support_t
        IsaacPose_Response__rosidl_typesupport_introspection_c__IsaacPose_Response_message_type_support_handle = {
            0,
            &IsaacPose_Response__rosidl_typesupport_introspection_c__IsaacPose_Response_message_members,
            get_message_typesupport_handle_function,
        };

    ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_isaac_ros2_messages const rosidl_message_type_support_t* ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
        rosidl_typesupport_introspection_c, isaac_ros2_messages, srv, IsaacPose_Response)()
    {
        if (!IsaacPose_Response__rosidl_typesupport_introspection_c__IsaacPose_Response_message_type_support_handle
                 .typesupport_identifier)
        {
            IsaacPose_Response__rosidl_typesupport_introspection_c__IsaacPose_Response_message_type_support_handle
                .typesupport_identifier = rosidl_typesupport_introspection_c__identifier;
        }
        return &IsaacPose_Response__rosidl_typesupport_introspection_c__IsaacPose_Response_message_type_support_handle;
    }
#ifdef __cplusplus
}
#endif

#include "rosidl_runtime_c/service_type_support_struct.h"
// already included above
// #include "isaac_ros2_messages/msg/rosidl_typesupport_introspection_c__visibility_control.h"
// already included above
// #include "isaac_ros2_messages/srv/detail/isaac_pose__rosidl_typesupport_introspection_c.h"
// already included above
// #include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/service_introspection.h"

// this is intentionally not const to allow initialization later to prevent an initialization race
static rosidl_typesupport_introspection_c__ServiceMembers
    isaac_ros2_messages__srv__detail__isaac_pose__rosidl_typesupport_introspection_c__IsaacPose_service_members = {
        "isaac_ros2_messages__srv", // service namespace
        "IsaacPose", // service name
        // these two fields are initialized below on the first access
        NULL, // request message
        // isaac_ros2_messages__srv__detail__isaac_pose__rosidl_typesupport_introspection_c__IsaacPose_Request_message_type_support_handle,
        NULL // response message
        // isaac_ros2_messages__srv__detail__isaac_pose__rosidl_typesupport_introspection_c__IsaacPose_Response_message_type_support_handle
    };

static rosidl_service_type_support_t
    isaac_ros2_messages__srv__detail__isaac_pose__rosidl_typesupport_introspection_c__IsaacPose_service_type_support_handle = {
        0,
        &isaac_ros2_messages__srv__detail__isaac_pose__rosidl_typesupport_introspection_c__IsaacPose_service_members,
        get_service_typesupport_handle_function,
    };

// Forward declaration of request/response type support functions
const rosidl_message_type_support_t* ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
    rosidl_typesupport_introspection_c, isaac_ros2_messages, srv, IsaacPose_Request)();

const rosidl_message_type_support_t* ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
    rosidl_typesupport_introspection_c, isaac_ros2_messages, srv, IsaacPose_Response)();

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_isaac_ros2_messages const rosidl_service_type_support_t* ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(
    rosidl_typesupport_introspection_c, isaac_ros2_messages, srv, IsaacPose)()
{
    if (!isaac_ros2_messages__srv__detail__isaac_pose__rosidl_typesupport_introspection_c__IsaacPose_service_type_support_handle
             .typesupport_identifier)
    {
        isaac_ros2_messages__srv__detail__isaac_pose__rosidl_typesupport_introspection_c__IsaacPose_service_type_support_handle
            .typesupport_identifier = rosidl_typesupport_introspection_c__identifier;
    }
    rosidl_typesupport_introspection_c__ServiceMembers* service_members =
        (rosidl_typesupport_introspection_c__ServiceMembers*)
            isaac_ros2_messages__srv__detail__isaac_pose__rosidl_typesupport_introspection_c__IsaacPose_service_type_support_handle
                .data;

    if (!service_members->request_members_)
    {
        service_members->request_members_ =
            (const rosidl_typesupport_introspection_c__MessageMembers*)ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
                rosidl_typesupport_introspection_c, isaac_ros2_messages, srv, IsaacPose_Request)()
                ->data;
    }
    if (!service_members->response_members_)
    {
        service_members->response_members_ =
            (const rosidl_typesupport_introspection_c__MessageMembers*)ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
                rosidl_typesupport_introspection_c, isaac_ros2_messages, srv, IsaacPose_Response)()
                ->data;
    }

    return &isaac_ros2_messages__srv__detail__isaac_pose__rosidl_typesupport_introspection_c__IsaacPose_service_type_support_handle;
}
