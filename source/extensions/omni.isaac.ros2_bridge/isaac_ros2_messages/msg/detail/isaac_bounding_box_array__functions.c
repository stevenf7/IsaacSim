// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from isaac_ros2_messages:msg/IsaacBoundingBoxArray.idl
// generated code does not contain a copyright notice
#include "isaac_ros2_messages/msg/detail/isaac_bounding_box_array__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `bboxes`
#include "isaac_ros2_messages/msg/detail/isaac_bounding_box__functions.h"

bool isaac_ros2_messages__msg__IsaacBoundingBoxArray__init(isaac_ros2_messages__msg__IsaacBoundingBoxArray* msg)
{
    if (!msg)
    {
        return false;
    }
    // header
    if (!std_msgs__msg__Header__init(&msg->header))
    {
        isaac_ros2_messages__msg__IsaacBoundingBoxArray__fini(msg);
        return false;
    }
    // bboxes
    if (!isaac_ros2_messages__msg__IsaacBoundingBox__Sequence__init(&msg->bboxes, 0))
    {
        isaac_ros2_messages__msg__IsaacBoundingBoxArray__fini(msg);
        return false;
    }
    return true;
}

void isaac_ros2_messages__msg__IsaacBoundingBoxArray__fini(isaac_ros2_messages__msg__IsaacBoundingBoxArray* msg)
{
    if (!msg)
    {
        return;
    }
    // header
    std_msgs__msg__Header__fini(&msg->header);
    // bboxes
    isaac_ros2_messages__msg__IsaacBoundingBox__Sequence__fini(&msg->bboxes);
}

isaac_ros2_messages__msg__IsaacBoundingBoxArray* isaac_ros2_messages__msg__IsaacBoundingBoxArray__create()
{
    isaac_ros2_messages__msg__IsaacBoundingBoxArray* msg =
        (isaac_ros2_messages__msg__IsaacBoundingBoxArray*)malloc(sizeof(isaac_ros2_messages__msg__IsaacBoundingBoxArray));
    if (!msg)
    {
        return NULL;
    }
    memset(msg, 0, sizeof(isaac_ros2_messages__msg__IsaacBoundingBoxArray));
    bool success = isaac_ros2_messages__msg__IsaacBoundingBoxArray__init(msg);
    if (!success)
    {
        free(msg);
        return NULL;
    }
    return msg;
}

void isaac_ros2_messages__msg__IsaacBoundingBoxArray__destroy(isaac_ros2_messages__msg__IsaacBoundingBoxArray* msg)
{
    if (msg)
    {
        isaac_ros2_messages__msg__IsaacBoundingBoxArray__fini(msg);
    }
    free(msg);
}


bool isaac_ros2_messages__msg__IsaacBoundingBoxArray__Sequence__init(
    isaac_ros2_messages__msg__IsaacBoundingBoxArray__Sequence* array, size_t size)
{
    if (!array)
    {
        return false;
    }
    isaac_ros2_messages__msg__IsaacBoundingBoxArray* data = NULL;
    if (size)
    {
        data = (isaac_ros2_messages__msg__IsaacBoundingBoxArray*)calloc(
            size, sizeof(isaac_ros2_messages__msg__IsaacBoundingBoxArray));
        if (!data)
        {
            return false;
        }
        // initialize all array elements
        size_t i;
        for (i = 0; i < size; ++i)
        {
            bool success = isaac_ros2_messages__msg__IsaacBoundingBoxArray__init(&data[i]);
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
                isaac_ros2_messages__msg__IsaacBoundingBoxArray__fini(&data[i - 1]);
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

void isaac_ros2_messages__msg__IsaacBoundingBoxArray__Sequence__fini(
    isaac_ros2_messages__msg__IsaacBoundingBoxArray__Sequence* array)
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
            isaac_ros2_messages__msg__IsaacBoundingBoxArray__fini(&array->data[i]);
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

isaac_ros2_messages__msg__IsaacBoundingBoxArray__Sequence* isaac_ros2_messages__msg__IsaacBoundingBoxArray__Sequence__create(
    size_t size)
{
    isaac_ros2_messages__msg__IsaacBoundingBoxArray__Sequence* array =
        (isaac_ros2_messages__msg__IsaacBoundingBoxArray__Sequence*)malloc(
            sizeof(isaac_ros2_messages__msg__IsaacBoundingBoxArray__Sequence));
    if (!array)
    {
        return NULL;
    }
    bool success = isaac_ros2_messages__msg__IsaacBoundingBoxArray__Sequence__init(array, size);
    if (!success)
    {
        free(array);
        return NULL;
    }
    return array;
}

void isaac_ros2_messages__msg__IsaacBoundingBoxArray__Sequence__destroy(
    isaac_ros2_messages__msg__IsaacBoundingBoxArray__Sequence* array)
{
    if (array)
    {
        isaac_ros2_messages__msg__IsaacBoundingBoxArray__Sequence__fini(array);
    }
    free(array);
}
