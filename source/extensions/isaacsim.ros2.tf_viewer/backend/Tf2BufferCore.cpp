// Copyright (c) 2023-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include "Tf2Impl.h"

namespace isaacsim
{
namespace ros2
{
namespace tf_viewer
{

Ros2BufferCoreImpl::Ros2BufferCoreImpl() = default;

Ros2BufferCoreImpl::~Ros2BufferCoreImpl() = default;

bool Ros2BufferCoreImpl::setTransform(void* msg, const std::string& authority, bool isStatic)
{
    if (!msg)
    {
        return false;
    }
    tf2_msgs__msg__TFMessage* tfMsg = static_cast<tf2_msgs__msg__TFMessage*>(msg);
    for (size_t i = 0; i < tfMsg->transforms.size; ++i)
    {
        // geometry_msgs/TransformStamped's C to C++ conversion
        auto data = tfMsg->transforms.data[i];
        auto transformStamped = geometry_msgs::msg::TransformStamped();
        transformStamped.header.set__frame_id(std::string(data.header.frame_id.data));
        transformStamped.header.stamp.set__sec(data.header.stamp.sec);
        transformStamped.header.stamp.set__nanosec(data.header.stamp.nanosec);
        transformStamped.set__child_frame_id(std::string(data.child_frame_id.data));
        transformStamped.transform.translation.set__x(data.transform.translation.x);
        transformStamped.transform.translation.set__y(data.transform.translation.y);
        transformStamped.transform.translation.set__z(data.transform.translation.z);
        transformStamped.transform.rotation.set__w(data.transform.rotation.w);
        transformStamped.transform.rotation.set__x(data.transform.rotation.x);
        transformStamped.transform.rotation.set__y(data.transform.rotation.y);
        transformStamped.transform.rotation.set__z(data.transform.rotation.z);
        // call tf2::BufferCore setTransform method
        try
        {
            m_buffer.setTransform(transformStamped, authority, isStatic);
        }
        catch (tf2::TransformException& ex)
        {
            std::string errorString = ex.what();
            CARB_LOG_ERROR(errorString.c_str());
            return false;
        }
    }
    return true;
}

bool Ros2BufferCoreImpl::getTransform(const std::string& targetFrame,
                                      const std::string& sourceFrame,
                                      double translation[],
                                      double rotation[])
{
    try
    {
        auto transformStamped = m_buffer.lookupTransform(targetFrame, sourceFrame, tf2::TimePointZero);
        translation[0] = transformStamped.transform.translation.x;
        translation[1] = transformStamped.transform.translation.y;
        translation[2] = transformStamped.transform.translation.z;
        rotation[0] = transformStamped.transform.rotation.x;
        rotation[1] = transformStamped.transform.rotation.y;
        rotation[2] = transformStamped.transform.rotation.z;
        rotation[3] = transformStamped.transform.rotation.w;
    }
    catch (const tf2::LookupException& e)
    {
        (void)e; // avoid warning C4101: unreferenced local variable
        return false;
    }
    catch (const tf2::ConnectivityException& e)
    {
        (void)e; // avoid warning C4101: unreferenced local variable
        return false;
    }
    catch (const tf2::ExtrapolationException& e)
    {
        (void)e; // avoid warning C4101: unreferenced local variable
        return false;
    }
    catch (const tf2::InvalidArgumentException& e)
    {
        (void)e; // avoid warning C4101: unreferenced local variable
        return false;
    }
    catch (...)
    {
        std::string errorString = "UNKNOW EXCEPTION";
        CARB_LOG_ERROR(errorString.c_str());
        return false;
    }
    return true;
}

bool Ros2BufferCoreImpl::getParentFrame(const std::string& frame, std::string& parentFrame)
{
    return m_buffer._getParent(frame, tf2::TimePointZero, parentFrame);
}

std::vector<std::string> Ros2BufferCoreImpl::getFrames()
{
    m_frames.clear();
    m_buffer._getFrameStrings(m_frames);
    return m_frames;
}

void Ros2BufferCoreImpl::clear()
{
    m_buffer.clear();
}

} // namespace tf_viewer
} // namespace ros2
} // namespace isaacsim
