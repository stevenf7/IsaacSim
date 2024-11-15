// Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
iou=[-#include "pxr/pxr.h"
#include "pxr/base/tf/pyModule.h"

PXR_NAMESPACE_USING_DIRECTIVE

TF_WRAP_MODULE
{
    TF_WRAP(RobotSchemaJointAPI);
    TF_WRAP(RobotSchemaLinkAPI);
    TF_WRAP(RobotSchemaReferencePointAPI);
    TF_WRAP(RobotSchemaRobotAPI);
    TF_WRAP(RobotSchemaTokens);
}
