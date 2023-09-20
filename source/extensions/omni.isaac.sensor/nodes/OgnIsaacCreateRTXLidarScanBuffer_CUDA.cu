// Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include <cuda.h>
#include <stdint.h>
#include <stdio.h>

#define DEG2RAD(deg) ((deg) / 180.f * 3.14159265358979323846f)
#define RAD2DEG(rad) ((rad) / 3.14159265358979323846f * 180.f)

// uses the destination and a scrath area to compte and store for use computing pc
// const float azimuthDeg = 360.f - lidarReturns.azimuths[idx] + accuracyErrorAzimuthDeg;
// const float azimuthRad{ Deg2Rad(azimuthDeg) };
// const float sinAzimuth{ ::sinf(azimuthRad) };
// const float cosAzimuth{ ::cosf(azimuthRad) };
// if (point.azimuth > Deg2Rad(180.f))
//     point.azimuth -= Deg2Rad(360.f);
// srcDest computes final azimuth
// scratch.x = sinAzimuth
// scratch.y = conAzimuth
__global__ void azimuthRightHandedKernel(float* srcDest, float3* scratch, float accuracyError, int N)
{
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= N)
        return;
    srcDest[idx] = DEG2RAD(srcDest[idx] + accuracyError);
    // order of next two is order in original code.
    const float azimuthRad = 2.f * 3.14159265358979323846f - srcDest[idx];
    if (srcDest[idx] > 3.14159265358979323846f)
        srcDest[idx] -= 2.f * 3.14159265358979323846f;

    scratch[idx].x = sinf(azimuthRad); // notice.x
    scratch[idx].y = cosf(azimuthRad); // notice.y
}

extern "C" void azimuthRightHanded(float* srcDest, float3* scratch, float accuracyError, int N, int cdi)
{
    cudaDeviceProp prop;
    cudaGetDeviceProperties(&prop, cdi);
    const int nt = prop.maxThreadsPerBlock;
    const int nb = (N + nt - 1) / nt;

    azimuthRightHandedKernel<<<nb, nt>>>(srcDest, scratch, accuracyError, N);
}

// uses destination and scrath to compute and store
// const float elevationDeg{ lidarReturns.elevations[idx] + accuracyErrorElevationDeg };
// const float elevationRad{ Deg2Rad(elevationDeg) };
// const float sinElevation{ ::sinf(elevationRad) };
// const float cosElevation{ ::cosf(elevationRad) };
// srcDest computes final elevation
// scratch.z = sinElevation
// scratch2 = cosElevation
__global__ void elevationKernel(float* srcDest, float3* scratch, float* scratch2, float accuracyError, int N)
{
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= N)
        return;

    srcDest[idx] = DEG2RAD(srcDest[idx] + accuracyError);

    const float elevationRad = srcDest[idx];
    scratch[idx].z = sinf(elevationRad); // notice .z
    scratch2[idx] = cosf(elevationRad);
}

extern "C" void elevation(float* srcDest, float3* scratch, float* scratch2, float accuracyError, int N, int cdi)
{
    cudaDeviceProp prop;
    cudaGetDeviceProperties(&prop, cdi);
    const int nt = prop.maxThreadsPerBlock;
    const int nb = (N + nt - 1) / nt;

    elevationKernel<<<nb, nt>>>(srcDest, scratch, scratch2, accuracyError, N);
}

//    const float rayDirectionX{ cosElevation * cosAzimuth };
//    const float rayDirectionY{ cosElevation * sinAzimuth };
//    const float rayDirectionZ{ sinElevation };
// srdDest has the point cloud location with transforms at the end.
__global__ void pointCloudWithTransformKernel(
    float3* srcDest, const float* cosEle, const float* dist, const float4 t1, const float4 t2, const float4 t3, int N)
{
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= N)
        return;
    const float sinAzimuth = srcDest[idx].x;
    const float cosAzimuth = srcDest[idx].y;
    const float sinElevation = srcDest[idx].z;
    const float cosElevation = cosEle[idx];
    const float distance = dist[idx];
    const float X{ distance * cosElevation * cosAzimuth };
    const float Y{ distance * cosElevation * sinAzimuth };
    const float Z{ distance * sinElevation };
    srcDest[idx] = make_float3(t1.x * X + t1.y * Y + t1.z * Z + t1.w, t2.x * X + t2.y * Y + t2.z * Z + t2.w,
                               t3.x * X + t3.y * Y + t3.z * Z + t3.w);
}

extern "C" void pointCloudWithTransform(
    float3* srcDest, const float* cosEle, const float* dist, const float3& accuracyError, const double* T, int N, int cdi)
{
    cudaDeviceProp prop;
    cudaGetDeviceProperties(&prop, cdi);
    const int nt = prop.maxThreadsPerBlock;
    const int nb = (N + nt - 1) / nt;

    float4 t1, t2, t3;
    if (T)
    {
        t1 = make_float4(T[0], T[4], T[8], T[12]);
        t2 = make_float4(T[1], T[5], T[9], T[13]);
        t3 = make_float4(T[2], T[6], T[10], T[14]);
    }
    else
    {
        t1 = make_float4(1, 0, 0, 0);
        t2 = make_float4(0, 1, 0, 0);
        t3 = make_float4(0, 0, 1, 0);
    }
    t1.w += accuracyError.x;
    t2.w += accuracyError.y;
    t3.w += accuracyError.z;
    pointCloudWithTransformKernel<<<nb, nt>>>(srcDest, cosEle, dist, t1, t2, t3, N);
}

__global__ void timestampKernel(uint64_t* dest, const uint32_t* src, const uint64_t* tickSource, int tickSize, int N)
{
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= N)
        return;
    int tick = idx / tickSize;

    dest[idx] = src[idx] + tickSource[tick];
}

extern "C" void timestamp(uint64_t* dest, const uint32_t* src, const uint64_t* tickSource, int tickSize, int N, int cdi)
{
    cudaDeviceProp prop;
    cudaGetDeviceProperties(&prop, cdi);
    const int nt = prop.maxThreadsPerBlock;
    const int nb = (N + nt - 1) / nt;

    timestampKernel<<<nb, nt>>>(dest, src, tickSource, tickSize, N);
}
