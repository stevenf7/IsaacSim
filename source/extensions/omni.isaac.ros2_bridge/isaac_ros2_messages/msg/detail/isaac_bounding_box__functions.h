// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from isaac_ros2_messages:msg/IsaacBoundingBox.idl
// generated code does not contain a copyright notice

#ifndef ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX__FUNCTIONS_H_
#define ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include "isaac_ros2_messages/msg/detail/isaac_bounding_box__struct.h"
#include "isaac_ros2_messages/msg/rosidl_generator_c__visibility_control.h"
#include "rosidl_runtime_c/visibility_control.h"

#include <stdbool.h>
#include <stdlib.h>

    /// Initialize msg/IsaacBoundingBox message.
    /**
     * If the init function is called twice for the same message without
     * calling fini inbetween previously allocated memory will be leaked.
     * \param[in,out] msg The previously allocated message pointer.
     * Fields without a default value will not be initialized by this function.
     * You might want to call memset(msg, 0, sizeof(
     * isaac_ros2_messages__msg__IsaacBoundingBox
     * )) before or use
     * isaac_ros2_messages__msg__IsaacBoundingBox__create()
     * to allocate and initialize the message.
     * \return true if initialization was successful, otherwise false
     */
    ROSIDL_GENERATOR_C_PUBLIC_isaac_ros2_messages bool isaac_ros2_messages__msg__IsaacBoundingBox__init(
        isaac_ros2_messages__msg__IsaacBoundingBox* msg);

    /// Finalize msg/IsaacBoundingBox message.
    /**
     * \param[in,out] msg The allocated message pointer.
     */
    ROSIDL_GENERATOR_C_PUBLIC_isaac_ros2_messages void isaac_ros2_messages__msg__IsaacBoundingBox__fini(
        isaac_ros2_messages__msg__IsaacBoundingBox* msg);

    /// Create msg/IsaacBoundingBox message.
    /**
     * It allocates the memory for the message, sets the memory to zero, and
     * calls
     * isaac_ros2_messages__msg__IsaacBoundingBox__init().
     * \return The pointer to the initialized message if successful,
     * otherwise NULL
     */
    ROSIDL_GENERATOR_C_PUBLIC_isaac_ros2_messages isaac_ros2_messages__msg__IsaacBoundingBox* isaac_ros2_messages__msg__IsaacBoundingBox__create();

    /// Destroy msg/IsaacBoundingBox message.
    /**
     * It calls
     * isaac_ros2_messages__msg__IsaacBoundingBox__fini()
     * and frees the memory of the message.
     * \param[in,out] msg The allocated message pointer.
     */
    ROSIDL_GENERATOR_C_PUBLIC_isaac_ros2_messages void isaac_ros2_messages__msg__IsaacBoundingBox__destroy(
        isaac_ros2_messages__msg__IsaacBoundingBox* msg);


    /// Initialize array of msg/IsaacBoundingBox messages.
    /**
     * It allocates the memory for the number of elements and calls
     * isaac_ros2_messages__msg__IsaacBoundingBox__init()
     * for each element of the array.
     * \param[in,out] array The allocated array pointer.
     * \param[in] size The size / capacity of the array.
     * \return true if initialization was successful, otherwise false
     * If the array pointer is valid and the size is zero it is guaranteed
     # to return true.
     */
    ROSIDL_GENERATOR_C_PUBLIC_isaac_ros2_messages bool isaac_ros2_messages__msg__IsaacBoundingBox__Sequence__init(
        isaac_ros2_messages__msg__IsaacBoundingBox__Sequence* array, size_t size);

    /// Finalize array of msg/IsaacBoundingBox messages.
    /**
     * It calls
     * isaac_ros2_messages__msg__IsaacBoundingBox__fini()
     * for each element of the array and frees the memory for the number of
     * elements.
     * \param[in,out] array The initialized array pointer.
     */
    ROSIDL_GENERATOR_C_PUBLIC_isaac_ros2_messages void isaac_ros2_messages__msg__IsaacBoundingBox__Sequence__fini(
        isaac_ros2_messages__msg__IsaacBoundingBox__Sequence* array);

    /// Create array of msg/IsaacBoundingBox messages.
    /**
     * It allocates the memory for the array and calls
     * isaac_ros2_messages__msg__IsaacBoundingBox__Sequence__init().
     * \param[in] size The size / capacity of the array.
     * \return The pointer to the initialized array if successful, otherwise NULL
     */
    ROSIDL_GENERATOR_C_PUBLIC_isaac_ros2_messages isaac_ros2_messages__msg__IsaacBoundingBox__Sequence*
    isaac_ros2_messages__msg__IsaacBoundingBox__Sequence__create(size_t size);

    /// Destroy array of msg/IsaacBoundingBox messages.
    /**
     * It calls
     * isaac_ros2_messages__msg__IsaacBoundingBox__Sequence__fini()
     * on the array,
     * and frees the memory of the array.
     * \param[in,out] array The initialized array pointer.
     */
    ROSIDL_GENERATOR_C_PUBLIC_isaac_ros2_messages void isaac_ros2_messages__msg__IsaacBoundingBox__Sequence__destroy(
        isaac_ros2_messages__msg__IsaacBoundingBox__Sequence* array);

#ifdef __cplusplus
}
#endif

#endif // ISAAC_ROS2_MESSAGES__MSG__DETAIL__ISAAC_BOUNDING_BOX__FUNCTIONS_H_
