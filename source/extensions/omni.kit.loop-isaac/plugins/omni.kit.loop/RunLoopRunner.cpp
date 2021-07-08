// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#define CARB_EXPORTS

#include <carb/ObjectUtils.h>
#include <carb/PluginUtils.h>
#include <carb/dictionary/IDictionary.h>
#include <carb/events/IEvents.h>
#include <carb/filesystem/IFileSystem.h>
#include <carb/settings/ISettings.h>
#include <carb/settings/SettingsUtils.h>
#include <carb/tasking/TaskingUtils.h>

#include <omni/ext/IExt.h>
#include <omni/extras/DictHelpers.h>
#include <omni/kit/IApp.h>
#include <omni/kit/IRunLoopRunner.h>
#include <omni/kit/RunLoopRunner.h>

#include <iomanip>
#include <iostream>

#define FMT_HEADER_ONLY 1
#include "fmt/include/fmt/format.h"

static constexpr char kAppRunLoops[] = "/isaac/app/runLoops";

// clang-format off
const struct carb::PluginImplDesc kPluginImpl = {
    "omni.kit.loop-isaac.plugin",
    "",
    "NVIDIA",
    carb::PluginHotReload::eDisabled,
    "dev"
};

CARB_PLUGIN_IMPL_DEPS(
    carb::settings::ISettings,
    carb::dictionary::IDictionary,
    carb::events::IEvents,
    carb::logging::ILogging,
    carb::filesystem::IFileSystem
)
// clang-format on

using namespace carb;
using namespace std::chrono;

namespace omni
{
namespace kit
{


///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


const uint64_t kProfilerMask = 1;
const double kDefaultFrequency = 60;

class RunLoopThread
{
public:
    bool mainThread = false;
    std::string name;
    RunLoop* loop = nullptr;

    bool quit = false;

    double mDeltaTime;
    bool isManualDt = false;

    RunLoopThread(const std::string& name_) : name(name_)
    {
        // (hacky) Set first update time ~1/60 sec to avoid dealing with 0 elapsed time
        m_lastUpdateTime -= milliseconds(16);
        mDeltaTime = 1.0 / 60.0;
    }

    ~RunLoopThread()
    {
        if (m_thread)
            m_thread->join();
    }

    void run()
    {
        if (!mainThread && loop)
            m_thread.reset(new std::thread{ [this]
                                            {
                                                while (!quit)
                                                {
                                                    this->update();
                                                }
                                            } });
    }

    void update()
    {
        // Calculate dt
        auto startTime = high_resolution_clock::now();
        double dt = duration_cast<microseconds>(startTime - m_lastUpdateTime).count() * 0.000001;
        m_lastUpdateTime = startTime;

        if (isManualDt)
            dt = mDeltaTime;
        // CARB_LOG_WARN("name: %s, dt: %lf", name.c_str(), dt);

        // Send pre-update to all listeners
        {
            CARB_PROFILE_ZONE(kProfilerMask, "[RunLoop: %s] Pre-Update Events", name.c_str());
            this->loop->preUpdate->push(0, std::make_pair("dt", dt));
            this->loop->preUpdate->pump();
        }

        // Send update to all listeners
        {
            CARB_PROFILE_ZONE(kProfilerMask, "[RunLoop: %s] Update Events", name.c_str());
            this->loop->update->push(0, std::make_pair("dt", dt));
            this->loop->update->pump();
        }

        // Send post-update to all listeners
        {
            CARB_PROFILE_ZONE(kProfilerMask, "[RunLoop: %s] Post-Update Events", name.c_str());
            this->loop->postUpdate->push(0, std::make_pair("dt", dt));
            this->loop->postUpdate->pump();
        }

        {
            CARB_PROFILE_ZONE(kProfilerMask, "[RunLoop: %s] Message Bus Events", name.c_str());
            this->loop->messageBus->pump();
        }
    }

private:
    high_resolution_clock::time_point m_lastUpdateTime;
    std::unique_ptr<std::thread> m_thread;
};

std::map<std::string, std::unique_ptr<RunLoopThread>> m_runLoops;

class RunLoopRunnerImpl : public omni::kit::IRunLoopRunner
{
public:
    CARB_IOBJECT_IMPL

    virtual void startup() override
    {
        std::unique_lock<std::mutex> lock(m_mutex);

        // Read settings
        auto settings = getCachedInterface<settings::ISettings>();
        auto dict = getCachedInterface<dictionary::IDictionary>();
        const std::string kRunLoopsPath = kAppRunLoops;
        const dictionary::Item* runLoopsDict = settings->getSettingsDictionary(kRunLoopsPath.c_str());
        if (runLoopsDict)
        {
            size_t runLoopCount = dict->getItemChildCount(runLoopsDict);
            for (size_t i = 0; i < runLoopCount; i++)
            {
                const dictionary::Item* runLoopDict = dict->getItemChildByIndex(runLoopsDict, i);
                const std::string& name = dict->getItemName(runLoopDict);

                _getOrCreateThread(lock, name);
            }
        }

        for (auto& kv : m_runLoops)
            kv.second->run();

        m_started = true;
    }

    virtual void onAddRunLoop(const char* name, RunLoop* loop) override
    {
        std::unique_lock<std::mutex> lock(m_mutex);

        RunLoopThread* t = _getOrCreateThread(lock, name);
        t->loop = loop;

        if (std::string(name) == kRunLoopDefault)
        {
            t->mainThread = true;
            m_mainThread = t;
        }

        if (m_started)
            t->run();
    }

    virtual void onRemoveRunLoop(const char* name, RunLoop* loop) override
    {
        std::unique_lock<std::mutex> lock(m_mutex);

        auto it = m_runLoops.find(name);
        if (it != m_runLoops.end())
        {
            if (it->second->loop == loop)
            {
                it->second->quit = true;
            }
        }
    }

    virtual void update() override
    {
        if (m_mainThread)
        {
            m_mainThread->update();
        }
    }

    virtual void shutdown() override
    {
        for (auto& l : m_runLoops)
        {
            l.second->quit = true;
        }
        m_runLoops.clear();
    }

private:
    RunLoopThread* _getOrCreateThread(const std::unique_lock<std::mutex>& lock, const std::string& name)
    {
        // lock must already be hold
        CARB_ASSERT(lock.mutex() == &m_mutex);

        auto it = m_runLoops.find(name);
        if (it == m_runLoops.end())
            it = m_runLoops.insert({ name, std::make_unique<RunLoopThread>(name) }).first;
        return it->second.get();
    }

    bool m_started = false;


    RunLoopThread* m_mainThread = nullptr;
    std::mutex m_mutex;
};

static void SetRunnerDt(double dt, std::string name = "")
{
    for (auto& l : m_runLoops)
    {
        if (name.compare("") != 0)
        {
            if (l.first.compare(name) == 0)
                l.second->mDeltaTime = dt;
        }
        else
        {
            l.second->mDeltaTime = dt;
        }
        l.second->isManualDt = true;
    }
}


class IExtensionPluginImpl : public ext::IExt
{
public:
    void onStartup(const char*) override
    {
        carb::Framework* f = carb::getFramework();
        m_app = f->tryAcquireInterface<omni::kit::IApp>();
        m_runner = new RunLoopRunnerImpl();
        m_app->setRunLoopRunner(m_runner);
    }

    void onShutdown() override
    {
        m_app->setRunLoopRunner(nullptr);
        delete m_runner;
    }

private:
    RunLoopRunnerImpl* m_runner;
    omni::kit::IApp* m_app;
};
}
}

CARB_PLUGIN_IMPL(kPluginImpl, omni::kit::IRunLoopRunnerImpl, omni::kit::IExtensionPluginImpl)

void fillInterface(omni::kit::IRunLoopRunnerImpl& iface)
{
    using namespace omni::kit;

    iface.setRunnerDt = SetRunnerDt;
}

void fillInterface(omni::kit::IExtensionPluginImpl& iface)
{
}
