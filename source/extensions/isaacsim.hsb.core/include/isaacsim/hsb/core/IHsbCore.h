// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <carb/Interface.h>

namespace isaacsim
{
namespace hsb
{
namespace core
{

struct IHsbCore
{
    CARB_PLUGIN_INTERFACE("isaacsim::hsb::core::IHsbCore", 1, 0);
};

} // namespace core
} // namespace hsb
} // namespace isaacsim
