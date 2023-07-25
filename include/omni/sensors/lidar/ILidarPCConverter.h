// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

//! @file
//!
//! @brief Utility for converting lidar sensor model buffer to a lidar point cloud

#include "LidarPoint.h"

#include <carb/IObject.h>

#include <cstdint>
#include <memory>
#include <vector>

namespace omni
{
namespace sensors
{
struct Point;
namespace lidar
{

/**
 * @brief LidarPCConverterRunMode -- describes the run mode of the conversion
 *
 */
enum LidarPCConverterRunMode
{
    CPU = 0, /**< converts on host */
    GPU = 1, /**< converts on device */
    GPU_NO_ASYNC = 2 /**< converts on device in post procssing without async */
};

/**
 * @brief LidarProfileType -- describes the type of lidar
 *
 */
enum LidarProfileType
{
    ROTARY = 0, /**< a rotating lidar */
    SOLID_STATE = 1, /**< a solid state lidar */
    NONE = 2 /**< no type given -- don't use a profile to correct measurements */
};

#pragma pack(push, 1) // Make sure we have consistent structure packing

/**
 * @brief LidarPCConverterContext -- Context data to be used in converter code
 *
 */
struct LidarPCConverterContext
{
    uint32_t numTicks{ 0 }; /**< num ticks of processed buffer */
    uint32_t numPoints{ 0 }; /**< number of converted points */
    uint32_t startPointId{ 0 }; /**< index of first point in the accumulated buffer */
    uint64_t scanStartTimeNs{ 0 }; /**< start timestamp of current scan in ns */
    uint64_t lastPointTimeNs{ 0 }; /**< timestamp of last point of the converted point cloud in ns  */
    uint32_t maxPoints{ 0 }; /**< maximum points in the point cloud buffer */
    uint32_t numVizPoints{ 0 }; /**<number of converted viz points */
    float position[3] = { 0.f, 0.f, 0.f }; /**< position to transform the converted points */
    float orientation[4] = { 0.f, 0.f, 0.f, 1.f }; /**< orientation to transform the converted points */
};

enum PointColorValue
{
    CONSTANT = 0,
    INTENSITY = 1,
    HEIGHT = 2,
    RANGE = 3,
    OBJECT = 4,
    ECHO = 5,
    MATERIAL = 6
};

struct VizPointsContainer
{
    size_t numPoints{ 0 };
    uint64_t scanStartTimeNs{ 0 };
    SensorPoseAtTime frameStart; /**< sensor transformation at frame start*/
    SensorPoseAtTime frameEnd; /**< sensor transformation at frame end*/
    omni::sensors::Point* points{ nullptr };
};

#pragma pack(pop)
/**
 * @brief LidarPCConverter interface. Users can create objects that implement this interface by acquiring the
 * ILidarPCConverterFactory carbonite interface and using the createInstance() method. The lidar pc converter converts
 * rtx sensor data stream to an easily usable point cloud.
 */
class ILidarPCConverter : public carb::IObject
{
public:
    virtual ~ILidarPCConverter(){};

    /**
     * @brief Initializes the converter (sets the profile, profile type and maximum number of points)
     * @param profile read sensor profile given as data blob
     * @param profileType profile type (ROTARY, SOLID_STATE or NONE)
     * @param runMode specify whether it is a host only or device operation conversion
     * @param maxPoints (optional) maximum number of points for accumulation, will be calculated through profile except
     * @param allocVizPoints (optional) allocate for visualizer Points (omni::sensors::Point) - this will enable
     * converting to vizPoints
     */
    virtual void init(void* profile,
                      const LidarProfileType profileType,
                      LidarPCConverterRunMode runMode,
                      uint32_t maxPoints = 0,
                      const bool allocVizPoints = false) = 0;

    /**
     * @brief Gets calculated maximum number of points
     * @return uint32_t max points
     */
    virtual uint32_t getMaxPoints() const = 0;

    /**
     * @brief Converts the rtx sensor data buffer of one trace to a LidarPointCloud
     * @param sensorBuffer the rtx sensor data buffer
     * @param rightHanded (optional) indicates if the point cloud lies in RHS coordinate system
     * @param cudaStream (optional) used for parallelizing point cloud conversion
     * @param constantValue (optional) indicate the constant value for vizPoints (for color code CONSTANT)
     * @return void
     */
    virtual void convertBuffer(uint8_t* sensorBuffer,
                               const bool rightHanded = true,
                               void* cudaStream = nullptr,
                               const float constantValue = 0) = 0;

    /**
     * @brief Tests if the dw-style packet (see SensorBinFileHeaders.h) is of a new scan
     * @param dwPacket dw-style packet (dw packet header + udp packet)
     * @return bool
     * */
    virtual bool isPacketOfNewScan(char* dwPacket) = 0;

    /**
     * @brief Converts vendor packet to point cloud (only CPU mode for now)
     * @param dwPacket vendor packet (udp packet)
     * @param lidarBinFileHeader header of dw-style bin file
     * @return void
     * */
    virtual void convertPacket(char* dwPacket, char* lidarBinFileHeader) = 0;

    /**
     * @brief Sets the transformation applied to every converted point
     * @param pos position (x,y,z) in m
     * @param rpyDeg roll, pitch and yaw in degrees
     * @param stream (optional) used for parallelizing point cloud conversion
     * @return void
     * */
    virtual void setTransformation(const float* pos, const float* rpyDeg, void* stream) = 0;

    /**
     * @brief Gets size of vendor packet
     * @return size_t
     * */
    virtual size_t sizeOfVendorPacket() const = 0;

    /**
     * @brief Sets the cudaDevice and, potentially, handles the gpu migration
     * @param cudaDevice current cuda device id
     */
    virtual void setCudaDevice(int cudaDevice) = 0;

    /**
     * @brief Gets current converted LidarPointCloud
     * @return LidarPointCloud
     */
    virtual LidarPointCloud getBuffer(const bool accumulate, const bool erase) = 0;

    /**
     * @brief Gets current converted sensors::common:Point(s) which can be used by the visualizer
     * @return VizPointsContainer
     */
    virtual VizPointsContainer getVizPoints(const bool accumulate, const bool erase) = 0;

    /**
     * @brief Gets time of the packet in nanoseconds
     * @param dwPacket packet -- could also be vendor packet
     * @return uint64_t
     * */
    virtual uint64_t getPacketTime(char* dwPacket) = 0;
};

/**
 * @brief a carb object pointer for an object that implements the ILidarPCConverter interface
 *
 */
using ILidarPCConverterPtr = carb::ObjectPtr<ILidarPCConverter>;

} // namespace lidar
} // namespace sensors
} // namespace omni
