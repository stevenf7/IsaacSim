// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
//! @file
//!
//! @brief LidarProfileTypes: These are the paramater for the simulated lidar for the generic lidar plugin

#pragma once

#include <cstdint>
#include <vector>

//-----------------------------------------------------------------------------
constexpr uint32_t kMaxEmitters = 144; /**< global maximum of emitters for static emitterprofile */
constexpr uint32_t kMaxReturns = 2; /**< global maximum of returns per detector for static emitterprofile */
constexpr uint32_t kMaxLines = 500; /**< global maximum of returns per detector for static emitterprofile */
constexpr uint32_t kMaxAzimuthTicks = 8192; /**< global maximum of azimuth thicks */
constexpr uint32_t kMaxScanRates = 8; /**< global maximum of scan rates for lidar profile */
constexpr uint32_t kMaxIntensityMapElements = 400; /**< global maximum of intensity mapping elements */
constexpr uint32_t kMaxRangeCount = 4; /**< global maximum of ranges */
constexpr uint32_t kMaxEmitterStates = 4; /**< global maximum of emitter states */
constexpr float kDefaultEmitterStateResolution = 0.1f; /**< globally defined default emitter state resolution */
constexpr float kMaxEncoder = 131071.f; /**< globally defined max encoder value used in transcoder */


/**
 * Mapping Type
 */
enum LidarIntensityMapping
{
    LINEAR = 0, /**< only scaling will be applied*/
    NONLINEAR = 1, /**< nonlinear mapping of intensities based on provided quantized intensity mapping. Additionally,
                      there is one special cases: An inverted 1:1 decoder map (map elements == scaling factor) will be
                      used as an encoder map*/
    NONLINEAR_ENCODING_ONLY = 2,
    NONLINEAR_DECODING_ONLY = 3
};

/**
 * Specifies ray type of lidar simulation
 */
enum LidarRayType
{
    IDEALIZED = 0, /**< emitter is modeled as an idealized ray */
    GAUSSIAN_BEAM = 1, /**< emitter is simulated as an gaussian beam */
    UNIFORM_BEAM = 2 /**< emitter is simulated as a uniform beam */
};


/**
 * Specifies the scanning principle of the simulated lidar
 */
enum class LidarScanType : uint8_t
{
    kUnknown, /**< unknown principle, result of incorrect reading of profile */
    kRotary, /**< rotating sensors */
    kLinear, /**< linear principle */
    kSolidState, /**< solid state sensors including flash lidar */
    kNum /**< indicator for number of elements in the enum */
};

/**
 * Specifies the intensity correction method
 */
enum class LidarIntensityProcessing : uint8_t
{
    kCorrection, /**< simple correction method which removes the distance factor */
    kRaw, /**< no correction, raw intensity output scaled to fit */
    kNormalization, /**< normalized intensity output (not supported, yet) */
    kCalibrated, /**< close to true reflectance output, rigorous radimetric correction and calibration applied. (not
                    supported, yet) */
    kPointType, /**< inferred hit point type (not supported, yet) */
    kNum /**< indicator for number of elements in the enum */
};

/**
 * Emitter profile relative to lidar sensor base position
 */
struct EmitterProfile
{
    float azimuthDeg; /**< azimuth deviation in degrees */
    float elevationDeg; /**< elevation deviation in degrees */
    float vertOffsetM; /**< vertical offset of the emitter origin in m */
    float horOffsetM; /**< horizontal offset of the emitter origin in m */

    float distanceCorrectionM; /**< distance offset to sensor origin in m */
    float focalDistM; /**< focal distance in m */
    float focalSlope; /**< focal slope in m */

    uint32_t fireTimeNs; /**< firing time of emitter (delta to tick start time) in ns */
    uint32_t reportRateDiv; /**< report rate divisor */
    uint32_t bank; /**< beam bank */
    uint32_t channelId; /**< channel of beam */
    uint32_t rangeId; /**< emitter range id */
};

/**
 * Error profile for the sensor azimuth position
 */
struct ErrorProfile
{
    float std;
    float mean;
};

struct EmitterError
{
    ErrorProfile azimuth; /**< jitter for azimuth */
    ErrorProfile elevation; /**< jitter for elevation */
    ErrorProfile origin[3]; /**< jitter for origin (x,y,z) -- simulate small vibrations */
};

/**
 * EmitterRange, specifies the range [min,max] of the laser emitter in m
 */
struct EmitterRange
{
    float max; /**< maximum distance of hit point for the emitter */
    float min; /**< minimum distance of hit point for the emitter */
};

/**
 * EmitterStates, holds a static array of EmitterProfiles
 */
struct EmitterStates
{
    EmitterProfile emitterProfiles[kMaxEmitters]; /**< static array of EmitterProfiles */
};

/**
 * EmitterStatesDynamic, holds a dynamic array of EmitterProfiles
 * not used in device code...therefore can have vector inside -- vector has the advantage of automatic memory handling
 */
struct EmitterStatesDynamic
{
    std::vector<EmitterProfile> emitterProfiles; /**< dynamic array of EmitterProfiles */
};

struct AtmosProfileParam
{
    float rainRate{ 0.f }; // in mm/h  -- base parameter for atmospherics
    float rainDropHitThresh{ 0.f }; // min thresh for backscatter based random drop hit
    float alpha{ 0.f }; // alpha parameter of beta distribution
    float beta{ 0.f }; // beta parameter of beta distribution
};

struct AerosolAtmosProfileParam
{
    float aerosolModel{ -1.f }; // specifies the atmospheric model ranging from continental, rural, marine, and urban
};

struct RayFiringsParam
{
    float rangeOffset{ 0.f }; // Specifies an offset for each primary ray firing
    bool cullBackFace{ false }; // cull back facing primitives parameter
};

/**
 * BeamProfile, used for beam divergence
 */
struct BeamProfile
{
    float wavelengthNm; /**< wavelength of laser */
    float beamWaistHorM; /**< beam radius at waist */
    float beamWaistVertM; /**< beam radius at waist */
    float Msquared; /**< beam quality */
    float focusDistM; /**< Focusing distance in m, distance to beam waist */

    float divHorRad{ 0.f }; /**< beam divergence in rad, optional, if not provided, will be calculated for Gaussian
                                   beam from M2 and w0 */
    float divVertRad{ 0.f }; /**< beam divergence in rad, optional, if not provided, will be calculated for Gaussian
                                   beam from M2 and w0 */
    float aspectRatio{ 1.f }; /**< beam footprint aspect ratio, optional */
};

// DOXYGEN needs a namespace in order to handle the LidarBaseProfile derrived structs
#ifdef DOXYGEN_BUILD
namespace
{
#endif
/**
 * LidarBaseProfile, common for all types of lidar
 */
struct LidarBaseProfile
{
    LidarScanType scanType; /**< specifies the scanning principle of the simulated lidar */
    LidarIntensityProcessing intensityProcessing; /**< specifies the intensity correction method */
    LidarRayType rayType; /**< specifies the modeled ray type */
    LidarIntensityMapping intensityMapping; /**< specifies intensity mapping type */
    float intensityMapEncoding[kMaxIntensityMapElements]; /**< intensity mapping */
    uint32_t intensityMapElCountEnc;
    float intensityMapDecoding[kMaxIntensityMapElements]; /**< intensity mapping */
    uint32_t intensityMapElCountDec;
    float intensityScalePercent; /**< max intensity value in % */
    uint32_t dwId; /**< DriveWorks id  */

    float nearRangeM; /**< minimum distance of sensor in m */
    float farRangeM; /**< maximum distance of sensor in m */
    float startAzimuthDeg; /**< start azimuth of sensor fov in deg */
    float endAzimuthDeg; /**< end azimuth of sensor fov in deg */
    float validStartAzimuthDeg; /**< start azimuth in deg for capped sensor fov */
    float validEndAzimuthDeg; /**< end azimuth in deg for capped sensor fov */

    float effectiveApertureSize; /**< effective aperture size of collector in meters */
    float quantumEfficiency; /**< quantum efficiency of the detector */
    float calibrationGain; /**< gain factor that accounts for intensity calibration */
    float pixelPitch; /**< size of single detector element in microns */
    float bitDepthResolution; /**< bit depth quantization from detector */
    float reflectionPowerFraction; /**< reflection power fraction for secondary returns */
    float transmissionPowerFraction; /**< transmission power fraction for secondary returns */

    float upElevationDeg; /**< upper elevation of sensor fov in deg */
    float downElevationDeg; /**< lower azimuth of sensor fov in deg */

    float rangeResolutionM; /**< range resolution in m */
    float rangeAccuracyM; /**< range accuracy in m */

    uint32_t rangeCount; /**< number of different emitter ranges */
    EmitterRange ranges[kMaxRangeCount]; /**< static array of emitter ranges */

    float avgPowerW; /**< average power of laser in W */
    float minReflectance; /**< minimum reflectance at a specified range */
    float minReflectanceRange; /**< specified range with min reflectance */
    float minDistBetweenEchos; /**< min distance between succeeding echos */
    uint32_t pulseTimeNs; /**< laser pulse time in ns */

    BeamProfile beamProfile; /**< beam profile */

    uint32_t maxReturns; /**< maximum number of returns/echos per laser emitter */

    uint32_t scanRateBaseHz; /**< base scan rate which is the default */
    uint32_t reportRateBaseHz; /**< base frequency of one shooting of all lasers */

    // Multiple emitter can map to same channel.
    uint32_t numberOfChannels; /**< number of channels = detectors per tick/sensor position */
    uint32_t numberOfEmitters; /**< number of emitters per tick/sensor position */

    float stateResolutionStep; /**< step size between different emitter states */
    uint32_t emitterStateCount; /**< number of different emitter states */

    EmitterError emitterError; /**< error parameter for emitter */
    AtmosProfileParam weatherAtmosParam; /**< weather parameter */
    AerosolAtmosProfileParam aerosolAtmosParam; /**< aerosol parameter */
    RayFiringsParam rayFiringsParam; /**< specifies the ray firing control params */
};


/**
 * LidarRotaryProfile, profile for rotary sensor
 */
struct LidarRotaryProfile : LidarBaseProfile
{
    EmitterStates emitterStates[kMaxEmitterStates]; /**< emitter states array */
};

/**
 * LidarSolidStateProfile, profile for solid state sensor with dynamic array of emitter states
 */
struct LidarSolidStateProfile : LidarBaseProfile
{
    uint16_t numLines; /**< number of azimuth lines per full scan */
    uint16_t numRaysPerLine[kMaxLines]; /**< dynamic array of EmitterProfiles */
    EmitterStatesDynamic emitterStates[kMaxEmitterStates]; /**< dynamic emitter states array */
};

#ifdef DOXYGEN_BUILD
}
#endif
