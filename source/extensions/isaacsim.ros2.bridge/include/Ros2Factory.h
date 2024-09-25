// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

/** @file
 * @brief Factory that contains the class definitions and methods for creating ROS 2 entities according to the sourced
 * ROS 2 distribution.
 */
#pragma once

#include <include/Ros2QoS.h>
#include <nlohmann/json.hpp>
#include <omni/fabric/Type.h>
#include <omni/isaac/utils/Math.h>

#include <DynamicControl.h>
#include <LibraryLoader.h>
#include <memory>
#include <string>
#include <vector>

namespace isaacsim
{
namespace ros2
{
namespace bridge
{

/**
 * Enumerations of ROS 2 message types
 */
enum class BackendMessageType : uint8_t
{
    eMessage = 0, //!< Topic message.
    eRequest, //!< Service request (`_Request`).
    eResponse, //!< Service response (`_Response`).
    eGoal, //!< Action goal (`_Goal`).
    eResult, //!< Action result (`_Result`).
    eFeedback, //!< Action feedback (`_Feedback`).
    eSendGoalRequest, //!< Action goal request (`_SendGoal_Request`).
    eSendGoalResponse, //!< Action goal response (`_SendGoal_Response`).
    eFeedbackMessage, //!< Action feedback (`_FeedbackMessage`).
    eGetResultRequest, //!< Action result request (`_GetResult_Request`).
    eGetResultResponse, //!< Action result response (`_GetResult_Response`).
};

/**
 * Struct that encapsulates a dynamic message field
 */
struct DynamicMessageField
{
    std::string name; //!< Field name. Hierarchical names (e.g.: MESSAGE fields are unrolled and concatenated by `:`).
    uint8_t rosType; //!< ROS data type.
                     // https://github.com/ros2/rosidl/blob/humble/rosidl_typesupport_introspection_c/include/rosidl_typesupport_introspection_c/field_types.h
    bool isArray; //!< Whether the field is an array.
    std::string ognType; //!< OmniGraph data type name.
                         // https://docs.omniverse.nvidia.com/kit/docs/omni.graph.docs/latest/dev/ogn/attribute_types.html
    omni::fabric::BaseDataType dataType; //!< Fabric data type.

    /**
     * Generate a list of field names in hierarchical manner.
     *
     * @param delimiter Delimiter used to split the name.
     * @returns List of field names in hierarchical manner.
     */
    std::vector<std::string> names(char delimiter = ':')
    {
        std::vector<std::string> fieldNames;
        std::stringstream stringStream(name);
        std::string segment;
        while (std::getline(stringStream, segment, delimiter))
            fieldNames.push_back(segment);
        return fieldNames;
    }
};

/**
 * Struct that encapsulates `geometry_msgs/msg/TransformStamped` data for tf
 */
struct TfTransformStamped
{
    double timeStamp; //!< Time (seconds).
    std::string parentFrame; //!< Transform frame with which this data is associated.
    std::string childFrame; //!< Frame ID of the child frame to which this transform points.

    // translation components
    double translation_x; //!< Translation of child frame from parent frame (x-axis).
    double translation_y; //!< Translation of child frame from parent frame (y-axis).
    double translation_z; //!< Translation of child frame from parent frame (z-axis).

    // quaternion components
    double rotation_x; //!< Rotation of child frame from parent frame (quaternion x-component).
    double rotation_y; //!< Rotation of child frame from parent frame (quaternion y-component).
    double rotation_z; //!< Rotation of child frame from parent frame (quaternion z-component).
    double rotation_w; //!< Rotation of child frame from parent frame (quaternion w-component).
};

/**
 * Base class for all ROS 2 message encapsulations.
 */
class Ros2Message
{
public:
    /**
     * Get the message pointer.
     *
     * @returns The pointer to the message if it has been created and initialized properly, otherwise `nullptr`.
     */
    void* getPtr()
    {
        return m_msg;
    }

    /**
     * Get the pointer to the struct that contains the ROS IDL message type support data.
     *
     * The pointer points to a ROS IDL struct if the message if founded.
     *
     * Message type | ROS IDL struct
     * --- | ---
     * Topic (Message) | `rosidl_message_type_support_t`
     * Service | `rosidl_service_type_support_t`
     * Action | `rosidl_action_type_support_t`
     *
     * @returns The pointer to the struct, otherwise `nullptr`.
     */
    virtual const void* getTypeSupportHandle() = 0;

protected:
    void* m_msg = nullptr; //!< Message pointer.
};

/**
 * Class implementing dynamic ROS 2 messages
 *
 * This class allows to define and use ROS 2 message types at runtime, rather than at compile time.
 *
 * \warning Processing the message as JSON has a significative computation overhead compared to processing it as a
 * vector.
 */
class Ros2DynamicMessage : public Ros2Message
{
public:
    /**
     * Generate a human-readable summary of the dynamic message structure and print it (configurable)
     *
     * \code{.unparsed}
     * Message: sensor_msgs/msg/PointCloud2 (topic | message)
     * Idx Array ROS type                  OGN type                  Name
     * === ===== ========================= ========================= ====
     * 0   no    INT32 (int32_t)           eInt (int32_t)            header:stamp:sec
     * 1   no    UINT32 (uint32_t)         eUInt (uint32_t)          header:stamp:nanosec
     * 2   no    STRING (std::string)      eToken (std::string)      header:frame_id
     * 3   no    UINT32 (uint32_t)         eUInt (uint32_t)          height
     * 4   no    UINT32 (uint32_t)         eUInt (uint32_t)          width
     * 5   yes   MESSAGE (nlohmann::json)  eUnknown (nlohmann::json) fields
     * 6   no    BOOLEAN (bool)            eBool (bool)              is_bigendian
     * 7   no    UINT32 (uint32_t)         eUInt (uint32_t)          point_step
     * 8   no    UINT32 (uint32_t)         eUInt (uint32_t)          row_step
     * 9   yes   UINT8 (uint8_t)           eUInt (uint32_t)          data
     * 10  no    BOOLEAN (bool)            eBool (bool)              is_dense
     * \endcode
     *
     * @param print Whether to print the human-readable structure of the dynamic message to the console.
     * @returns A human-readable tabular structure of the dynamic message.
     */
    virtual std::string generateSummary(bool print) = 0;

    /**
     * Read the message fields value and return them contained in a JSON object.
     *
     * @returns Message data as JSON.
     */
    virtual const nlohmann::json& readData() = 0;

    /**
     * Read the message fields value and return them contained in a vector of shared pointers object.
     *
     * @param asOgnType Whether the pointers point to OmniGraph or ROS 2 specific data types.
     * @returns Message data as vector of shared pointers.
     */
    virtual const std::vector<std::shared_ptr<void>>& readData(bool asOgnType) = 0;

    /**
     * Write the message fields value from a JSON object.
     *
     * @param data Message data as JSON.
     */
    virtual void writeData(const nlohmann::json& data) = 0;

    /**
     * Write the message fields value from a vector of shared pointers object.
     *
     * @param data Message data as vector of shared pointers object.
     * @param fromOgnType Whether the pointers point to OmniGraph or ROS 2 specific data types.
     */
    virtual void writeData(const std::vector<std::shared_ptr<void>>& data, bool fromOgnType) = 0;

    /**
     * Get the dynamic message fields description (\ref DynamicMessageField).
     *
     * @returns Message fields description.
     */
    const std::vector<DynamicMessageField>& getMessageFields()
    {
        return m_messagesFields;
    };

    /**
     * Get the dynamic message container as vector of shared pointers.
     *
     * The vector container is a constant vector of non-constant shared pointers.
     * This means that the elements of the vector (the message fields) cannot be modified but their content
     * (the message fields' value) can. This is particularly useful when writing the message data using a vector
     * as a container since it is not necessary to create pointers to the required data types.
     * See \ref Ros2DynamicMessage::writeData for use example.
     *
     * @param asOgnType Whether the pointers point to OmniGraph or ROS 2 specific data types.
     * @returns Message container as vector of shared pointers.
     */
    const std::vector<std::shared_ptr<void>>& getVectorContainer(bool asOgnType)
    {
        return asOgnType ? m_messageVectorOgnContainer : m_messageVectorRosContainer;
    };

    /**
     * Check whether the ROS 2 message has been created and initialized properly.
     *
     * @returns Whether the ROS 2 message has been created and initialized properly.
     */
    bool isValid()
    {
        return m_msg != nullptr;
    }

protected:
    std::vector<DynamicMessageField> m_messagesFields; //!< Message fields description.
    nlohmann::json m_messageJsonContainer; //!< Message container as JSON.
    std::vector<std::shared_ptr<void>> m_messageVectorRosContainer; //!< Message container as ROS 2-specific data types
                                                                    //!< vector.
    std::vector<std::shared_ptr<void>> m_messageVectorOgnContainer; //!< Message container as OmniGraph-specific data
                                                                    //!< types vector.
};

/**
 * Base class that encapsulates a non-global state of an ROS init/shutdown cycle (`rcl_context_t`) instance used in the
 * creation of ROS 2 nodes and other entities.
 */
class Ros2ContextHandle
{
public:
    /**
     * Get the pointer to the ROS 2 context `rcl_context_t` struct.
     *
     * @returns Pointer to the context.
     */
    virtual void* getContext() = 0;

    /**
     * Initialize `rcl` and the context
     *
     * @param argc Number of strings in argv.
     * @param argv Command line arguments.
     * @param setDomainId Whether to set the ROS domain ID. If true, the specified value will override the
     * `ROS_DOMAIN_ID` environment variable.
     * @param domainId ROS domain ID.
     */
    virtual void init(int argc, char const* const* argv, bool setDomainId = false, size_t domainId = 0) = 0;

    /**
     * Check whether the object holds a valid ROS 2 context instance.
     *
     * @returns Whether the object holds a valid ROS 2 context instance.
     */
    virtual bool isValid() = 0;

    /**
     * Shutdown the `rcl` context.
     *
     * @param shutdownReason An optional human-readable string that documents the shutdown reason.
     * @returns True if the shutdown was completed successfully, false otherwise.
     */
    virtual bool shutdown(const char* shutdownReason = nullptr) = 0;
};

/**
 * Base class that encapsulates a ROS 2 node (`rcl_node_t`) instance.
 */
class Ros2NodeHandle
{
public:
    /**
     * Get the pointer to the context handler (\ref Ros2ContextHandle) object.
     *
     * @returns Pointer to the context handler.
     */
    virtual Ros2ContextHandle* getContextHandle() = 0;

    /**
     * Get the pointer to the ROS 2 `rcl_node_t` struct.
     *
     * @returns Pointer to the node.
     */
    virtual void* getNode() = 0;
};

/**
 * Base class for ROS 2 publishers.
 */
class Ros2Publisher
{
public:
    /**
     * Send a message to the topic.
     *
     * @param msg Message pointer.
     */
    virtual void publish(const void* msg) = 0;

    /**
     * Get the number of existing subscriptions to the publisher topic.
     *
     * @returns Number of subscriptions.
     */
    virtual size_t getSubscriptionCount() = 0;

    /**
     * Check whether the object holds a valid ROS 2 publisher instance.
     *
     * @returns Whether the object holds a valid ROS 2 publisher instance.
     */
    virtual bool isValid() = 0;
};

/**
 * Base class for ROS 2 subscribers.
 */
class Ros2Subscriber
{
public:
    /**
     * Do subscription work to take an incoming message from the topic, if any.
     *
     * @param msg Pointer to store the message content, if a message has been received and taken.
     * @returns True if there is a message and it has been taken without error, false otherwise.
     */
    virtual bool spin(void* msg) = 0;

    /**
     * Check whether the object holds a valid ROS 2 subscriber instance.
     *
     * @returns Whether the object holds a valid ROS 2 subscriber instance.
     */
    virtual bool isValid() = 0;
};

/**
 * Base class for ROS 2 service servers.
 */
class Ros2Service
{
public:
    /**
     * Do service work to take an incoming request message from the topic, if any.
     *
     * @param requestMsg Pointer to store the message content, if a request message has been received and taken.
     * @returns True if there is a request message and it has been taken without error, false otherwise.
     */
    virtual bool takeRequest(void* requestMsg) = 0;

    /**
     * Send a response message to the topic.
     *
     * @param responseMsg Message pointer.
     * @returns True if the response message was sent without error, false otherwise.
     */
    virtual bool sendResponse(void* responseMsg) = 0;

    /**
     * Check whether the object holds a valid ROS 2 service server instance.
     *
     * @returns Whether the object holds a valid ROS 2 service server instance.
     */
    virtual bool isValid() = 0;
};

/**
 * Base class for ROS 2 service clients.
 */
class Ros2Client
{
public:
    /**
     * Send a request message to the topic.
     *
     * @param requestMsg Message pointer.
     * @returns True if the request message was sent without error, false otherwise.
     */
    virtual bool sendRequest(void* requestMsg) = 0;

    /**
     * Do client work to take an incoming response message from the topic, if any.
     *
     * @param responseMsg Pointer to store the message content, if a response message has been received and taken.
     * @returns True if there is a response message and it has been taken without error, false otherwise.
     */
    virtual bool takeResponse(void* responseMsg) = 0;

    /**
     * Check whether the object holds a valid ROS 2 service client instance.
     *
     * @returns Whether the object holds a valid ROS 2 service client instance.
     */
    virtual bool isValid() = 0;
};

/**
 * Base class for ROS 2 message definition/generation via ROS Interface Definition Language (IDL).
 */
class Ros2MessageInterface
{
public:
    /**
     * Constructor.
     *
     * @param pkgName Message package name (e.g.: `"std_msgs"` for `std_msgs/msg/Int32`).
     * @param msgSubfolder Message subfolder name (e.g.: `"msg"` for `std_msgs/msg/Int32`).
     * @param msgName Message name (e.g.: `"Int32"` for `std_msgs/msg/Int32`).
     * @param messageType Message type.
     * @param showLoadingError Whether to print ROS IDL libraries load errors to the console.
     */
    Ros2MessageInterface(std::string pkgName,
                         std::string msgSubfolder,
                         std::string msgName,
                         BackendMessageType messageType = BackendMessageType::eMessage,
                         bool showLoadingError = false)
        : m_pkgName(pkgName), m_msgSubfolder(msgSubfolder), m_msgName(msgName), m_msgType(messageType)
    {
        m_generatorLibrary = std::make_shared<omni::isaac::utils::LibraryLoader>(
            std::string(m_pkgName) + "__rosidl_generator_c", "", showLoadingError);
        m_typesupportLibrary = std::make_shared<omni::isaac::utils::LibraryLoader>(
            std::string(m_pkgName) + "__rosidl_typesupport_c", "", showLoadingError);
        m_typesupportIntrospectionLibrary = std::make_shared<omni::isaac::utils::LibraryLoader>(
            std::string(m_pkgName) + "__rosidl_typesupport_introspection_c", "", showLoadingError);
    }

    /**
     * Get the pointer to the struct that contains the ROS IDL message type support data.
     *
     * The pointer points to a ROS IDL struct if the message if founded.
     * It is resolved by calling the `rosidl_typesupport_c` type support handle symbol for the given message name.
     *
     * Message type | ROS IDL struct
     * --- | ---
     * Topic (Message) | `rosidl_message_type_support_t`
     * Service | `rosidl_service_type_support_t`
     * Action | `rosidl_action_type_support_t`
     *
     * @returns The pointer to the struct, otherwise `nullptr`.
     */
    void* getTypeSupportHandleDynamic()
    {
        return m_typesupportLibrary->callSymbol<void*>("rosidl_typesupport_c__get_" + getTypeSupportSpec(false) +
                                                       "_type_support_handle__" + std::string(m_pkgName) + "__" +
                                                       std::string(m_msgSubfolder) + "__" + std::string(m_msgName));
    }

    /**
     * Get the pointer to the struct that contains the ROS IDL struct used to describe a single interface type.
     *
     * The pointer points to a ROS IDL struct if the message if founded.
     * It is resolved by calling the `rosidl_typesupport_introspection_c` type support handle symbol for the given
     * message name and type.
     *
     * Message type | ROS IDL struct
     * --- | ---
     * Topic (Message) | `rosidl_message_type_support_t`
     * Service | `rosidl_service_type_support_t`
     * Action | `rosidl_message_type_support_t`
     *
     * @returns The pointer to the struct, otherwise `nullptr`.
     */
    void* getTypeSupportIntrospectionHandleDynamic()
    {
        return m_typesupportIntrospectionLibrary->callSymbol<void*>(
            "rosidl_typesupport_introspection_c__get_" + getTypeSupportSpec(true) + "_type_support_handle__" +
            std::string(m_pkgName) + "__" + std::string(m_msgSubfolder) + "__" + std::string(m_msgName) +
            getMessageSpec(true));
    }

    /**
     * Create the ROS 2 message
     *
     * This method creates/allocates the memory for the message and initializes it.
     * The pointer is resolved by calling the `rosidl_generator_c` `__create` symbol for the given message.
     *
     * @returns The pointer to the created message, otherwise `nullptr`.
     */
    void* create()
    {
        return m_generatorLibrary->callSymbol<void*>(std::string(m_pkgName) + "__" + std::string(m_msgSubfolder) +
                                                     "__" + std::string(m_msgName) + getMessageSpec(false) + "__create");
    }

    /**
     * Destroy the ROS 2 message
     *
     * This method finalizes the message by freeing its allocated memory.
     * The pointer is resolved by calling the `rosidl_generator_c` `__destroy` symbol for the given message.
     *
     * @param msg The pointer to the message.
     */
    template <typename T>
    void destroy(T msg)
    {
        if (!msg)
            return;
        m_generatorLibrary->callSymbolWithArg<void>(std::string(m_pkgName) + "__" + std::string(m_msgSubfolder) + "__" +
                                                        std::string(m_msgName) + getMessageSpec(false) + "__destroy",
                                                    msg);
    }

protected:
    std::string m_pkgName; //!< Message package name.
    std::string m_msgSubfolder; //!< Message subfolder name.
    std::string m_msgName; //!< Message name.
    BackendMessageType m_msgType; //!< Message type.
    std::shared_ptr<omni::isaac::utils::LibraryLoader> m_typesupportIntrospectionLibrary; //!< ROS IDL type support
                                                                                          //!< introspection library.
    std::shared_ptr<omni::isaac::utils::LibraryLoader> m_typesupportLibrary; //!< ROS IDL type support library.
    std::shared_ptr<omni::isaac::utils::LibraryLoader> m_generatorLibrary; //!< ROS IDL generator library.

private:
    std::string getTypeSupportSpec(const bool& introspection)
    {
        switch (BackendMessageType(m_msgType))
        {
        case BackendMessageType::eMessage:
            return "message";
        case BackendMessageType::eRequest:
        case BackendMessageType::eResponse:
            return "service";
        case BackendMessageType::eGoal:
        case BackendMessageType::eResult:
        case BackendMessageType::eFeedback:
        case BackendMessageType::eSendGoalRequest:
        case BackendMessageType::eSendGoalResponse:
        case BackendMessageType::eFeedbackMessage:
        case BackendMessageType::eGetResultRequest:
        case BackendMessageType::eGetResultResponse:
            return introspection ? "message" : "action";
        default:
            break;
        }
        return "";
    }
    std::string getMessageSpec(const bool& introspection)
    {
        switch (BackendMessageType(m_msgType))
        {
        case BackendMessageType::eMessage:
            return "";
        case BackendMessageType::eRequest:
            return introspection ? "" : "_Request";
        case BackendMessageType::eResponse:
            return introspection ? "" : "_Response";
        case BackendMessageType::eGoal:
            return "_Goal";
        case BackendMessageType::eResult:
            return "_Result";
        case BackendMessageType::eFeedback:
            return "_Feedback";
        case BackendMessageType::eSendGoalRequest:
            return "_SendGoal_Request";
        case BackendMessageType::eSendGoalResponse:
            return "_SendGoal_Response";
        case BackendMessageType::eFeedbackMessage:
            return "_FeedbackMessage";
        case BackendMessageType::eGetResultRequest:
            return "_GetResult_Request";
        case BackendMessageType::eGetResultResponse:
            return "_GetResult_Response";
        default:
            break;
        }
        return "";
    }
};

/**
 * Class implementing a `rosgraph_msgs/msg/Clock` message.
 */
class Ros2ClockMessage : public Ros2Message
{
public:
    /**
     * Read the message field values.
     *
     * @param timeStamp Time (seconds).
     */
    virtual void readData(double& timeStamp) = 0;

    /**
     * Write the message field values from the given arguments.
     *
     * @param timeStamp Time (seconds).
     */
    virtual void writeData(double timeStamp) = 0;
};

/**
 * Class implementing a `sensor_msgs/msg/Imu` message.
 */
class Ros2ImuMessage : public Ros2Message
{
public:
    /**
     * Write the message header.
     *
     * @param timeStamp Time (seconds).
     * @param frameId Transform frame with which this data is associated.
     */
    virtual void writeHeader(double timeStamp, std::string& frameId) = 0;

    /**
     * Write the `linear_acceleration` or its covariance.
     *
     * @param covariance If true, only the element 0 of the associated covariance matrix will be written to -1, not the
     * acceleration (regardless of its value). If false, the acceleration values will be written.
     * @param acceleration Linear acceleration.
     */
    virtual void writeAcceleration(bool covariance = false,
                                   const std::vector<double>& acceleration = std::vector<double>()) = 0;

    /**
     * Write the `angular_velocity` or its covariance.
     *
     * @param covariance If true, only the element 0 of the associated covariance matrix will be written to -1, not the
     * velocity (regardless of its value). If false, the velocity values will be written.
     * @param velocity Angular velocity.
     */
    virtual void writeVelocity(bool covariance = false, const std::vector<double>& velocity = std::vector<double>()) = 0;

    /**
     * Write the `orientation` or its covariance.
     *
     * @param covariance If true, only the element 0 of the associated covariance matrix will be written to -1, not the
     * orientation (regardless of its value). If false, the orientation values will be written.
     * @param orientation Orientation.
     */
    virtual void writeOrientation(bool covariance = false,
                                  const std::vector<double>& orientation = std::vector<double>()) = 0;
};

/**
 * Class implementing a `sensor_msgs/msg/CameraInfo` message.
 */
class Ros2CameraInfoMessage : public Ros2Message
{
public:
    /**
     * Write the message header.
     *
     * @param timeStamp Time (seconds).
     * @param frameId Transform frame with which this data is associated.
     */
    virtual void writeHeader(const double timeStamp, const std::string& frameId) = 0;

    /**
     * Write the image dimensions (resolution).
     *
     * @param height Image height.
     * @param width Image width.
     */
    virtual void writeResolution(const uint32_t height, const uint32_t width) = 0;

    /**
     * Write the intrinsic camera matrix (`K`).
     *
     * @param array Flattened intrinsic camera matrix.
     * @param arraySize Array size.
     */
    virtual void writeIntrinsicMatrix(const double array[], const int arraySize) = 0;

    /**
     * Write the projection/camera matrix (`P`).
     *
     * @param array Flattened projection/camera matrix.
     * @param arraySize Array size.
     */
    virtual void writeProjectionMatrix(const double array[], const int arraySize) = 0;

    /**
     * Write the rectification matrix (`R`).
     *
     * @param array Flattened rectification matrix.
     * @param arraySize Array size.
     */
    virtual void writeRectificationMatrix(const double array[], const int arraySize) = 0;

    /**
     * Write the distortion parameters (`D`).
     *
     * @param array Distortion parameters (size depending on the distortion model).
     * @param distortionModel Distortion model.
     */
    virtual void writeDistortionParameters(std::vector<double>& array, const std::string& distortionModel) = 0;
};

/**
 * Class implementing a `sensor_msgs/msg/Image` message.
 */
class Ros2ImageMessage : public Ros2Message
{
public:
    /**
     * Write the message header.
     *
     * @param timeStamp Time (seconds).
     * @param frameId Transform frame with which this data is associated.
     */
    virtual void writeHeader(const double timeStamp, const std::string& frameId) = 0;

    /**
     * Generate the buffer (matrix data) according to the image metadata.
     *
     * It allocates memory for the `data` field, and computes and fills in the values of the other message fields.
     *
     * @param height Image height.
     * @param width Image width.
     * @param encoding Encoding of pixels.
     */
    virtual void generateBuffer(const uint32_t height, const uint32_t width, const std::string& encoding) = 0;

    /**
     * Get the pointer to the buffer (matrix data).
     *
     * @returns Pointer to the buffer.
     */
    void* getBufferPtr()
    {
        return &m_buffer[0];
    }

    /**
     * Get the total size (`step * height`) of the buffer, in bytes.
     *
     * @returns Buffer size.
     */
    size_t getTotalBytes()
    {
        return m_totalBytes;
    }

protected:
    std::vector<uint8_t> m_buffer; //!< Buffer (matrix data).
    size_t m_totalBytes = 0; //!< Buffer size.
};

/**
 * Class implementing a `isaac_ros_nitros_bridge_interfaces/msg/NitrosBridgeImage` message.
 */
class Ros2NitrosBridgeImageMessage : public Ros2Message
{
public:
    /**
     * Write the message header.
     *
     * @param timeStamp Time (seconds).
     * @param frameId Transform frame with which this data is associated.
     */
    virtual void writeHeader(const double timeStamp, const std::string& frameId) = 0;

    /**
     * Compute and fill in the values of the other message fields.
     *
     * This method is named the same as \ref Ros2ImageMessage::generateBuffer for compatibility.
     * Since the NitrosBridgeImage message does not define a buffer, no memory allocation is performed.
     * It only computes and fills in the values of the other message fields.
     *
     * @param height Image height.
     * @param width Image width.
     * @param encoding Encoding of pixels.
     */
    virtual void generateBuffer(const uint32_t height, const uint32_t width, const std::string& encoding) = 0;

    /**
     * Write the `data` field.
     *
     * @param data Calling process ID and the CUDA memory block file-descriptor.
     */
    virtual void writeData(const std::vector<int32_t>& data) = 0;

    /**
     * Get the pointer to the buffer.
     *
     * This method is named the same as \ref Ros2ImageMessage::getBufferPtr for compatibility.
     * Since the NitrosBridgeImage message does not define a buffer, it always return `nullptr`.
     *
     * @returns `nullptr`.
     */
    void* getBufferPtr()
    {
        return nullptr;
    }

    /**
     * Get the total size (`step * height`) of the buffer, in bytes.
     *
     * @returns Buffer size.
     */
    size_t getTotalBytes()
    {
        return m_totalBytes;
    }

protected:
    size_t m_totalBytes = 0; //!< Buffer size.
    std::vector<int32_t> m_imageData; //!< Calling process ID and the CUDA memory block file-descriptor.
};

/**
 * Class implementing a `vision_msgs/msg/Detection2DArray` message.
 */
class Ros2BoundingBox2DMessage : public Ros2Message
{
public:
    /**
     * Write the message header.
     *
     * @param timeStamp Time (seconds).
     * @param frameId Transform frame with which this data is associated.
     */
    virtual void writeHeader(const double timeStamp, const std::string& frameId) = 0;

    /**
     * Write the message field values from the given arguments.
     *
     * @param bboxArray Array of `Bbox2DData` struct.
     * @param numBoxes Number of boxed defined in the array.
     */
    virtual void writeBboxData(const void* bboxArray, size_t numBoxes) = 0;
};

/**
 * Class implementing a `vision_msgs/msg/Detection3DArray` message.
 */
class Ros2BoundingBox3DMessage : public Ros2Message
{
public:
    /**
     * Write the message header.
     *
     * @param timeStamp Time (seconds).
     * @param frameId Transform frame with which this data is associated.
     */
    virtual void writeHeader(const double timeStamp, const std::string& frameId) = 0;

    /**
     * Write the message field values from the given arguments.
     *
     * @param bboxArray Array of `Bbox3DData` struct.
     * @param numBoxes Number of boxed defined in the array.
     */
    virtual void writeBboxData(const void* bboxArray, size_t numBoxes) = 0;
};

/**
 * Class implementing a `sensor_msgs/msg/JointState` message.
 */
class Ros2JointStateMessage : public Ros2Message
{
public:
    /**
     * Write the message field values from the given arguments.
     *
     * @param timeStamp Time (seconds).
     * @param dynamicControlPtr DynamicControl interface.
     * @param articulationHandle DynamicControl's articulation handler.
     * @param stage USD stage.
     * @param dofProperties Vector to storage the articulation DOF properties.
     * @param previousJointPosition Vector to storage the previous joint positions.
     * @param calculatedJointVelocity Vector to storage the computed joint velocities.
     * @param dt Time delta for computing the joint velocities.
     * @param stageUnits Unit scale of the stage.
     */
    virtual void writeData(const double& timeStamp,
                           omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr,
                           omni::isaac::dynamic_control::DcHandle articulationHandle,
                           pxr::UsdStageWeakPtr stage,
                           std::vector<omni::isaac::dynamic_control::DcDofProperties>& dofProperties,
                           std::vector<float>& previousJointPosition,
                           std::vector<float>& calculatedJointVelocity,
                           const double& dt,
                           const double& stageUnits) = 0;

    /**
     * Read the message field values.
     *
     * The size of the arrays to store the joint positions, velocities, and efforts must be equal to the number of
     * joints (see \ref Ros2JointStateMessage::getNumJoints) of the message before calling this method.
     *
     * @param jointNames Joint names.
     * @param jointPositions Joint positions.
     * @param jointVelocities Joint velocities.
     * @param jointEfforts Joint efforts.
     * @param timeStamp Time (seconds).
     */
    virtual void readData(std::vector<char*>& jointNames,
                          double* jointPositions,
                          double* jointVelocities,
                          double* jointEfforts,
                          double& timeStamp) = 0;

    /**
     * Get the number of joints in the message.
     *
     * The size of the `name` field array is used as the number of joints.
     *
     * @returns Number of joints.
     */
    virtual size_t getNumJoints() = 0;

    /**
     * Check that the message field arrays (joint names, positions, velocities, and efforts) have the same size.
     *
     * @returns Whether the message field arrays have the same size.
     */
    virtual bool checkValid() = 0;
};

/**
 * Class implementing a `sensor_msgs/msg/LaserScan` message.
 */
class Ros2LaserScanMessage : public Ros2Message
{
public:
    /**
     * Write the message field values from the given arguments.
     *
     * @param timeStamp Time (seconds).
     * @param frameId Transform frame with which this data is associated.
     * @param azimuthRange Start (`angle_min`) and end (`angle_max`) angles of the scan in degrees.
     * @param rotationRate Scan frequency in Hz (`1 / scan_time`).
     * @param depthRange Minimum (`range_min`) and maximum (`range_max`) range values.
     * @param buffSize Range and intensities array sizes.
     * @param rangeData Range array.
     * @param intensitiesData Intensities array.
     * @param horizontalResolution Angular distance (`angle_increment`) between measurements in degrees.
     * @param horizontalFov Horizontal field of view (`360 * time_increment * ranges.size / scan_time`) in degrees.
     */
    virtual void writeData(const double& timeStamp,
                           const std::string& frameId,
                           const pxr::GfVec2f& azimuthRange,
                           const float& rotationRate,
                           const pxr::GfVec2f& depthRange,
                           size_t buffSize,
                           float* rangeData,
                           float* intensitiesData,
                           float horizontalResolution,
                           float horizontalFov) = 0;
};

/**
 * Class implementing a `nav_msgs/msg/Odometry` message.
 */
class Ros2OdometryMessage : public Ros2Message
{
public:
    /**
     * Write the message header.
     *
     * @param timeStamp Time (seconds).
     * @param frameId Transform frame with which this data is associated.
     */
    virtual void writeHeader(const double timeStamp, const std::string& frameId) = 0;

    /**
     * Write the message field values from the given arguments.
     *
     * @param childFrame Frame id the pose points to.
     * @param linearVelocity Linear velocity.
     * @param angularVelocity Angular velocity.
     * @param robotFront Front normalized vector.
     * @param robotSide Side normalized vector.
     * @param unitScale Unit scale of the stage.
     * @param zUp Whether the stage is z-axis up.
     * @param position Position.
     * @param orientation Orientation.
     */
    virtual void writeData(std::string& childFrame,
                           const pxr::GfVec3d& linearVelocity,
                           const pxr::GfVec3d& angularVelocity,
                           const pxr::GfVec3f& robotFront,
                           const pxr::GfVec3f& robotSide,
                           double unitScale,
                           bool zUp,
                           const pxr::GfVec3d& position,
                           const pxr::GfQuatd& orientation) = 0;
};

/**
 * Class implementing a `sensor_msgs/msg/PointCloud2` message.
 */
class Ros2PointCloudMessage : public Ros2Message
{
public:
    /**
     * Generate the buffer (data) according to the point cloud metadata.
     *
     * It allocates memory for the `data` field, and computes and fills in the values of the other message fields.
     *
     * @param timeStamp Time (seconds).
     * @param frameId Transform frame with which this data is associated.
     * @param height Point cloud height.
     * @param width Point cloud width.
     * @param pointStep Length of a point in bytes.
     */
    virtual void generateBuffer(const double& timeStamp,
                                const std::string& frameId,
                                const size_t& width,
                                const size_t& height,
                                const uint32_t& pointStep) = 0;

    /**
     * Get the pointer to the buffer (data).
     *
     * @returns Pointer to the buffer.
     */
    void* getBufferPtr()
    {
        return &m_buffer[0];
    }

    /**
     * Get the total size (`width * point_step`) of the buffer, in bytes.
     *
     * @returns Buffer size.
     */
    size_t getTotalBytes()
    {
        return m_totalBytes;
    }

protected:
    std::vector<uint8_t> m_buffer; //!< Buffer (data).
    size_t m_totalBytes = 0; //!< Buffer size.
};

/**
 * Class implementing a `tf2_msgs/msg/TFMessage` message with only one transform.
 */
class Ros2RawTfTreeMessage : public Ros2Message
{
public:
    /**
     * Write the message field values from the given arguments.
     *
     * @param timeStamp Time (seconds).
     * @param frameId Transform frame with which this data is associated.
     * @param childFrame Frame ID of the child frame to which this transform points.
     * @param translation Translation of child frame from header frame.
     * @param rotation Rotation of child frame from header frame.
     */
    virtual void writeData(const double timeStamp,
                           const std::string& frameId,
                           const std::string& childFrame,
                           const pxr::GfVec3d& translation,
                           const pxr::GfQuatd& rotation) = 0;
};

/**
 * Class implementing a `std_msgs/msg/String` message for semantic label.
 */
class Ros2SemanticLabelMessage : public Ros2Message
{
public:
    /**
     * Write the message field values from the given arguments.
     *
     * @param data String data.
     */
    virtual void writeData(const std::string& data) = 0;
};

/**
 * Class implementing a `geometry_msgs/msg/Twist`.
 */
class Ros2TwistMessage : public Ros2Message
{
public:
    /**
     * Read the message field values.
     *
     * @param linearVelocity Linear velocity.
     * @param angularVelocity Angular velocity.
     */
    virtual void readData(pxr::GfVec3d& linearVelocity, pxr::GfVec3d& angularVelocity) = 0;
};

/**
 * Class implementing a `ackermann_msgs/msg/AckermannDriveStamped`.
 */
class Ros2AckermannDriveStampedMessage : public Ros2Message
{
public:
    /**
     * Write the message header.
     *
     * @param timeStamp Time (seconds).
     * @param frameId Transform frame with which this data is associated.
     */
    virtual void writeHeader(const double timeStamp, const std::string& frameId) = 0;

    /**
     * Read the message field values.
     *
     * @param timeStamp Time (seconds).
     * @param frameId Transform frame with which this data is associated.
     * @param steeringAngle Virtual angle.
     * @param steeringAngleVelocity Rate of change.
     * @param speed Forward speed.
     * @param acceleration Acceleration.
     * @param jerk Jerk.
     */
    virtual void readData(double& timeStamp,
                          std::string& frameId,
                          double& steeringAngle,
                          double& steeringAngleVelocity,
                          double& speed,
                          double& acceleration,
                          double& jerk) = 0;

    /**
     * Write the message field values from the given arguments.
     *
     * @param steeringAngle Virtual angle.
     * @param steeringAngleVelocity Rate of change.
     * @param speed Forward speed.
     * @param acceleration Acceleration.
     * @param jerk Jerk.
     */
    virtual void writeData(const double& steeringAngle,
                           const double& steeringAngleVelocity,
                           const double& speed,
                           const double& acceleration,
                           const double& jerk) = 0;
};

/**
 * Class implementing a `tf2_msgs/msg/TFMessage` message.
 */
class Ros2TfTreeMessage : public Ros2Message
{
public:
    /**
     * Write the message field values from the given arguments.
     *
     * @param timeStamp Time (seconds).
     * @param transforms Transforms.
     */
    virtual void writeData(const double& timeStamp, std::vector<TfTransformStamped>& transforms) = 0;

    /**
     * Read the message field values.
     *
     * @param transforms Transforms.
     */
    virtual void readData(std::vector<TfTransformStamped>& transforms) = 0;
};

/**
 * Base class for creating ROS 2 related functions/objects according to the sourced ROS 2 distribution.
 */
class Ros2Factory
{
public:
    /**
     * Destructor.
     */
    virtual ~Ros2Factory() = default;

    /**
     * Create a ROS 2 context handler.
     *
     * @returns Pointer to the context handler.
     */
    virtual std::shared_ptr<Ros2ContextHandle> createContextHandle() = 0;

    /**
     * Create a ROS 2 node handler.
     *
     * @param name Name of the node.
     * @param namespaceName Namespace of the node.
     * @param contextHandle Context handler.
     * @returns Pointer to the node handler.
     */
    virtual std::shared_ptr<Ros2NodeHandle> createNodeHandle(const char* name,
                                                             const char* namespaceName,
                                                             Ros2ContextHandle* contextHandle) = 0;

    /**
     * Create a ROS 2 publisher.
     *
     * @param nodeHandle Node handler.
     * @param topicName Name of the topic to publish on.
     * @param typeSupport Message type support.
     * @param qos Quality of service profile.
     * @returns Pointer to the publisher.
     */
    virtual std::shared_ptr<Ros2Publisher> createPublisher(Ros2NodeHandle* nodeHandle,
                                                           const char* topicName,
                                                           const void* typeSupport,
                                                           const Ros2QoSProfile& qos) = 0;

    /**
     * Create a ROS 2 subscriber.
     *
     * @param nodeHandle Node handler.
     * @param topicName Name of the topic to subscribe to.
     * @param typeSupport Message type support.
     * @param qos Quality of Service profile.
     * @returns Pointer to the subscriber.
     */
    virtual std::shared_ptr<Ros2Subscriber> createSubscriber(Ros2NodeHandle* nodeHandle,
                                                             const char* topicName,
                                                             const void* typeSupport,
                                                             const Ros2QoSProfile& qos) = 0;

    /**
     * Create a ROS 2 service server.
     *
     * @param nodeHandle Node handler.
     * @param serviceName Name of the service.
     * @param typeSupport Message type support.
     * @param qos Quality of Service profile.
     * @returns Pointer to the service server.
     */
    virtual std::shared_ptr<Ros2Service> createService(Ros2NodeHandle* nodeHandle,
                                                       const char* serviceName,
                                                       const void* typeSupport,
                                                       const Ros2QoSProfile& qos) = 0;

    /**
     * Create a ROS 2 service client.
     *
     * @param nodeHandle Node handler.
     * @param serviceName Name of the service.
     * @param typeSupport Message type support.
     * @param qos Quality of Service profile.
     * @returns Pointer to the service client.
     */
    virtual std::shared_ptr<Ros2Client> createClient(Ros2NodeHandle* nodeHandle,
                                                     const char* serviceName,
                                                     const void* typeSupport,
                                                     const Ros2QoSProfile& qos) = 0;

    /**
     * Create a ROS 2 `rosgraph_msgs/msg/Clock` message.
     *
     * @returns Pointer to the message.
     */
    virtual std::shared_ptr<Ros2ClockMessage> createClockMessage() = 0;

    /**
     * Create a ROS 2 `sensor_msgs/msg/Imu` message.
     *
     * @returns Pointer to the message.
     */
    virtual std::shared_ptr<Ros2ImuMessage> createImuMessage() = 0;

    /**
     * Create a ROS 2 `sensor_msgs/msg/CameraInfo` message.
     *
     * @returns Pointer to the message.
     */
    virtual std::shared_ptr<Ros2CameraInfoMessage> createCameraInfoMessage() = 0;

    /**
     * Create a ROS 2 `sensor_msgs/msg/Image` message.
     *
     * @returns Pointer to the message.
     */
    virtual std::shared_ptr<Ros2ImageMessage> createImageMessage() = 0;

    /**
     * Create a ROS 2 `isaac_ros_nitros_bridge_interfaces/msg/NitrosBridgeImage` message.
     *
     * @returns Pointer to the message.
     */
    virtual std::shared_ptr<Ros2NitrosBridgeImageMessage> createNitrosBridgeImageMessage() = 0;

    /**
     * Create a ROS 2 `vision_msgs/msg/Detection2DArray` message.
     *
     * @returns Pointer to the message.
     */
    virtual std::shared_ptr<Ros2BoundingBox2DMessage> createBoundingBox2DMessage() = 0;

    /**
     * Create a ROS 2 `vision_msgs/msg/Detection3DArray` message.
     *
     * @returns Pointer to the message.
     */
    virtual std::shared_ptr<Ros2BoundingBox3DMessage> createBoundingBox3DMessage() = 0;

    /**
     * Create a ROS 2 `nav_msgs/msg/Odometry` message.
     *
     * @returns Pointer to the message.
     */
    virtual std::shared_ptr<Ros2OdometryMessage> createOdometryMessage() = 0;

    /**
     * Create a ROS 2 `tf2_msgs/msg/TFMessage` message.
     *
     * @returns Pointer to the message.
     */
    virtual std::shared_ptr<Ros2RawTfTreeMessage> createRawTfTreeMessage() = 0;

    /**
     * Create a ROS 2 `std_msgs/msg/String` message as semantic label.
     *
     * @returns Pointer to the message.
     */
    virtual std::shared_ptr<Ros2SemanticLabelMessage> createSemanticLabelMessage() = 0;

    /**
     * Create a ROS 2 `sensor_msgs/msg/JointState` message.
     *
     * @returns Pointer to the message.
     */
    virtual std::shared_ptr<Ros2JointStateMessage> createJointStateMessage() = 0;

    /**
     * Create a ROS 2 `sensor_msgs/msg/PointCloud2` message.
     *
     * @returns Pointer to the message.
     */
    virtual std::shared_ptr<Ros2PointCloudMessage> createPointCloudMessage() = 0;

    /**
     * Create a ROS 2 `sensor_msgs/msg/LaserScan` message.
     *
     * @returns Pointer to the message.
     */
    virtual std::shared_ptr<Ros2LaserScanMessage> createLaserScanMessage() = 0;

    /**
     * Create a ROS 2 `tf2_msgs/msg/TFMessage` message.
     *
     * @returns Pointer to the message.
     */
    virtual std::shared_ptr<Ros2TfTreeMessage> createTfTreeMessage() = 0;

    /**
     * Create a ROS 2 `geometry_msgs/msg/Twist` message.
     *
     * @returns Pointer to the message.
     */
    virtual std::shared_ptr<Ros2TwistMessage> createTwistMessage() = 0;

    /**
     * Create a ROS 2 `ackermann_msgs/msg/AckermannDriveStamped` message.
     *
     * @returns Pointer to the message.
     */
    virtual std::shared_ptr<Ros2AckermannDriveStampedMessage> createAckermannDriveStampedMessage() = 0;

    /**
     * Create a ROS 2 dynamic message.
     *
     * @param pkgName Message package name (e.g.: `"std_msgs"` for `std_msgs/msg/Int32`).
     * @param msgSubfolder Message subfolder name (e.g.: `"msg"` for `std_msgs/msg/Int32`).
     * @param msgName Message name (e.g.: `"Int32"` for `std_msgs/msg/Int32`).
     * @param messageType Message type.
     * @returns Pointer to the dynamic message.
     */
    virtual std::shared_ptr<Ros2Message> createDynamicMessage(
        const std::string& pkgName,
        const std::string& msgSubfolder,
        const std::string& msgName,
        BackendMessageType messageType = BackendMessageType::eMessage) = 0;

    /**
     * Determine if the given topic name is valid.
     *
     * @param topicName Topic name.
     * @returns Whether the topic name is valid.
     */
    virtual bool validateTopicName(const std::string& topicName) = 0;

    /**
     * Determine if the given node namespace name is valid.
     *
     * @param namespaceName Namespace name.
     * @returns Whether the node namespace name is valid.
     */
    virtual bool validateNamespaceName(const std::string& namespaceName) = 0;

    /**
     * Determine if the given node name is valid.
     *
     * @param nodeName Node name.
     * @returns Whether the node name is valid.
     */
    virtual bool validateNodeName(const std::string& nodeName) = 0;
};

} // namespace bridge
} // namespace ros2
} // namespace isaacsim
