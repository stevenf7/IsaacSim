// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include "Tf2Foxy.h"

Ros2BufferCoreFoxy::Ros2BufferCoreFoxy()
{
}

Ros2BufferCoreFoxy::~Ros2BufferCoreFoxy()
{
}

bool Ros2BufferCoreFoxy::setTransform(void* msg, const std::string& authority, bool isStatic)
{
    if (!msg)
        return false;
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
            mBuffer.setTransform(transformStamped, authority, isStatic);
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

bool Ros2BufferCoreFoxy::getTransform(const std::string& targetFrame,
                                      const std::string& sourceFrame,
                                      double translation[],
                                      double rotation[])
{
    try
    {
        auto transformStamped = mBuffer.lookupTransform(targetFrame, sourceFrame, tf2::TimePointZero);
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
        return false;
    }
    catch (const tf2::ConnectivityException& e)
    {
        return false;
    }
    catch (const tf2::ExtrapolationException& e)
    {
        return false;
    }
    catch (const tf2::InvalidArgumentException& e)
    {
        return false;
    }
    catch (...)
    {
        std::string errorString = "UNKNOW EXCEPTION";
        // std::string errorString = ex.what();
        CARB_LOG_ERROR(errorString.c_str());
        return false;
    }
    return true;
}

bool Ros2BufferCoreFoxy::getParentFrame(const std::string& frame, std::string& parentFrame)
{
    return mBuffer._getParent(frame, tf2::TimePointZero, parentFrame);
}

std::vector<std::string> Ros2BufferCoreFoxy::getFrames()
{
    mFrames.clear();
    mBuffer._getFrameStrings(mFrames);
    return mFrames;
}

void Ros2BufferCoreFoxy::clear()
{
    mBuffer.clear();
}
