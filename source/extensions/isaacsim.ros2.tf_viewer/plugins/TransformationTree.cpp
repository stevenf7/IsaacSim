// Copyright (c) 2022-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define CARB_EXPORTS

#include <carb/PluginUtils.h>

#include <isaacsim/ros2/bridge/Ros2Distro.h>
#include <isaacsim/ros2/bridge/Ros2Node.h>

#include <Tf2Factory.h>
#include <TransformListener.h>

const struct carb::PluginImplDesc pluginImplDesc = { "isaacsim.ros2.tf_viewer.plugin", "Transform Listener", "NVIDIA",
                                                     carb::PluginHotReload::eDisabled, "dev" };

namespace isaacsim
{
namespace ros2
{
namespace tf_viewer
{

class TransformListener : public ITransformListener, isaacsim::ros2::bridge::Ros2Node
{
public:
    bool initialize(const std::string& rosDistro)
    {
        if (!isaacsim::ros2::bridge::isRos2DistroSupported(rosDistro))
        {
            CARB_LOG_ERROR("Unsupported ROS_DISTRO: %s", rosDistro.c_str());
            return false;
        }
        if (!m_libraryLoader)
        {
            m_libraryLoader =
                std::make_shared<isaacsim::core::utils::LibraryLoader>("isaacsim.ros2.tf_viewer." + rosDistro);
            if (!m_libraryLoader)
            {
                CARB_LOG_ERROR("Unable to load the isaacsim.ros2.tf_viewer.%s library", rosDistro.c_str());
                return false;
            }
        }
        if (!m_tf2Factory)
        {

            typedef Tf2Factory* (*createFactory_binding)(void);
            createFactory_binding createFactory = (m_libraryLoader->getSymbol<createFactory_binding>("createFactory"));
            if (!createFactory)
            {
                CARB_LOG_ERROR("Unable to load symbols from the isaacsim.ros2.tf_viewer.%s library", rosDistro.c_str());
                return false;
            }
            m_tf2Factory = createFactory();
        }
        if (!m_buffer)
        {
            m_buffer = m_tf2Factory->createBuffer();
            m_buffer->clear();
        }
        return true;
    }

    void finalize()
    {
        if (m_subscriberTf)
        {
            m_subscriberTf.reset();
            m_subscriberTf = nullptr;
        }
        if (m_messageTfStatic)
        {
            m_messageTfStatic.reset();
            m_messageTfStatic = nullptr;
        }
        Ros2Node::reset();
    }

    bool spin()
    {
        if (!isInitialized())
        {
            if (!initializeNodeHandle("isaacsim_tf_viewer", "", 0))
            {
                CARB_LOG_ERROR("Unable to create isaacsim.ros2.tf_viewer ROS2 node");
                return false;
            }
        }

        if (!m_subscriberTf)
        {
            isaacsim::ros2::bridge::Ros2QoSProfile qos;
            qos.depth = 100;
            m_messageTf = m_factory->createTfTreeMessage();
            m_subscriberTf =
                m_factory->createSubscriber(m_nodeHandle.get(), "/tf", m_messageTf->getTypeSupportHandle(), qos);
            return true;
        }
        if (!m_subscriberTfStatic)
        {
            isaacsim::ros2::bridge::Ros2QoSProfile qos;
            qos.depth = 100;
            m_messageTfStatic = m_factory->createTfTreeMessage();
            m_subscriberTfStatic = m_factory->createSubscriber(
                m_nodeHandle.get(), "/tf_static", m_messageTfStatic->getTypeSupportHandle(), qos);
            return true;
        }

        bool status = true;
        status &= _subscriberCallback(false);
        status &= _subscriberCallback(true);
        return status;
    }

    void reset()
    {
        if (!m_buffer)
        {
            return;
        }
        m_buffer->clear();
    }

    void computeTransforms(const std::string& rootFrame)
    {
        if (!m_buffer)
        {
            return;
        }
        // clear containers
        m_frames.clear();
        m_relations.clear();
        m_transforms.clear();
        // get all frames
        m_frames = m_buffer->getFrames();
        // get transformations
        std::string parentFrame;
        for (auto& frame : m_frames)
        {
            bool retval = m_buffer->getParentFrame(frame, parentFrame);
            if (retval)
            {
                m_relations.push_back({ frame, parentFrame });
                double translation[3], rotation[4];
                retval = m_buffer->getTransform(rootFrame, frame, translation, rotation);
                if (retval)
                {
                    m_transforms[frame] = { { translation[0], translation[1], translation[2] },
                                            { rotation[0], rotation[1], rotation[2], rotation[3] } };
                }
            }
        }
    }

    const std::vector<std::string>& getFrames()
    {
        return m_frames;
    };
    const std::vector<std::tuple<std::string, std::string>>& getRelations()
    {
        return m_relations;
    };
    const std::unordered_map<std::string,
                             std::tuple<std::tuple<double, double, double>, std::tuple<double, double, double, double>>>&
    getTransforms()
    {
        return m_transforms;
    };

private:
    std::shared_ptr<isaacsim::core::utils::LibraryLoader> m_libraryLoader = nullptr;
    Tf2Factory* m_tf2Factory = nullptr;

    std::shared_ptr<isaacsim::ros2::bridge::Ros2Subscriber> m_subscriberTf = nullptr;
    std::shared_ptr<isaacsim::ros2::bridge::Ros2Subscriber> m_subscriberTfStatic = nullptr;

    std::shared_ptr<isaacsim::ros2::bridge::Ros2TfTreeMessage> m_messageTf = nullptr;
    std::shared_ptr<isaacsim::ros2::bridge::Ros2TfTreeMessage> m_messageTfStatic = nullptr;

    std::shared_ptr<Ros2BufferCore> m_buffer = nullptr;

    std::vector<std::string> m_frames;
    std::vector<std::tuple<std::string, std::string>> m_relations;
    std::unordered_map<std::string, std::tuple<std::tuple<double, double, double>, std::tuple<double, double, double, double>>>
        m_transforms;

    bool _subscriberCallback(bool isStatic)
    {
        if (!m_buffer)
        {
            return false;
        }
        auto subscriber = isStatic ? m_subscriberTfStatic : m_subscriberTf;
        auto message = isStatic ? m_messageTfStatic : m_messageTf;
        while (subscriber->spin(message->getPtr()))
        {
            m_buffer->setTransform(message->getPtr(), "", isStatic);
        }
        return true;
    }
};

} // namespace tf_viewer
} // namespace ros2
} // namespace isaacsim

CARB_PLUGIN_IMPL(pluginImplDesc, isaacsim::ros2::tf_viewer::TransformListener)

void fillInterface(isaacsim::ros2::tf_viewer::TransformListener& iface)
{
}
