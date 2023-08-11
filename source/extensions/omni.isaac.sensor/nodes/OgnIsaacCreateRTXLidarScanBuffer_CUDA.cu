// Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include <stdio.h>
#include <cuda.h>

#define DEG2RAD(deg) ((deg)/180.f* 3.14159265358979323846f)
#define RAD2DEG(rad) ((rad)/3.14159265358979323846f*180.f)

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
__global__ void azimuthRightHandedKernel(float *srcDest, float3 *scratch, float accuracyError, int N)
{
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= N) return;
    srcDest[idx] = srcDest[idx] + accuracyError;
    // order of next two is order in original code.
	const float azimuthDeg = DEG2RAD(360.f - srcDest[idx]);
    if (srcDest[idx] > 3.14159265358979323846f) srcDest[idx] -= 2.f*3.14159265358979323846f;

    scratch[idx].x = sinf(azimuthDeg);// notice.x
    scratch[idx].y = cosf(azimuthDeg);// notice.y
}

extern "C" void azimuthRightHanded(float *srcDest, float3 *scratch, float accuracyError, int N, int cdi)
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
__global__ void elevationKernel(float *srcDest, float3 *scratch, float *scratch2, float accuracyError, int N)
{
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= N) return;

	srcDest[idx] = srcDest[idx] + accuracyError;

	const float elevationDeg = DEG2RAD(srcDest[idx]);
    scratch[idx].z = sinf(elevationDeg);// notice .z
    scratch2[idx] = cosf(elevationDeg);
}

extern "C" void elevation(float *srcDest, float3 *scratch, float *scratch2, float accuracyError, int N, int cdi)
{
    cudaDeviceProp prop;
    cudaGetDeviceProperties(&prop, cdi);
    //printf("tpb %i\n", prop.maxThreadsPerBlock);
    const int nt = prop.maxThreadsPerBlock;
    const int nb = (N + nt - 1) / nt;

    elevationKernel<<<nb, nt>>>(srcDest, scratch, scratch2, accuracyError, N);
}

//    const float rayDirectionX{ cosElevation * cosAzimuth };
//    const float rayDirectionY{ cosElevation * sinAzimuth };
//    const float rayDirectionZ{ sinElevation };
// srdDest has the point cloud location at the end.
__global__ void pointCloudKernel(float3 *srcDest, const float *cosEle, const float* dist, int N)
{
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= N) return;
    const float sinAzimuth = srcDest[idx].x;
    const float cosAzimuth = srcDest[idx].y;
    const float sinElevation = srcDest[idx].z;
    const float cosElevation = cosEle[idx];
    const float distance = dist[idx];
    const float rayDirectionX{ cosElevation * cosAzimuth };
    const float rayDirectionY{ cosElevation * sinAzimuth };
    const float rayDirectionZ{ sinElevation };
    srcDest[idx] = make_float3(distance*rayDirectionX, distance*rayDirectionY, distance*rayDirectionZ);
}


extern "C" void pointCloud(float3 *srcDest, const float *cosEle, const float* dist, int N, int cdi)
{
    cudaDeviceProp prop;
    cudaGetDeviceProperties(&prop, cdi);
    const int nt = prop.maxThreadsPerBlock;
    const int nb = (N + nt - 1) / nt;

    pointCloudKernel<<<nb, nt>>>(srcDest, cosEle, dist, N);
}