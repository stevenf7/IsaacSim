// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from isaac_ros2_messages:msg/BoundingBox3D.idl
// generated code does not contain a copyright notice
#include "isaac_ros2_messages/msg/detail/bounding_box3_d__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>


// Include directives for member types
// Member `name`
#include "rosidl_runtime_c/string_functions.h"
// Member `center`
#include "geometry_msgs/msg/detail/pose__functions.h"
// Member `size`
#include "geometry_msgs/msg/detail/vector3__functions.h"

bool isaac_ros2_messages__msg__BoundingBox3D__init(isaac_ros2_messages__msg__BoundingBox3D* msg)
{
    if (!msg)
    {
        return false;
    }
    // name
    if (!rosidl_runtime_c__String__init(&msg->name))
    {
        isaac_ros2_messages__msg__BoundingBox3D__fini(msg);
        return false;
    }
    // confidence
    // center
    if (!geometry_msgs__msg__Pose__init(&msg->center))
    {
        isaac_ros2_messages__msg__BoundingBox3D__fini(msg);
        return false;
    }
    // size
    if (!geometry_msgs__msg__Vector3__init(&msg->size))
    {
        isaac_ros2_messages__msg__BoundingBox3D__fini(msg);
        return false;
    }
    return true;
}

void isaac_ros2_messages__msg__BoundingBox3D__fini(isaac_ros2_messages__msg__BoundingBox3D* msg)
{
    if (!msg)
    {
        return;
    }
    // name
    rosidl_runtime_c__String__fini(&msg->name);
    // confidence
    // center
    geometry_msgs__msg__Pose__fini(&msg->center);
    // size
    geometry_msgs__msg__Vector3__fini(&msg->size);
}

isaac_ros2_messages__msg__BoundingBox3D* isaac_ros2_messages__msg__BoundingBox3D__create()
{
    isaac_ros2_messages__msg__BoundingBox3D* msg =
        (isaac_ros2_messages__msg__BoundingBox3D*)malloc(sizeof(isaac_ros2_messages__msg__BoundingBox3D));
    if (!msg)
    {
        return NULL;
    }
    memset(msg, 0, sizeof(isaac_ros2_messages__msg__BoundingBox3D));
    bool success = isaac_ros2_messages__msg__BoundingBox3D__init(msg);
    if (!success)
    {
        free(msg);
        return NULL;
    }
    return msg;
}

void isaac_ros2_messages__msg__BoundingBox3D__destroy(isaac_ros2_messages__msg__BoundingBox3D* msg)
{
    if (msg)
    {
        isaac_ros2_messages__msg__BoundingBox3D__fini(msg);
    }
    free(msg);
}


bool isaac_ros2_messages__msg__BoundingBox3D__Sequence__init(isaac_ros2_messages__msg__BoundingBox3D__Sequence* array,
                                                             size_t size)
{
    if (!array)
    {
        return false;
    }
    isaac_ros2_messages__msg__BoundingBox3D* data = NULL;
    if (size)
    {
        data = (isaac_ros2_messages__msg__BoundingBox3D*)calloc(size, sizeof(isaac_ros2_messages__msg__BoundingBox3D));
        if (!data)
        {
            return false;
        }
        // initialize all array elements
        size_t i;
        for (i = 0; i < size; ++i)
        {
            bool success = isaac_ros2_messages__msg__BoundingBox3D__init(&data[i]);
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
                isaac_ros2_messages__msg__BoundingBox3D__fini(&data[i - 1]);
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

void isaac_ros2_messages__msg__BoundingBox3D__Sequence__fini(isaac_ros2_messages__msg__BoundingBox3D__Sequence* array)
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
            isaac_ros2_messages__msg__BoundingBox3D__fini(&array->data[i]);
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

isaac_ros2_messages__msg__BoundingBox3D__Sequence* isaac_ros2_messages__msg__BoundingBox3D__Sequence__create(size_t size)
{
    isaac_ros2_messages__msg__BoundingBox3D__Sequence* array = (isaac_ros2_messages__msg__BoundingBox3D__Sequence*)malloc(
        sizeof(isaac_ros2_messages__msg__BoundingBox3D__Sequence));
    if (!array)
    {
        return NULL;
    }
    bool success = isaac_ros2_messages__msg__BoundingBox3D__Sequence__init(array, size);
    if (!success)
    {
        free(array);
        return NULL;
    }
    return array;
}

void isaac_ros2_messages__msg__BoundingBox3D__Sequence__destroy(isaac_ros2_messages__msg__BoundingBox3D__Sequence* array)
{
    if (array)
    {
        isaac_ros2_messages__msg__BoundingBox3D__Sequence__fini(array);
    }
    free(array);
}
