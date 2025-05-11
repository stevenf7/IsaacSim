// SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#pragma once

namespace isaacsim
{
namespace core
{
namespace includes
{

/**
 * Helper base class to subscribe to pxr::TfNotice
 */
template <typename T>
class UsdNoticeListener : public pxr::TfWeakBase
{
public:
    virtual ~UsdNoticeListener()
    {
        revokeListener();
    }

    void registerListener()
    {
        // To avoid leak
        revokeListener();
        m_usdNoticeListenerKey = pxr::TfNotice::Register(pxr::TfCreateWeakPtr(this), &UsdNoticeListener::handleNotice);
    }

    void revokeListener()
    {
        if (m_usdNoticeListenerKey.IsValid())
        {
            pxr::TfNotice::Revoke(m_usdNoticeListenerKey);
        }
    }

    virtual void handleNotice(const T& objectsChanged) = 0;

private:
    pxr::TfNotice::Key m_usdNoticeListenerKey;
};

} // namespace includes
} // namespace core
} // namespace isaacsim
