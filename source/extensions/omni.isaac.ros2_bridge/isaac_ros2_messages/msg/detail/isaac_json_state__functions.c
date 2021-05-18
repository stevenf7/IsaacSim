// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from isaac_ros2_messages:msg/IsaacJSONState.idl
// generated code does not contain a copyright notice
#include "isaac_ros2_messages/msg/detail/isaac_json_state__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `json`
#include "rosidl_runtime_c/string_functions.h"

bool isaac_ros2_messages__msg__IsaacJSONState__init(isaac_ros2_messages__msg__IsaacJSONState* msg)
{
    if (!msg)
    {
        return false;
    }
    // header
    if (!std_msgs__msg__Header__init(&msg->header))
    {
        isaac_ros2_messages__msg__IsaacJSONState__fini(msg);
        return false;
    }
    // json
    if (!rosidl_runtime_c__String__init(&msg->json))
    {
        isaac_ros2_messages__msg__IsaacJSONState__fini(msg);
        return false;
    }
    return true;
}

void isaac_ros2_messages__msg__IsaacJSONState__fini(isaac_ros2_messages__msg__IsaacJSONState* msg)
{
    if (!msg)
    {
        return;
    }
    // header
    std_msgs__msg__Header__fini(&msg->header);
    // json
    rosidl_runtime_c__String__fini(&msg->json);
}

isaac_ros2_messages__msg__IsaacJSONState* isaac_ros2_messages__msg__IsaacJSONState__create()
{
    isaac_ros2_messages__msg__IsaacJSONState* msg =
        (isaac_ros2_messages__msg__IsaacJSONState*)malloc(sizeof(isaac_ros2_messages__msg__IsaacJSONState));
    if (!msg)
    {
        return NULL;
    }
    memset(msg, 0, sizeof(isaac_ros2_messages__msg__IsaacJSONState));
    bool success = isaac_ros2_messages__msg__IsaacJSONState__init(msg);
    if (!success)
    {
        free(msg);
        return NULL;
    }
    return msg;
}

void isaac_ros2_messages__msg__IsaacJSONState__destroy(isaac_ros2_messages__msg__IsaacJSONState* msg)
{
    if (msg)
    {
        isaac_ros2_messages__msg__IsaacJSONState__fini(msg);
    }
    free(msg);
}


bool isaac_ros2_messages__msg__IsaacJSONState__Sequence__init(isaac_ros2_messages__msg__IsaacJSONState__Sequence* array,
                                                              size_t size)
{
    if (!array)
    {
        return false;
    }
    isaac_ros2_messages__msg__IsaacJSONState* data = NULL;
    if (size)
    {
        data = (isaac_ros2_messages__msg__IsaacJSONState*)calloc(size, sizeof(isaac_ros2_messages__msg__IsaacJSONState));
        if (!data)
        {
            return false;
        }
        // initialize all array elements
        size_t i;
        for (i = 0; i < size; ++i)
        {
            bool success = isaac_ros2_messages__msg__IsaacJSONState__init(&data[i]);
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
                isaac_ros2_messages__msg__IsaacJSONState__fini(&data[i - 1]);
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

void isaac_ros2_messages__msg__IsaacJSONState__Sequence__fini(isaac_ros2_messages__msg__IsaacJSONState__Sequence* array)
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
            isaac_ros2_messages__msg__IsaacJSONState__fini(&array->data[i]);
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

isaac_ros2_messages__msg__IsaacJSONState__Sequence* isaac_ros2_messages__msg__IsaacJSONState__Sequence__create(size_t size)
{
    isaac_ros2_messages__msg__IsaacJSONState__Sequence* array =
        (isaac_ros2_messages__msg__IsaacJSONState__Sequence*)malloc(
            sizeof(isaac_ros2_messages__msg__IsaacJSONState__Sequence));
    if (!array)
    {
        return NULL;
    }
    bool success = isaac_ros2_messages__msg__IsaacJSONState__Sequence__init(array, size);
    if (!success)
    {
        free(array);
        return NULL;
    }
    return array;
}

void isaac_ros2_messages__msg__IsaacJSONState__Sequence__destroy(isaac_ros2_messages__msg__IsaacJSONState__Sequence* array)
{
    if (array)
    {
        isaac_ros2_messages__msg__IsaacJSONState__Sequence__fini(array);
    }
    free(array);
}
