// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

//-----------------------------------------------------------------------------
// Bulk material properties. These are wavelength independent
struct BulkProperties
{
    float solarAbsorptivity{ 0.0f }; // [1] - unitless
    float thermalConductivity{ 0.0f }; // [W/m/K]
    float specificHeat{ 0.0f }; // [J/kg/K]
    float density{ 0.0f }; // [kg/m**3]
    float compressibility{ 0.0f }; // [1/Pa]
    float thickness{ 0.0f }; // [m]
    float porosity{ 1.f }; // [1] - unitless
};

//-----------------------------------------------------------------------------
// Spectral material properties. These are wavelength dependent
struct SpectralProperties
{
    float wavelength{ 0.0f }; // [m]
    float permittivityReal{ 1.0f }; // [1]
    float permittivityImag{ 0.0f }; // [1]
    float permeabilityReal{ 1.0f }; // [1]
    float permeabilityImag{ 0.0f }; // [1]
    float refractiveIndexReal{ 1.0f }; // [1]
    float refractiveIndexImag{ 0.0f }; // [1]
    float lobewidth{ 0.0f }; // [rad]
    float diffuseAlbedo{ 0.0f }; // [1]
    float emissivity{ 0.0f }; // [1]
    float baseRCS{ 0.0f }; // [m**2]
};
