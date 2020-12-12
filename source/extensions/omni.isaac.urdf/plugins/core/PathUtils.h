// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <string>
#include <vector>

namespace carb
{
namespace gym
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

// returns filename without extension (e.g. "foo/bar/bingo.txt" -> "bingo")
std::string getPathStem(const char* path);

std::vector<std::string> getFileListRecursive(const std::string& dir, bool sorted = true);

}
}
