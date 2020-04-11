// Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "UsdUrdfStream.h"
#include <algorithm>
#include <fstream>
#include <iostream>
#include <string>
using std::string;
using std::vector;

// #include <boost/iterator.hpp>
// #include <boost/lexical_cast.hpp>

/// FIXME
#if defined(DEBUG) || defined(ERROR)
//int oldDEBUG = DEBUG;
#    undef ERROR
#    undef DEBUG
#    include <NvIsaacFramework.h>
#    include <NvIsaacRobotModel.h>
//#define ERROR 0
//#define DEBUG 0
#else
#    include <NvIsaacFramework.h>
#    include <NvIsaacRobotModel.h>
#endif

UsdUrdfStream::UsdUrdfStream()
{
}


bool UsdUrdfStream::UsdUrdfReadDataFromFile(std::string const& fileName, std::string* error)
{
    // try and open the file
    std::ifstream fin(fileName.c_str());
    if (!fin.is_open())
    {
        if (error)
        {
            *error = pxr::TfStringPrintf("Could not open file: (%s)\n", fileName.c_str());
        }
        return false;
    }
    SetFileName(fileName);
    return UsdUrdfReadDataFromStream(fin, error);
}


bool UsdUrdfStream::UsdUrdfReadDataFromStream(std::istream& input, std::string* error)
{
    // copy the stream into a char* buffer so it can be read by RobotImpSDK.
    // it would probably  be better if we could have RobotImpSDK use std::istream directly.
    string line;
    std::vector<char> inputAsVec;
    while (getline(input, line))
    {
        std::copy(line.begin(), line.end(), std::back_inserter(inputAsVec));
        inputAsVec.push_back('\n');
    }

    // Setup the RobotImpSDK to load the file into a PhysicsDOM.
    NvIsaac::FrameworkDesc desc;
    desc.fullUserInterface = false;
    // desc.addCwdToAssetPaths = false;
    // desc.searchForDefaultDataDirectory = false;
    NvIsaac::IFramework* framework = NvIsaac::createFramework(desc);
    if (!framework)
    {
        std::fprintf(stderr, "*** Failed to create Isaac framework\n");
        return false;
    }

    NvIsaac::IRobotModelImporter* modelMgr = framework->getRobotModelImporter();
    if (!modelMgr)
    {
        fprintf(stderr, "*** Failed to get model manager\n");
        return false;
    }

    NvIsaac::RobotModelImportSettings settings;
    settings.mergeBodiesConnectedByFixedJoints = 0;

    NvIsaac::IRobotModel* model =
        modelMgr->importModel(GetFileName().c_str(), settings, inputAsVec.data(), inputAsVec.size());

    if (!model)
    {

        fprintf(stderr, "Model NOT loaded!\n");
        return false;
    }
    else
    {
        fprintf(stderr, "Model %s loaded!\n", model->getName());
    }
    SetRobotModel(model);
    return true;
}
