// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from isaac_ros2_messages:srv/IsaacPose.idl
// generated code does not contain a copyright notice
#include "isaac_ros2_messages/srv/detail/isaac_pose__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `names`
#include "rosidl_runtime_c/string_functions.h"
// Member `poses`
#include "geometry_msgs/msg/detail/pose__functions.h"
// Member `velocities`
#include "geometry_msgs/msg/detail/twist__functions.h"
// Member `scales`
#include "geometry_msgs/msg/detail/vector3__functions.h"

bool isaac_ros2_messages__srv__IsaacPose_Request__init(isaac_ros2_messages__srv__IsaacPose_Request* msg)
{
    if (!msg)
    {
        return false;
    }
    // header
    if (!std_msgs__msg__Header__init(&msg->header))
    {
        isaac_ros2_messages__srv__IsaacPose_Request__fini(msg);
        return false;
    }
    // names
    if (!rosidl_runtime_c__String__Sequence__init(&msg->names, 0))
    {
        isaac_ros2_messages__srv__IsaacPose_Request__fini(msg);
        return false;
    }
    // poses
    if (!geometry_msgs__msg__Pose__Sequence__init(&msg->poses, 0))
    {
        isaac_ros2_messages__srv__IsaacPose_Request__fini(msg);
        return false;
    }
    // velocities
    if (!geometry_msgs__msg__Twist__Sequence__init(&msg->velocities, 0))
    {
        isaac_ros2_messages__srv__IsaacPose_Request__fini(msg);
        return false;
    }
    // scales
    if (!geometry_msgs__msg__Vector3__Sequence__init(&msg->scales, 0))
    {
        isaac_ros2_messages__srv__IsaacPose_Request__fini(msg);
        return false;
    }
    return true;
}

void isaac_ros2_messages__srv__IsaacPose_Request__fini(isaac_ros2_messages__srv__IsaacPose_Request* msg)
{
    if (!msg)
    {
        return;
    }
    // header
    std_msgs__msg__Header__fini(&msg->header);
    // names
    rosidl_runtime_c__String__Sequence__fini(&msg->names);
    // poses
    geometry_msgs__msg__Pose__Sequence__fini(&msg->poses);
    // velocities
    geometry_msgs__msg__Twist__Sequence__fini(&msg->velocities);
    // scales
    geometry_msgs__msg__Vector3__Sequence__fini(&msg->scales);
}

isaac_ros2_messages__srv__IsaacPose_Request* isaac_ros2_messages__srv__IsaacPose_Request__create()
{
    isaac_ros2_messages__srv__IsaacPose_Request* msg =
        (isaac_ros2_messages__srv__IsaacPose_Request*)malloc(sizeof(isaac_ros2_messages__srv__IsaacPose_Request));
    if (!msg)
    {
        return NULL;
    }
    memset(msg, 0, sizeof(isaac_ros2_messages__srv__IsaacPose_Request));
    bool success = isaac_ros2_messages__srv__IsaacPose_Request__init(msg);
    if (!success)
    {
        free(msg);
        return NULL;
    }
    return msg;
}

void isaac_ros2_messages__srv__IsaacPose_Request__destroy(isaac_ros2_messages__srv__IsaacPose_Request* msg)
{
    if (msg)
    {
        isaac_ros2_messages__srv__IsaacPose_Request__fini(msg);
    }
    free(msg);
}


bool isaac_ros2_messages__srv__IsaacPose_Request__Sequence__init(
    isaac_ros2_messages__srv__IsaacPose_Request__Sequence* array, size_t size)
{
    if (!array)
    {
        return false;
    }
    isaac_ros2_messages__srv__IsaacPose_Request* data = NULL;
    if (size)
    {
        data = (isaac_ros2_messages__srv__IsaacPose_Request*)calloc(
            size, sizeof(isaac_ros2_messages__srv__IsaacPose_Request));
        if (!data)
        {
            return false;
        }
        // initialize all array elements
        size_t i;
        for (i = 0; i < size; ++i)
        {
            bool success = isaac_ros2_messages__srv__IsaacPose_Request__init(&data[i]);
            if (!success)
            {
                break;
            }
        }
        if (i < size)
        {
            // if initialization failed finalize the already initialized array elements
            for (; i > 0; --i)
            {
                isaac_ros2_messages__srv__IsaacPose_Request__fini(&data[i - 1]);
            }
            free(data);
            return false;
        }
    }
    array->data = data;
    array->size = size;
    array->capacity = size;
    return true;
}

void isaac_ros2_messages__srv__IsaacPose_Request__Sequence__fini(isaac_ros2_messages__srv__IsaacPose_Request__Sequence* array)
{
    if (!array)
    {
        return;
    }
    if (array->data)
    {
        // ensure that data and capacity values are consistent
        assert(array->capacity > 0);
        // finalize all array elements
        for (size_t i = 0; i < array->capacity; ++i)
        {
            isaac_ros2_messages__srv__IsaacPose_Request__fini(&array->data[i]);
        }
        free(array->data);
        array->data = NULL;
        array->size = 0;
        array->capacity = 0;
    }
    else
    {
        // ensure that data, size, and capacity values are consistent
        assert(0 == array->size);
        assert(0 == array->capacity);
    }
}

isaac_ros2_messages__srv__IsaacPose_Request__Sequence* isaac_ros2_messages__srv__IsaacPose_Request__Sequence__create(
    size_t size)
{
    isaac_ros2_messages__srv__IsaacPose_Request__Sequence* array =
        (isaac_ros2_messages__srv__IsaacPose_Request__Sequence*)malloc(
            sizeof(isaac_ros2_messages__srv__IsaacPose_Request__Sequence));
    if (!array)
    {
        return NULL;
    }
    bool success = isaac_ros2_messages__srv__IsaacPose_Request__Sequence__init(array, size);
    if (!success)
    {
        free(array);
        return NULL;
    }
    return array;
}

void isaac_ros2_messages__srv__IsaacPose_Request__Sequence__destroy(
    isaac_ros2_messages__srv__IsaacPose_Request__Sequence* array)
{
    if (array)
    {
        isaac_ros2_messages__srv__IsaacPose_Request__Sequence__fini(array);
    }
    free(array);
}


bool isaac_ros2_messages__srv__IsaacPose_Response__init(isaac_ros2_messages__srv__IsaacPose_Response* msg)
{
    if (!msg)
    {
        return false;
    }
    // structure_needs_at_least_one_member
    return true;
}

void isaac_ros2_messages__srv__IsaacPose_Response__fini(isaac_ros2_messages__srv__IsaacPose_Response* msg)
{
    if (!msg)
    {
        return;
    }
    // structure_needs_at_least_one_member
}

isaac_ros2_messages__srv__IsaacPose_Response* isaac_ros2_messages__srv__IsaacPose_Response__create()
{
    isaac_ros2_messages__srv__IsaacPose_Response* msg =
        (isaac_ros2_messages__srv__IsaacPose_Response*)malloc(sizeof(isaac_ros2_messages__srv__IsaacPose_Response));
    if (!msg)
    {
        return NULL;
    }
    memset(msg, 0, sizeof(isaac_ros2_messages__srv__IsaacPose_Response));
    bool success = isaac_ros2_messages__srv__IsaacPose_Response__init(msg);
    if (!success)
    {
        free(msg);
        return NULL;
    }
    return msg;
}

void isaac_ros2_messages__srv__IsaacPose_Response__destroy(isaac_ros2_messages__srv__IsaacPose_Response* msg)
{
    if (msg)
    {
        isaac_ros2_messages__srv__IsaacPose_Response__fini(msg);
    }
    free(msg);
}


bool isaac_ros2_messages__srv__IsaacPose_Response__Sequence__init(
    isaac_ros2_messages__srv__IsaacPose_Response__Sequence* array, size_t size)
{
    if (!array)
    {
        return false;
    }
    isaac_ros2_messages__srv__IsaacPose_Response* data = NULL;
    if (size)
    {
        data = (isaac_ros2_messages__srv__IsaacPose_Response*)calloc(
            size, sizeof(isaac_ros2_messages__srv__IsaacPose_Response));
        if (!data)
        {
            return false;
        }
        // initialize all array elements
        size_t i;
        for (i = 0; i < size; ++i)
        {
            bool success = isaac_ros2_messages__srv__IsaacPose_Response__init(&data[i]);
            if (!success)
            {
                break;
            }
        }
        if (i < size)
        {
            // if initialization failed finalize the already initialized array elements
            for (; i > 0; --i)
            {
                isaac_ros2_messages__srv__IsaacPose_Response__fini(&data[i - 1]);
            }
            free(data);
            return false;
        }
    }
    array->data = data;
    array->size = size;
    array->capacity = size;
    return true;
}

void isaac_ros2_messages__srv__IsaacPose_Response__Sequence__fini(
    isaac_ros2_messages__srv__IsaacPose_Response__Sequence* array)
{
    if (!array)
    {
        return;
    }
    if (array->data)
    {
        // ensure that data and capacity values are consistent
        assert(array->capacity > 0);
        // finalize all array elements
        for (size_t i = 0; i < array->capacity; ++i)
        {
            isaac_ros2_messages__srv__IsaacPose_Response__fini(&array->data[i]);
        }
        free(array->data);
        array->data = NULL;
        array->size = 0;
        array->capacity = 0;
    }
    else
    {
        // ensure that data, size, and capacity values are consistent
        assert(0 == array->size);
        assert(0 == array->capacity);
    }
}

isaac_ros2_messages__srv__IsaacPose_Response__Sequence* isaac_ros2_messages__srv__IsaacPose_Response__Sequence__create(
    size_t size)
{
    isaac_ros2_messages__srv__IsaacPose_Response__Sequence* array =
        (isaac_ros2_messages__srv__IsaacPose_Response__Sequence*)malloc(
            sizeof(isaac_ros2_messages__srv__IsaacPose_Response__Sequence));
    if (!array)
    {
        return NULL;
    }
    bool success = isaac_ros2_messages__srv__IsaacPose_Response__Sequence__init(array, size);
    if (!success)
    {
        free(array);
        return NULL;
    }
    return array;
}

void isaac_ros2_messages__srv__IsaacPose_Response__Sequence__destroy(
    isaac_ros2_messages__srv__IsaacPose_Response__Sequence* array)
{
    if (array)
    {
        isaac_ros2_messages__srv__IsaacPose_Response__Sequence__fini(array);
    }
    free(array);
}
