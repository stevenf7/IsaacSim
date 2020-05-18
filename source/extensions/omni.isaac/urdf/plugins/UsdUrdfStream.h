// Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once
#include <omni/isaac/urdf/Urdf.h>

#include <string>

namespace NvIsaac
{
class IRobotModel;
}


namespace omni
{
namespace isaac
{
namespace urdf
{


/// \class UsdUrdfStream
///
/// Deserialization is supported.  See \relates UsdUrdfReadDataFromFile
/// \relates UsdUrdfReadDataFromStream.
///
class UsdUrdfStream
{
public:
    void SetImportConfig(const ImportConfig& importConfig)
    {
        mImportConfig = importConfig;
    }
    void SetRobotModel(NvIsaac::IRobotModel* model)
    {
        mRobotModel = model;
    }
    NvIsaac::IRobotModel* GetRobotModel() const
    {
        return mRobotModel;
    }
    void SetFileName(std::string const& name)
    {
        mFileName = name;
    }
    std::string GetFileName() const
    {
        return mFileName;
    }


    /// Read urdf data from \a fileName into \a data.  Return true if successful,
    /// false otherwise.  If unsuccessful, return an error message in \a error if it
    /// is not null.
    bool UsdUrdfReadDataFromFile(std::string const& fileName, std::string* error = 0);

    /// Read urdf data from \a stream into \a data.  Return true if successful, false
    /// otherwise.  If unsuccessful, return an error message in \a error if it is
    /// not null.
    bool UsdUrdfReadDataFromStream(std::istream& input, std::string* error = 0);

    /// Return an anonymous (in-memory-only) layer with data from \p urdfStream
    /// translated to Usd.
    void UsdUrdfTranslateUrdfToUsd(pxr::UsdStageRefPtr stage);


private:
    ImportConfig mImportConfig;
    // The "stream" is really just a pointer to a DOM and graphics loaded with RobotImpSDK
    NvIsaac::IRobotModel* mRobotModel;


    // File names are used to derive the possible package paths, and can have more than one if more then one urdf is
    // loaded or if a urdf if combined into this one.  FIXME
    std::string mFileName;
};

}
}
}
