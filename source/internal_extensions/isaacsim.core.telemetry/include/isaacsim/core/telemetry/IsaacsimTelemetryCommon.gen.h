// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// DO NOT MODIFY THIS FILE. This is a generated file.
// This file was generated from: isaacsim.telemetry.common.schema

//
#pragma once

#include <omni/log/ILog.h>
#include <omni/structuredlog/BinarySerializer.h>
#include <omni/structuredlog/IStructuredLog.h>
#include <omni/structuredlog/JsonTree.h>
#include <omni/structuredlog/StringView.h>

#include <memory>

namespace isaacsim
{
namespace core
{
namespace telemetry
{

/** helper macro to send the 'extensionActivated' event.
 *
 *  @param[in] extensionId_ Parameter from schema at path '/extensionId'.
 *             Extension identifier (e.g. isaacsim.sensors.experimental.rtx)
 *  @param[in] extensionVersion_ Parameter from schema at path '/extensionVersion'.
 *             Semantic version of the extension (e.g. 1.2.0)
 *  @param[in] action_ Parameter from schema at path '/action'.
 *             Lifecycle action: enabled or disabled
 *  @returns no return value.
 *
 *  @remarks Emitted when an Isaac Sim extension is enabled or disabled.
 *
 *  @sa @ref Schema_isaacsim_telemetry_common_1_0::extensionActivated_sendEvent().
 *  @sa @ref Schema_isaacsim_telemetry_common_1_0::extensionActivated_isEnabled().
 */
#define OMNI_ISAACSIM_TELEMETRY_COMMON_1_0_EXTENSIONACTIVATED(extensionId_, extensionVersion_, action_)                \
    OMNI_STRUCTURED_LOG(isaacsim::core::telemetry::Schema_isaacsim_telemetry_common_1_0::extensionActivated,           \
                        extensionId_, extensionVersion_, action_)

/** helper macro to send the 'featureUsed' event.
 *
 *  @param[in] extensionId_ Parameter from schema at path '/extensionId'.
 *             Extension that owns the feature
 *  @param[in] featureName_ Parameter from schema at path '/featureName'.
 *             Feature identifier (e.g. import_urdf, create_lidar_sensor)
 *  @param[in] featureType_ Parameter from schema at path '/featureType'.
 *             Category of usage: command, menu_item, or api_call
 *  @param[in] durationMs_ Parameter from schema at path '/durationMs'.
 *             Wall-clock duration of the operation in milliseconds, 0 if not
 *             measured
 *  @returns no return value.
 *
 *  @remarks Emitted when a user invokes a command, menu item, or significant
 *           API call.
 *
 *  @sa @ref Schema_isaacsim_telemetry_common_1_0::featureUsed_sendEvent().
 *  @sa @ref Schema_isaacsim_telemetry_common_1_0::featureUsed_isEnabled().
 */
#define OMNI_ISAACSIM_TELEMETRY_COMMON_1_0_FEATUREUSED(extensionId_, featureName_, featureType_, durationMs_)          \
    OMNI_STRUCTURED_LOG(isaacsim::core::telemetry::Schema_isaacsim_telemetry_common_1_0::featureUsed, extensionId_,    \
                        featureName_, featureType_, durationMs_)

/** helper macro to send the 'errorOccurred' event.
 *
 *  @param[in] extensionId_ Parameter from schema at path '/extensionId'.
 *             Extension where the error occurred
 *  @param[in] errorType_ Parameter from schema at path '/errorType'.
 *             Error classification (e.g. import_failure, validation_error,
 *             runtime_error)
 *  @param[in] errorMessage_ Parameter from schema at path '/errorMessage'.
 *             Human-readable error summary without user-identifying information.
 *             Must not include file paths, hostnames, usernames, or other PII.
 *  @returns no return value.
 *
 *  @remarks Emitted when a recoverable error occurs in an Isaac Sim extension.
 *
 *  @sa @ref Schema_isaacsim_telemetry_common_1_0::errorOccurred_sendEvent().
 *  @sa @ref Schema_isaacsim_telemetry_common_1_0::errorOccurred_isEnabled().
 */
#define OMNI_ISAACSIM_TELEMETRY_COMMON_1_0_ERROROCCURRED(extensionId_, errorType_, errorMessage_)                      \
    OMNI_STRUCTURED_LOG(isaacsim::core::telemetry::Schema_isaacsim_telemetry_common_1_0::errorOccurred, extensionId_,  \
                        errorType_, errorMessage_)

class Schema_isaacsim_telemetry_common_1_0
{
public:
    /** enumeration for parameter action */
    enum class Enum_extensionActivated_action : uint16_t
    {
        /** for value "enabled" */
        eEnabled,

        /** for value "disabled" */
        eDisabled,

    };

    /** enumeration for parameter featureType */
    enum class Enum_featureUsed_featureType : uint16_t
    {
        /** for value "command" */
        eCommand,

        /** for value "menu_item" */
        eMenu_item,

        /** for value "api_call" */
        eApi_call,

    };

    /** the event ID names used to send the events in this schema.  These IDs
     *  are used when the schema is first registered, and are passed to the
     *  allocEvent() function when sending the event.
     */
    enum : uint64_t
    {
        kExtensionActivatedEventId = OMNI_STRUCTURED_LOG_EVENT_ID(
            "isaacsim.telemetry.common", "com.nvidia.isaacsim.telemetry.common.extensionActivated", "1.0", "0"),
        kFeatureUsedEventId = OMNI_STRUCTURED_LOG_EVENT_ID(
            "isaacsim.telemetry.common", "com.nvidia.isaacsim.telemetry.common.featureUsed", "1.0", "0"),
        kErrorOccurredEventId = OMNI_STRUCTURED_LOG_EVENT_ID(
            "isaacsim.telemetry.common", "com.nvidia.isaacsim.telemetry.common.errorOccurred", "1.0", "0"),
    };

    Schema_isaacsim_telemetry_common_1_0() = default;

    /** Register this class with the @ref omni::structuredlog::IStructuredLog interface.
     *  @param[in] flags The flags to pass into @ref omni::structuredlog::IStructuredLog::allocSchema()
     *                   This may be zero or more of the @ref omni::structuredlog::SchemaFlags flags.
     *  @returns `true` if the operation succeeded.
     *  @returns `false` if @ref omni::structuredlog::IStructuredLog couldn't be loaded.
     *  @returns `false` if a memory allocation failed.
     */
    static bool registerSchema(omni::structuredlog::IStructuredLog* strucLog) noexcept
    {
        return _registerSchema(strucLog);
    }

    /** Check whether this structured log schema is enabled.
     *  @param[in] eventId     the ID of the event to check the enable state for.
     *                         This must be one of the @a k*EventId symbols
     *                         defined above.
     *  @returns Whether this client is enabled.
     */
    static bool isEnabled(omni::structuredlog::EventId eventId) noexcept
    {
        return _isEnabled(eventId);
    }

    /** Enable/disable an event in this schema.
     *  @param[in] eventId     the ID of the event to enable or disable.
     *                         This must be one of the @a k*EventId symbols
     *                         defined above.
     *  @param[in] enabled     Whether is enabled or disabled.
     */
    static void setEnabled(omni::structuredlog::EventId eventId, bool enabled) noexcept
    {
        _setEnabled(eventId, enabled);
    }

    /** Enable/disable this schema.
     *  @param[in] enabled     Whether is enabled or disabled.
     */
    static void setEnabled(bool enabled) noexcept
    {
        _setEnabled(enabled);
    }

    /** event enable check helper functions.
     *
     *  @param[in] strucLog   The structured log object to use to send this event.  This
     *                        must not be nullptr.  It is the caller's responsibility
     *                        to ensure that a valid object is passed in.
     *  @returns `true` if the specific event and this schema are both enabled.
     *  @returns `false` if either the specific event or this schema is disabled.
     *
     *  @remarks These check if an event corresponding to the function name is currently
     *           enabled.  These are useful to avoid parameter evaluation before calling
     *           into one of the event emitter functions.  These will be called from the
     *           OMNI_STRUCTURED_LOG() macro.  These may also be called directly if an event
     *           needs to be emitted manually, but the only effect would be the potential
     *           to avoid parameter evaluation in the *_sendEvent() function.  Each
     *           *_sendEvent() function itself will also internally check if the event
     *           is enabled before sending it.
     *  @{
     */
    static bool extensionActivated_isEnabled(omni::structuredlog::IStructuredLog* strucLog) noexcept
    {
        return strucLog->isEnabled(kExtensionActivatedEventId);
    }

    static bool featureUsed_isEnabled(omni::structuredlog::IStructuredLog* strucLog) noexcept
    {
        return strucLog->isEnabled(kFeatureUsedEventId);
    }

    static bool errorOccurred_isEnabled(omni::structuredlog::IStructuredLog* strucLog) noexcept
    {
        return strucLog->isEnabled(kErrorOccurredEventId);
    }
    /** @} */

    /** Send the event 'com.nvidia.isaacsim.telemetry.common.extensionActivated'
     *
     *  @param[in] strucLog The global structured log object to use to send
     *             this event.  This must not be nullptr.  It is the caller's
     *             responsibility to ensure a valid object is passed in.
     *  @param[in] extensionId Parameter from schema at path '/extensionId'.
     *             Extension identifier (e.g. isaacsim.sensors.experimental.rtx)
     *  @param[in] extensionVersion Parameter from schema at path '/extensionVersion'.
     *             Semantic version of the extension (e.g. 1.2.0)
     *  @param[in] action Parameter from schema at path '/action'.
     *             Lifecycle action: enabled or disabled
     *  @returns no return value.
     *
     *  @remarks Emitted when an Isaac Sim extension is enabled or disabled.
     */
    static void extensionActivated_sendEvent(omni::structuredlog::IStructuredLog* strucLog,
                                             const omni::structuredlog::StringView& extensionId,
                                             const omni::structuredlog::StringView& extensionVersion,
                                             Enum_extensionActivated_action action) noexcept
    {
        _extensionActivated_sendEvent(strucLog, extensionId, extensionVersion, action);
    }

    /** Send the event 'com.nvidia.isaacsim.telemetry.common.featureUsed'
     *
     *  @param[in] strucLog The global structured log object to use to send
     *             this event.  This must not be nullptr.  It is the caller's
     *             responsibility to ensure a valid object is passed in.
     *  @param[in] extensionId Parameter from schema at path '/extensionId'.
     *             Extension that owns the feature
     *  @param[in] featureName Parameter from schema at path '/featureName'.
     *             Feature identifier (e.g. import_urdf, create_lidar_sensor)
     *  @param[in] featureType Parameter from schema at path '/featureType'.
     *             Category of usage: command, menu_item, or api_call
     *  @param[in] durationMs Parameter from schema at path '/durationMs'.
     *             Wall-clock duration of the operation in milliseconds, 0 if not
     *             measured
     *  @returns no return value.
     *
     *  @remarks Emitted when a user invokes a command, menu item, or significant
     *           API call.
     */
    static void featureUsed_sendEvent(omni::structuredlog::IStructuredLog* strucLog,
                                      const omni::structuredlog::StringView& extensionId,
                                      const omni::structuredlog::StringView& featureName,
                                      Enum_featureUsed_featureType featureType,
                                      int64_t durationMs) noexcept
    {
        _featureUsed_sendEvent(strucLog, extensionId, featureName, featureType, durationMs);
    }

    /** Send the event 'com.nvidia.isaacsim.telemetry.common.errorOccurred'
     *
     *  @param[in] strucLog The global structured log object to use to send
     *             this event.  This must not be nullptr.  It is the caller's
     *             responsibility to ensure a valid object is passed in.
     *  @param[in] extensionId Parameter from schema at path '/extensionId'.
     *             Extension where the error occurred
     *  @param[in] errorType Parameter from schema at path '/errorType'.
     *             Error classification (e.g. import_failure, validation_error,
     *             runtime_error)
     *  @param[in] errorMessage Parameter from schema at path '/errorMessage'.
     *             Human-readable error summary without user-identifying information.
     *             Must not include file paths, hostnames, usernames, or other PII.
     *  @returns no return value.
     *
     *  @remarks Emitted when a recoverable error occurs in an Isaac Sim extension.
     */
    static void errorOccurred_sendEvent(omni::structuredlog::IStructuredLog* strucLog,
                                        const omni::structuredlog::StringView& extensionId,
                                        const omni::structuredlog::StringView& errorType,
                                        const omni::structuredlog::StringView& errorMessage) noexcept
    {
        _errorOccurred_sendEvent(strucLog, extensionId, errorType, errorMessage);
    }

private:
    /** This will allow us to disable array length checks in release builds,
     *  since they would have a negative performance impact and only be hit
     *  in unusual circumstances.
     */
    static constexpr bool kValidateLength = CARB_DEBUG;

    /** body for the registerSchema() public function. */
    static bool _registerSchema(omni::structuredlog::IStructuredLog* strucLog)
    {
        omni::structuredlog::AllocHandle handle = {};
        omni::structuredlog::SchemaResult result;
        uint8_t* buffer;
        omni::structuredlog::EventInfo events[3] = {};
        size_t bufferSize = 0;
        size_t total = 0;
        omni::structuredlog::SchemaFlags flags = 0;

        if (strucLog == nullptr)
        {
            OMNI_LOG_WARN(OMNI_LOG_DEFAULT_CHANNEL,
                          "no structured log object!  The schema "
                          "'Schema_isaacsim_telemetry_common_1_0' "
                          "will be disabled.");
            return false;
        }

        // calculate the tree sizes
        size_t extensionActivated_size = _extensionActivated_calculateTreeSize();
        size_t featureUsed_size = _featureUsed_calculateTreeSize();
        size_t errorOccurred_size = _errorOccurred_calculateTreeSize();

        // calculate the event buffer size
        bufferSize += extensionActivated_size;
        bufferSize += featureUsed_size;
        bufferSize += errorOccurred_size;

        // begin schema creation
        buffer = strucLog->allocSchema("isaacsim.telemetry.common", "1.0", flags, bufferSize, &handle);
        if (buffer == nullptr)
        {
            OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL, "allocSchema failed (size = %zu bytes)", bufferSize);
            return false;
        }

        // register all the events
        events[0].schema = _extensionActivated_buildJsonTree(extensionActivated_size, buffer + total);
        events[0].eventName = "com.nvidia.isaacsim.telemetry.common.extensionActivated";
        events[0].parserVersion = 0;
        events[0].eventId = kExtensionActivatedEventId;
        total += extensionActivated_size;
        events[1].schema = _featureUsed_buildJsonTree(featureUsed_size, buffer + total);
        events[1].eventName = "com.nvidia.isaacsim.telemetry.common.featureUsed";
        events[1].parserVersion = 0;
        events[1].eventId = kFeatureUsedEventId;
        total += featureUsed_size;
        events[2].schema = _errorOccurred_buildJsonTree(errorOccurred_size, buffer + total);
        events[2].eventName = "com.nvidia.isaacsim.telemetry.common.errorOccurred";
        events[2].parserVersion = 0;
        events[2].eventId = kErrorOccurredEventId;
        total += errorOccurred_size;

        result = strucLog->commitSchema(handle, events, CARB_COUNTOF(events));
        if (result != omni::structuredlog::SchemaResult::eSuccess &&
            result != omni::structuredlog::SchemaResult::eAlreadyExists)
        {
            OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL,
                           "failed to register structured log events "
                           "{result = %s (%zu)}",
                           getSchemaResultName(result), size_t(result));
            return false;
        }

        return true;
    }

    /** body for the isEnabled() public function. */
    static bool _isEnabled(omni::structuredlog::EventId eventId)
    {
        omni::structuredlog::IStructuredLog* strucLog = omniGetStructuredLogWithoutAcquire();
        return strucLog != nullptr && strucLog->isEnabled(eventId);
    }

    /** body for the setEnabled() public function. */
    static void _setEnabled(omni::structuredlog::EventId eventId, bool enabled)
    {
        omni::structuredlog::IStructuredLog* strucLog = omniGetStructuredLogWithoutAcquire();
        if (strucLog == nullptr)
            return;

        strucLog->setEnabled(eventId, 0, enabled);
    }

    /** body for the setEnabled() public function. */
    static void _setEnabled(bool enabled)
    {
        omni::structuredlog::IStructuredLog* strucLog = omniGetStructuredLogWithoutAcquire();
        if (strucLog == nullptr)
            return;

        strucLog->setEnabled(kExtensionActivatedEventId, omni::structuredlog::fEnableFlagWholeSchema, enabled);
    }

#if OMNI_PLATFORM_WINDOWS
#    pragma warning(push)
#    pragma warning(disable : 4127) // warning C4127: conditional expression is constant.
#endif

    /** body for the extensionActivated_sendEvent() function. */
    static void _extensionActivated_sendEvent(omni::structuredlog::IStructuredLog* strucLog,
                                              const omni::structuredlog::StringView& extensionId,
                                              const omni::structuredlog::StringView& extensionVersion,
                                              Enum_extensionActivated_action action) noexcept
    {
        omni::structuredlog::AllocHandle handle = {};

        // calculate the required buffer size for the event
        omni::structuredlog::BinaryBlobSizeCalculator calc;
        {
            if (kValidateLength && extensionId.length() + 1 > UINT16_MAX)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL,
                               "length of parameter 'extensionId' exceeds max value 65535 - "
                               "it will be truncated (size was %zu)",
                               extensionId.length() + 1);
            }

            // property extensionId
            calc.track(extensionId);

            if (kValidateLength && extensionVersion.length() + 1 > UINT16_MAX)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL,
                               "length of parameter 'extensionVersion' exceeds max value 65535 - "
                               "it will be truncated (size was %zu)",
                               extensionVersion.length() + 1);
            }

            // property extensionVersion
            calc.track(extensionVersion);

            // property uint16_t(action)
            calc.track(uint16_t(action));
        }

        // write out the event into the buffer
        void* buffer = strucLog->allocEvent(0, kExtensionActivatedEventId, 0, calc.getSize(), &handle);
        if (buffer == nullptr)
        {
            OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL,
                           "failed to allocate a %zu byte buffer for structured log event "
                           "'com.nvidia.isaacsim.telemetry.common.extensionActivated'",
                           calc.getSize());
            return;
        }

        omni::structuredlog::BlobWriter<CARB_DEBUG, _onStructuredLogValidationError> writer(buffer, calc.getSize());
        {
            // property extensionId
            writer.copy(extensionId);

            // property extensionVersion
            writer.copy(extensionVersion);

            // property uint16_t(action)
            writer.copy(uint16_t(action));
        }

        strucLog->commitEvent(handle);
    }

    /** body for the featureUsed_sendEvent() function. */
    static void _featureUsed_sendEvent(omni::structuredlog::IStructuredLog* strucLog,
                                       const omni::structuredlog::StringView& extensionId,
                                       const omni::structuredlog::StringView& featureName,
                                       Enum_featureUsed_featureType featureType,
                                       int64_t durationMs) noexcept
    {
        omni::structuredlog::AllocHandle handle = {};

        // calculate the required buffer size for the event
        omni::structuredlog::BinaryBlobSizeCalculator calc;
        {
            if (kValidateLength && extensionId.length() + 1 > UINT16_MAX)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL,
                               "length of parameter 'extensionId' exceeds max value 65535 - "
                               "it will be truncated (size was %zu)",
                               extensionId.length() + 1);
            }

            // property extensionId
            calc.track(extensionId);

            if (kValidateLength && featureName.length() + 1 > UINT16_MAX)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL,
                               "length of parameter 'featureName' exceeds max value 65535 - "
                               "it will be truncated (size was %zu)",
                               featureName.length() + 1);
            }

            // property featureName
            calc.track(featureName);

            // property uint16_t(featureType)
            calc.track(uint16_t(featureType));

            // property durationMs
            calc.track(durationMs);
        }

        // write out the event into the buffer
        void* buffer = strucLog->allocEvent(0, kFeatureUsedEventId, 0, calc.getSize(), &handle);
        if (buffer == nullptr)
        {
            OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL,
                           "failed to allocate a %zu byte buffer for structured log event "
                           "'com.nvidia.isaacsim.telemetry.common.featureUsed'",
                           calc.getSize());
            return;
        }

        omni::structuredlog::BlobWriter<CARB_DEBUG, _onStructuredLogValidationError> writer(buffer, calc.getSize());
        {
            // property extensionId
            writer.copy(extensionId);

            // property featureName
            writer.copy(featureName);

            // property uint16_t(featureType)
            writer.copy(uint16_t(featureType));

            // property durationMs
            writer.copy(durationMs);
        }

        strucLog->commitEvent(handle);
    }

    /** body for the errorOccurred_sendEvent() function. */
    static void _errorOccurred_sendEvent(omni::structuredlog::IStructuredLog* strucLog,
                                         const omni::structuredlog::StringView& extensionId,
                                         const omni::structuredlog::StringView& errorType,
                                         const omni::structuredlog::StringView& errorMessage) noexcept
    {
        omni::structuredlog::AllocHandle handle = {};

        // calculate the required buffer size for the event
        omni::structuredlog::BinaryBlobSizeCalculator calc;
        {
            if (kValidateLength && extensionId.length() + 1 > UINT16_MAX)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL,
                               "length of parameter 'extensionId' exceeds max value 65535 - "
                               "it will be truncated (size was %zu)",
                               extensionId.length() + 1);
            }

            // property extensionId
            calc.track(extensionId);

            if (kValidateLength && errorType.length() + 1 > UINT16_MAX)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL,
                               "length of parameter 'errorType' exceeds max value 65535 - "
                               "it will be truncated (size was %zu)",
                               errorType.length() + 1);
            }

            // property errorType
            calc.track(errorType);

            if (kValidateLength && errorMessage.length() + 1 > UINT16_MAX)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL,
                               "length of parameter 'errorMessage' exceeds max value 65535 - "
                               "it will be truncated (size was %zu)",
                               errorMessage.length() + 1);
            }

            // property errorMessage
            calc.track(errorMessage);
        }

        // write out the event into the buffer
        void* buffer = strucLog->allocEvent(0, kErrorOccurredEventId, 0, calc.getSize(), &handle);
        if (buffer == nullptr)
        {
            OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL,
                           "failed to allocate a %zu byte buffer for structured log event "
                           "'com.nvidia.isaacsim.telemetry.common.errorOccurred'",
                           calc.getSize());
            return;
        }

        omni::structuredlog::BlobWriter<CARB_DEBUG, _onStructuredLogValidationError> writer(buffer, calc.getSize());
        {
            // property extensionId
            writer.copy(extensionId);

            // property errorType
            writer.copy(errorType);

            // property errorMessage
            writer.copy(errorMessage);
        }

        strucLog->commitEvent(handle);
    }
#if OMNI_PLATFORM_WINDOWS
#    pragma warning(pop)
#endif

    /** Calculate JSON tree size for structured log event: com.nvidia.isaacsim.telemetry.common.extensionActivated.
     *  @returns The JSON tree size in bytes for this event.
     */
    static size_t _extensionActivated_calculateTreeSize()
    {
        // calculate the buffer size for the tree
        omni::structuredlog::JsonTreeSizeCalculator calc;
        calc.trackRoot();
        calc.trackObject(3); // object has 3 properties
        {
            // property extensionId
            calc.trackName("extensionId");
            calc.track(static_cast<const char*>(nullptr));

            // property extensionVersion
            calc.trackName("extensionVersion");
            calc.track(static_cast<const char*>(nullptr));

            // property action
            calc.trackName("action");
            {
                // Enum_extensionActivated_action maps onto this array
                static const char* const a__[] = { "enabled", "disabled" };
                calc.track(a__, uint16_t(CARB_COUNTOF(a__)));
            }
        }
        return calc.getSize();
    }

    /** Generate the JSON tree for structured log event: com.nvidia.isaacsim.telemetry.common.extensionActivated.
     *  @param[in]    bufferSize The length of @p buffer in bytes.
     *  @param[inout] buffer     The buffer to write the tree into.
     *  @returns The JSON tree for this event.
     *  @returns nullptr if a logic error occurred or @p bufferSize was too small.
     */
    static omni::structuredlog::JsonNode* _extensionActivated_buildJsonTree(size_t bufferSize, uint8_t* buffer)
    {
        CARB_MAYBE_UNUSED bool result;
        omni::structuredlog::BlockAllocator alloc(buffer, bufferSize);
        omni::structuredlog::JsonBuilder builder(&alloc);
        omni::structuredlog::JsonNode* base = static_cast<omni::structuredlog::JsonNode*>(alloc.alloc(sizeof(*base)));
        if (base == nullptr)
        {
            OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL,
                           "failed to allocate the base node for event "
                           "'com.nvidia.isaacsim.telemetry.common.extensionActivated' "
                           "{alloc size = %zu, buffer size = %zu}",
                           sizeof(*base), bufferSize);
            return nullptr;
        }
        *base = {};

        // build the tree
        result = builder.createObject(base, 3); // object has 3 properties
        if (!result)
        {
            OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL, "failed to create an object node (bad size calculation?)");
            return nullptr;
        }
        {
            // property extensionId
            result = builder.setName(&base->data.objVal[0], "extensionId");
            if (!result)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL, "failed to set the object name (bad size calculation?)");
                return nullptr;
            }
            result = builder.setNode(&base->data.objVal[0], static_cast<const char*>(nullptr));
            if (!result)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL, "failed to set type 'const char*' (shouldn't be possible)");
                return nullptr;
            }

            // property extensionVersion
            result = builder.setName(&base->data.objVal[1], "extensionVersion");
            if (!result)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL, "failed to set the object name (bad size calculation?)");
                return nullptr;
            }
            result = builder.setNode(&base->data.objVal[1], static_cast<const char*>(nullptr));
            if (!result)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL, "failed to set type 'const char*' (shouldn't be possible)");
                return nullptr;
            }

            // property action
            result = builder.setName(&base->data.objVal[2], "action");
            if (!result)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL, "failed to set the object name (bad size calculation?)");
                return nullptr;
            }
            {
                // Enum_extensionActivated_action maps onto this array
                static const char* const a__[] = { "enabled", "disabled" };
                result = builder.setNode(&base->data.objVal[2], a__, uint16_t(CARB_COUNTOF(a__)));
                if (!result)
                {
                    OMNI_LOG_ERROR(
                        OMNI_LOG_DEFAULT_CHANNEL, "failed to set an array of length 2 (bad size calculation?)");
                    return nullptr;
                }
            }
            result = omni::structuredlog::JsonBuilder::setFlags(
                &base->data.objVal[2], omni::structuredlog::JsonNode::fFlagEnum);
            if (!result)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL, "failed to set flag 'omni::structuredlog::JsonNode::fFlagEnum'");
                return nullptr;
            }
        }

        return base;
    }

    /** Calculate JSON tree size for structured log event: com.nvidia.isaacsim.telemetry.common.featureUsed.
     *  @returns The JSON tree size in bytes for this event.
     */
    static size_t _featureUsed_calculateTreeSize()
    {
        // calculate the buffer size for the tree
        omni::structuredlog::JsonTreeSizeCalculator calc;
        calc.trackRoot();
        calc.trackObject(4); // object has 4 properties
        {
            // property extensionId
            calc.trackName("extensionId");
            calc.track(static_cast<const char*>(nullptr));

            // property featureName
            calc.trackName("featureName");
            calc.track(static_cast<const char*>(nullptr));

            // property featureType
            calc.trackName("featureType");
            {
                // Enum_featureUsed_featureType maps onto this array
                static const char* const a__[] = { "command", "menu_item", "api_call" };
                calc.track(a__, uint16_t(CARB_COUNTOF(a__)));
            }

            // property durationMs
            calc.trackName("durationMs");
            calc.track(int64_t(0));
        }
        return calc.getSize();
    }

    /** Generate the JSON tree for structured log event: com.nvidia.isaacsim.telemetry.common.featureUsed.
     *  @param[in]    bufferSize The length of @p buffer in bytes.
     *  @param[inout] buffer     The buffer to write the tree into.
     *  @returns The JSON tree for this event.
     *  @returns nullptr if a logic error occurred or @p bufferSize was too small.
     */
    static omni::structuredlog::JsonNode* _featureUsed_buildJsonTree(size_t bufferSize, uint8_t* buffer)
    {
        CARB_MAYBE_UNUSED bool result;
        omni::structuredlog::BlockAllocator alloc(buffer, bufferSize);
        omni::structuredlog::JsonBuilder builder(&alloc);
        omni::structuredlog::JsonNode* base = static_cast<omni::structuredlog::JsonNode*>(alloc.alloc(sizeof(*base)));
        if (base == nullptr)
        {
            OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL,
                           "failed to allocate the base node for event "
                           "'com.nvidia.isaacsim.telemetry.common.featureUsed' "
                           "{alloc size = %zu, buffer size = %zu}",
                           sizeof(*base), bufferSize);
            return nullptr;
        }
        *base = {};

        // build the tree
        result = builder.createObject(base, 4); // object has 4 properties
        if (!result)
        {
            OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL, "failed to create an object node (bad size calculation?)");
            return nullptr;
        }
        {
            // property extensionId
            result = builder.setName(&base->data.objVal[0], "extensionId");
            if (!result)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL, "failed to set the object name (bad size calculation?)");
                return nullptr;
            }
            result = builder.setNode(&base->data.objVal[0], static_cast<const char*>(nullptr));
            if (!result)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL, "failed to set type 'const char*' (shouldn't be possible)");
                return nullptr;
            }

            // property featureName
            result = builder.setName(&base->data.objVal[1], "featureName");
            if (!result)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL, "failed to set the object name (bad size calculation?)");
                return nullptr;
            }
            result = builder.setNode(&base->data.objVal[1], static_cast<const char*>(nullptr));
            if (!result)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL, "failed to set type 'const char*' (shouldn't be possible)");
                return nullptr;
            }

            // property featureType
            result = builder.setName(&base->data.objVal[2], "featureType");
            if (!result)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL, "failed to set the object name (bad size calculation?)");
                return nullptr;
            }
            {
                // Enum_featureUsed_featureType maps onto this array
                static const char* const a__[] = { "command", "menu_item", "api_call" };
                result = builder.setNode(&base->data.objVal[2], a__, uint16_t(CARB_COUNTOF(a__)));
                if (!result)
                {
                    OMNI_LOG_ERROR(
                        OMNI_LOG_DEFAULT_CHANNEL, "failed to set an array of length 3 (bad size calculation?)");
                    return nullptr;
                }
            }
            result = omni::structuredlog::JsonBuilder::setFlags(
                &base->data.objVal[2], omni::structuredlog::JsonNode::fFlagEnum);
            if (!result)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL, "failed to set flag 'omni::structuredlog::JsonNode::fFlagEnum'");
                return nullptr;
            }

            // property durationMs
            result = builder.setName(&base->data.objVal[3], "durationMs");
            if (!result)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL, "failed to set the object name (bad size calculation?)");
                return nullptr;
            }
            result = builder.setNode(&base->data.objVal[3], int64_t(0));
            if (!result)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL, "failed to set type 'int64_t' (shouldn't be possible)");
                return nullptr;
            }
        }

        return base;
    }

    /** Calculate JSON tree size for structured log event: com.nvidia.isaacsim.telemetry.common.errorOccurred.
     *  @returns The JSON tree size in bytes for this event.
     */
    static size_t _errorOccurred_calculateTreeSize()
    {
        // calculate the buffer size for the tree
        omni::structuredlog::JsonTreeSizeCalculator calc;
        calc.trackRoot();
        calc.trackObject(3); // object has 3 properties
        {
            // property extensionId
            calc.trackName("extensionId");
            calc.track(static_cast<const char*>(nullptr));

            // property errorType
            calc.trackName("errorType");
            calc.track(static_cast<const char*>(nullptr));

            // property errorMessage
            calc.trackName("errorMessage");
            calc.track(static_cast<const char*>(nullptr));
        }
        return calc.getSize();
    }

    /** Generate the JSON tree for structured log event: com.nvidia.isaacsim.telemetry.common.errorOccurred.
     *  @param[in]    bufferSize The length of @p buffer in bytes.
     *  @param[inout] buffer     The buffer to write the tree into.
     *  @returns The JSON tree for this event.
     *  @returns nullptr if a logic error occurred or @p bufferSize was too small.
     */
    static omni::structuredlog::JsonNode* _errorOccurred_buildJsonTree(size_t bufferSize, uint8_t* buffer)
    {
        CARB_MAYBE_UNUSED bool result;
        omni::structuredlog::BlockAllocator alloc(buffer, bufferSize);
        omni::structuredlog::JsonBuilder builder(&alloc);
        omni::structuredlog::JsonNode* base = static_cast<omni::structuredlog::JsonNode*>(alloc.alloc(sizeof(*base)));
        if (base == nullptr)
        {
            OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL,
                           "failed to allocate the base node for event "
                           "'com.nvidia.isaacsim.telemetry.common.errorOccurred' "
                           "{alloc size = %zu, buffer size = %zu}",
                           sizeof(*base), bufferSize);
            return nullptr;
        }
        *base = {};

        // build the tree
        result = builder.createObject(base, 3); // object has 3 properties
        if (!result)
        {
            OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL, "failed to create an object node (bad size calculation?)");
            return nullptr;
        }
        {
            // property extensionId
            result = builder.setName(&base->data.objVal[0], "extensionId");
            if (!result)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL, "failed to set the object name (bad size calculation?)");
                return nullptr;
            }
            result = builder.setNode(&base->data.objVal[0], static_cast<const char*>(nullptr));
            if (!result)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL, "failed to set type 'const char*' (shouldn't be possible)");
                return nullptr;
            }

            // property errorType
            result = builder.setName(&base->data.objVal[1], "errorType");
            if (!result)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL, "failed to set the object name (bad size calculation?)");
                return nullptr;
            }
            result = builder.setNode(&base->data.objVal[1], static_cast<const char*>(nullptr));
            if (!result)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL, "failed to set type 'const char*' (shouldn't be possible)");
                return nullptr;
            }

            // property errorMessage
            result = builder.setName(&base->data.objVal[2], "errorMessage");
            if (!result)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL, "failed to set the object name (bad size calculation?)");
                return nullptr;
            }
            result = builder.setNode(&base->data.objVal[2], static_cast<const char*>(nullptr));
            if (!result)
            {
                OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL, "failed to set type 'const char*' (shouldn't be possible)");
                return nullptr;
            }
        }

        return base;
    }

    /** The callback that is used to report validation errors.
     *  @param[in] s The validation error message.
     */
    static void _onStructuredLogValidationError(const char* s)
    {
        OMNI_LOG_ERROR(OMNI_LOG_DEFAULT_CHANNEL, "error sending a structured log event: %s", s);
    }
};

// asserts to ensure that no one's modified our dependencies
static_assert(omni::structuredlog::BlobWriter<>::kVersion == 0, "BlobWriter version changed");
static_assert(omni::structuredlog::JsonNode::kVersion == 0, "JsonNode version changed");
static_assert(sizeof(omni::structuredlog::JsonNode) == 24, "unexpected size");
static_assert(std::is_standard_layout<omni::structuredlog::JsonNode>::value, "this type needs to be ABI safe");
static_assert(offsetof(omni::structuredlog::JsonNode, type) == 0, "struct layout changed");
static_assert(offsetof(omni::structuredlog::JsonNode, flags) == 1, "struct layout changed");
static_assert(offsetof(omni::structuredlog::JsonNode, len) == 2, "struct layout changed");
static_assert(offsetof(omni::structuredlog::JsonNode, nameLen) == 4, "struct layout changed");
static_assert(offsetof(omni::structuredlog::JsonNode, name) == 8, "struct layout changed");
static_assert(offsetof(omni::structuredlog::JsonNode, data) == 16, "struct layout changed");

} // namespace telemetry
} // namespace core
} // namespace isaacsim

OMNI_STRUCTURED_LOG_ADD_SCHEMA(isaacsim::core::telemetry::Schema_isaacsim_telemetry_common_1_0,
                               isaacsim_telemetry_common,
                               1_0,
                               0);
