// SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#pragma once

// clang-format off
#include "../UsdPCH.h"
// clang-format on

#include <string>
#include <vector>

namespace isaacsim
{
namespace asset
{
namespace importer
{
namespace urdf
{
enum class PathType
{
    eNone, // path does not exist
    eFile, // path is a regular file
    eDirectory, // path is a directory
    eOther, // path is something else
};

PathType testPath(const char* path);

bool isAbsolutePath(const char* path);

bool makeDirectory(const char* path);

std::string pathJoin(const std::string& path1, const std::string& path2);

std::string getCwd();

// Convert a url path to a valid Sdf path
std::string convertToSdfPath(const std::string& Path, bool absolute = true);

// returns filename without extension (e.g. "foo/bar/bingo.txt" -> "bingo")
std::string getPathStem(const char* path);

std::vector<std::string> getFileListRecursive(const std::string& dir, bool sorted = true);

std::string makeValidUSDIdentifier(const std::string& name);

std::string getParent(const std::string& filePath);

bool createSymbolicLink(const std::string& target, const std::string& link);

std::string toLowercase(const std::string& str);

bool hasExtension(const std::string& filename, const std::string& extension);

}
}
}
}
