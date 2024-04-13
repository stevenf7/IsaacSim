// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define CARB_EXPORTS

#include <carb/PluginUtils.h>

#include <Ros2Node.h>
#include <Tf2Factory.h>
#include <TransformListener.h>


const struct carb::PluginImplDesc pluginImplDesc = { "omni.isaac.transform_listener.plugin", "Transform Listener",
                                                     "NVIDIA", carb::PluginHotReload::eDisabled, "dev" };

namespace omni
{
namespace isaac
{
namespace transform_listener
{


class TransformListener : public ITransformListener, Ros2Node
{
public:
    bool initialize(const std::string& rosDistro)
    {
        if (!(rosDistro == "foxy" || rosDistro == "humble"))
        {
            CARB_LOG_ERROR("Unsupported ROS_DISTRO: %s", rosDistro.c_str());
            return false;
        }
        if (!mLibraryLoader)
        {
            mLibraryLoader =
                std::make_shared<omni::isaac::utils::LibraryLoader>("omni.isaac.transform_listener." + rosDistro);
            if (!mLibraryLoader)
            {
                CARB_LOG_ERROR("Unable to load the omni.isaac.transform_listener.%s library", rosDistro.c_str());
                return false;
            }
        }
        if (!mTf2Factory)
        {

            typedef Tf2Factory* (*createFactory_binding)(void);
            createFactory_binding createFactory = (mLibraryLoader->getSymbol<createFactory_binding>("createFactory"));
            if (!createFactory)
            {
                CARB_LOG_ERROR(
                    "Unable to load symbols from the omni.isaac.transform_listener.%s library", rosDistro.c_str());
                return false;
            }
            mTf2Factory = (Tf2Factory*)createFactory();
        }
        if (!mBuffer)
        {
            mBuffer = mTf2Factory->createBuffer();
            mBuffer->clear();
        }
        return true;
    }

    void finalize()
    {
        if (mSubscriberTf)
        {
            mSubscriberTf.reset();
            mSubscriberTf = nullptr;
        }
        if (mMessageTfStatic)
        {
            mMessageTfStatic.reset();
            mMessageTfStatic = nullptr;
        }
        Ros2Node::reset();
    }

    bool spin()
    {
        if (!spinOnce("isaacsim_tf_viewer", "", 0))
            return false;

        if (!mSubscriberTf)
        {
            Ros2QoSProfile qos;
            qos.depth = 100;
            mMessageTf = mFactory->CreateTfTreeMessage();
            mSubscriberTf = mFactory->CreateSubscriber(mNodeHandle.get(), "/tf", mMessageTf->getTypeSupportHandle(), qos);
            return true;
        }
        if (!mSubscriberTfStatic)
        {
            Ros2QoSProfile qos;
            qos.depth = 100;
            mMessageTfStatic = mFactory->CreateTfTreeMessage();
            mSubscriberTfStatic = mFactory->CreateSubscriber(
                mNodeHandle.get(), "/tf_static", mMessageTfStatic->getTypeSupportHandle(), qos);
            return true;
        }

        bool status = true;
        status &= subscriberCallback(false);
        status &= subscriberCallback(true);
        return status;
    }

    void reset()
    {
        if (!mBuffer)
            return;
        mBuffer->clear();
    }

    void getTransformations(const std::string& rootFrame)
    {
        if (!mBuffer)
            return;
        // clear containers
        mFrames.clear();
        mRelations.clear();
        mTransformations.clear();
        // get all frames
        mFrames = mBuffer->getFrames();
        // get transformations
        std::string parentFrame;
        for (auto& frame : mFrames)
        {
            bool retval = mBuffer->getParentFrame(frame, parentFrame);
            if (retval)
            {
                mRelations.push_back({ frame, parentFrame });
                double translation[3], rotation[4];
                retval = mBuffer->getTransform(rootFrame, frame, translation, rotation);
                if (retval)
                    mTransformations[frame] = { { translation[0], translation[1], translation[2] },
                                                { rotation[0], rotation[1], rotation[2], rotation[3] } };
            }
        }
    }

    const std::vector<std::string>& getFrames()
    {
        return mFrames;
    };
    const std::vector<std::tuple<std::string, std::string>>& getRelations()
    {
        return mRelations;
    };
    const std::unordered_map<std::string,
                             std::tuple<std::tuple<double, double, double>, std::tuple<double, double, double, double>>>&
    getTransforms()
    {
        return mTransformations;
    };

private:
    std::shared_ptr<omni::isaac::utils::LibraryLoader> mLibraryLoader = nullptr;
    Tf2Factory* mTf2Factory = nullptr;

    std::shared_ptr<Ros2Subscriber> mSubscriberTf = nullptr;
    std::shared_ptr<Ros2Subscriber> mSubscriberTfStatic = nullptr;

    std::shared_ptr<Ros2TfTreeMessage> mMessageTf = nullptr;
    std::shared_ptr<Ros2TfTreeMessage> mMessageTfStatic = nullptr;

    std::shared_ptr<Ros2BufferCore> mBuffer = nullptr;

    std::vector<std::string> mFrames;
    std::vector<std::tuple<std::string, std::string>> mRelations;
    std::unordered_map<std::string, std::tuple<std::tuple<double, double, double>, std::tuple<double, double, double, double>>>
        mTransformations;

    bool subscriberCallback(bool isStatic)
    {
        if (!mBuffer)
            return false;
        auto subscriber = isStatic ? mSubscriberTfStatic : mSubscriberTf;
        auto message = isStatic ? mMessageTfStatic : mMessageTf;
        while (subscriber->spin(message->ptr()))
        {
            mBuffer->setTransform(message->ptr(), "", isStatic);
        }
        return true;
    }
};

} // namespace transform_listener
} // namespace isaac
} // namespace omni

CARB_PLUGIN_IMPL(pluginImplDesc, omni::isaac::transform_listener::TransformListener)

void fillInterface(omni::isaac::transform_listener::TransformListener& iface)
{
}
