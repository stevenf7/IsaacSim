// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
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

#include <RunLoopRunner.h>
#include <iomanip>
#include <iostream>

#define FMT_HEADER_ONLY 1
#include "RunLoopSynchronizer.h"
#include "fmt/include/fmt/format.h"

static constexpr char kAppRunLoops[] = "/app/runLoops";
static constexpr char kSyncToPresentGlobal[] = "/app/runLoopsGlobal/syncToPresent";

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


constexpr const uint64_t kProfilerMask = 1;
const double kDefaultFrequency = 60;

/**
 * @brief This class is a high precision timer that is specific to the Windows
 * operating system. It is designed to be efficient in terms of CPU usage, and
 * provides a more accurate way to measure sleep time than the chrono
 * sleep_until function. The class utilizes the Win32 timer and calculates the
 * average error in sleep time, which is then used to minimize the amount of
 * time spent in a sleep state, and instead uses a spin lock to wait for the
 * remaining time. Overall, this class is ideal for applications that require
 * precise timing.
 */
class PrecisionSleep
{
public:
    PrecisionSleep()
    {
#if CARB_PLATFORM_WINDOWS
        m_timer = CreateWaitableTimer(NULL, FALSE, NULL);
#endif
    }

    ~PrecisionSleep()
    {
#if CARB_PLATFORM_WINDOWS
        CloseHandle(m_timer);
#endif
    }

    void sleep(const high_resolution_clock::time_point& waitUntil)
    {
        using namespace std::chrono;
        // We use doubles because we use a lot of math to compute and balance
        // the error. Even though the error in nanoseconds is a big number, with
        // time, we multiply it by a tiny number. We want to maintain precision.
        double sleepDurationNs =
            static_cast<double>(duration_cast<nanoseconds>(waitUntil - high_resolution_clock::now()).count());
        double sleepDurationErrorCorrectedNs = sleepDurationNs - m_estimateWakeUpDelayNs;
        int64_t dueNs = static_cast<int64_t>(sleepDurationErrorCorrectedNs);

        // This loop waits a bit less than sleepDuration and adjusts the average
        // wake up error.
        while (dueNs > 100)
        {

#if CARB_PLATFORM_WINDOWS
            LARGE_INTEGER due;
            due.QuadPart = -dueNs / 100;
#else
            timespec due;
            due.tv_sec = dueNs / 1000000000;
            due.tv_nsec = dueNs % 1000000000;
#endif

            high_resolution_clock::time_point beforeSleep = high_resolution_clock::now();
            {
                CARB_PROFILE_ZONE(kProfilerMask, "Timer %" PRId64 "ns. Error is %.1fns", dueNs, m_estimateWakeUpDelayNs);
#if CARB_PLATFORM_WINDOWS
                // Use Windows SetWaitableTimerEx and WaitForSingleObject to sleep
                SetWaitableTimerEx(m_timer, &due, 0, NULL, NULL, NULL, 0);
                WaitForSingleObject(m_timer, INFINITE);
#else
                // Use posix nanosleep to sleep
                nanosleep(&due, &due);
#endif
            }
            high_resolution_clock::time_point afterSleep = high_resolution_clock::now();

            // Using Welford's algorithm to have the average of esimate delay
            // error on fly:
            // https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#Welford%27s_online_algorithm

            int64_t observedWaitNs = duration_cast<nanoseconds>(afterSleep - beforeSleep).count();

            ++m_count;
            double error = observedWaitNs - sleepDurationErrorCorrectedNs;

            // Double because we deal with a huge number m_count
            double delta = error - m_mean;
            m_mean += delta / m_count;
            m_m2 += delta * (error - m_mean);

            double stddev = sqrt(m_m2 / (m_count - 1));

            m_estimateWakeUpDelayNs = m_mean + stddev;

            // It's possible we need to sleep more. It happens during first several frames.
            sleepDurationNs = static_cast<double>(duration_cast<nanoseconds>(waitUntil - afterSleep).count());
            sleepDurationErrorCorrectedNs = sleepDurationNs - m_estimateWakeUpDelayNs;
            dueNs = static_cast<int64_t>(sleepDurationErrorCorrectedNs);
        }

        {
            CARB_PROFILE_ZONE(kProfilerMask, "Spin Lock");
            // Spin the rest of the time
            while (waitUntil - high_resolution_clock::now() > high_resolution_clock::duration::zero())
            {
                CARB_HARDWARE_PAUSE();
            }
        }
    }

#if CARB_PLATFORM_WINDOWS
    HANDLE m_timer;
#endif
    // 5e5 is initial value. It's possible to set any value, it will be
    // balanced to something like ~475726
    double m_estimateWakeUpDelayNs = 5e5;
    uint64_t m_count = 1;

    double m_mean = 5e5;
    double m_m2 = 0;
};

class RunLoopThread
{
public:
    bool mainThread = false;
    std::string name;
    RunLoop* loop = nullptr;

    std::atomic<bool> quit = { false };
    std::atomic<bool> running = { false };

    // Rate limiting:
    bool rateLimitEnabled = false;
    bool rateLimitUseBusyLoop = false;
    bool rateLimitUsePrecisionSleep = false;
    bool syncToPresent = false;
    bool syncToPresentGlobal = false;
    microseconds minLoopTime;

    // Sliding maximum parameters:
    bool useSlidingMaximum = false;
    size_t slidingMaximumCount = 60;
    size_t slidingMaximumOutlierCount = 6;
    float slidingMaximumToleranceFactor = 2.0f;

    RunLoopThread(const std::string& name_) : name(name_), m_runloopIterationCount(0)
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
                                                this->running = true;
                                                while (!quit)
                                                {
                                                    this->update();
                                                }
                                                this->running = false;
                                            } });
    }

    void update()
    {
        // Calculate dt
        auto startTime = high_resolution_clock::now();
        double dt = duration_cast<microseconds>(startTime - m_lastUpdateTime).count() * 0.000001;
        m_lastUpdateTime = startTime;
        if (mIsManualDt)
        {
            dt = mDeltaTime;
        }
        CARB_PROFILE_EVENT(kProfilerMask, carb::profiler::InstantType::Thread, "[%s] frame event", name.c_str());

#if 0 // For perf debugging - disable by default
        std::time_t t = std::time(nullptr);
        std::tm tm;
        localtime_s(&tm, &t);
        std::cout << "RunLoop Update [ " << name << "]" << " @ " << std::put_time(&tm, "%c %Z") << std::endl;
#endif

        this->_initialize();

        updateSettings();

        // We should only do this if we can guarantee we never fall below the rate limited FPS.
        // DriveSim would want something like this, but they do their own RunLoopRunner. For now disable this
        // if (this->rateLimitEnabled)
        //{
        //    // If rate limit is enabled, we set dt to rateLimitFrequency
        //    dt = this->minLoopTime.count() * 0.000001;
        //}

        // Send pre-update to all listeners
        {
            CARB_PROFILE_ZONE(kProfilerMask, "[RunLoop: %s] Pre-Update Events", name.c_str());
            //
            // Main thread should share the iteration count since that is the one place
            // that knows which "iteration" is being run
            //
            if (mainThread)
            {
                this->loop->preUpdate->push(
                    0, std::make_pair("dt", dt), std::make_pair("SWHFrameNumber", m_runloopIterationCount));
            }
            else
            {
                this->loop->preUpdate->push(0, std::make_pair("dt", dt));
            }
            this->loop->preUpdate->pump();
        }

        // Send update to all listeners
        {
            CARB_PROFILE_ZONE(kProfilerMask, "[RunLoop: %s] Update Events", name.c_str());
            if (mainThread)
            {
                this->loop->update->push(
                    0, std::make_pair("dt", dt), std::make_pair("SWHFrameNumber", m_runloopIterationCount));
            }
            else
            {
                this->loop->update->push(0, std::make_pair("dt", dt));
            }
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

        if (m_runLoopSynchronizer && m_runLoopSynchronizer->isActive())
        {
            CARB_PROFILE_ZONE(kProfilerMask, "Synchronize with present thread");
            auto elapsed = high_resolution_clock::now() - startTime;
            float elapsedNs = static_cast<float>(duration_cast<nanoseconds>(elapsed).count());
            m_runLoopSynchronizer->wait(elapsedNs, useSlidingMaximum ? slidingMaximumCount : 0,
                                        slidingMaximumOutlierCount, slidingMaximumToleranceFactor);
        }
        else
        {
            CARB_PROFILE_ZONE(kProfilerMask, "Rate limit sleep");
            auto elapsed = high_resolution_clock::now() - startTime;
            if (this->rateLimitEnabled && duration_cast<microseconds>(elapsed) < this->minLoopTime)
            {
                auto waitUntil = startTime + this->minLoopTime;
                if (rateLimitUseBusyLoop)
                {
                    while (high_resolution_clock::now() < waitUntil)
                    {
                        ;
                    }
                }
                else if (rateLimitUsePrecisionSleep)
                {
                    m_windowsSleep.sleep(waitUntil);
                }
                else
                {
                    std::this_thread::sleep_until(waitUntil);
                }
            }
        }

        // Mark frame completion for this RunLoop. NOTE: This name *must* contain "frame" for Tracy's import chrome tool
        // to recognize it as a frame message since chrome-tracing doesn't have a frame marker.
        // See: https://github.com/wolfpld/tracy/issues/456
        CARB_PROFILE_FRAME(0, "Frame: %s", name.c_str());

        m_runloopIterationCount++;
    }

    void updateSettings()
    {
        auto settings = getCachedInterface<settings::ISettings>();
        if (!settings)
            return;

        if (!m_minLoopTimeString.length())
        {
            m_minLoopTimeString = fmt::format("{0}/{1}/rateLimitFrequency", kAppRunLoops, name);
            m_rateLimitEnabledString = fmt::format("{0}/{1}/rateLimitEnabled", kAppRunLoops, name);
            m_rateLimitUseBusyLoopString = fmt::format("{0}/{1}/rateLimitUseBusyLoop", kAppRunLoops, name);
            m_rateLimitUsePrecisionSleepString = fmt::format("{0}/{1}/rateLimitUsePrecisionSleep", kAppRunLoops, name);
            m_syncToPresent = fmt::format("{0}/{1}/syncToPresent", kAppRunLoops, name);
            m_slidingMaximumEnabledPath = fmt::format("{0}/{1}/slidingMaximum/enabled", kAppRunLoops, name);
            m_slidingMaximumCountPath = fmt::format("{0}/{1}/slidingMaximum/count", kAppRunLoops, name);
            m_slidingMaximumOutlierCountPath = fmt::format("{0}/{1}/slidingMaximum/outlierCount", kAppRunLoops, name);
            m_slidingMaximumToleranceFactorPath =
                fmt::format("{0}/{1}/slidingMaximum/outlierTolerance", kAppRunLoops, name);

            settings->setDefaultBool(m_rateLimitEnabledString.c_str(), false);
            settings->setDefaultBool(m_rateLimitUseBusyLoopString.c_str(), false);
            settings->setDefaultFloat(m_minLoopTimeString.c_str(), kDefaultFrequency);
            settings->setDefaultBool(m_rateLimitUsePrecisionSleepString.c_str(), false);
            settings->setDefaultBool(m_syncToPresent.c_str(), true);
            settings->setDefaultBool(m_slidingMaximumEnabledPath.c_str(), false);
            settings->setDefaultInt(m_slidingMaximumCountPath.c_str(), 60);
            settings->setDefaultInt(m_slidingMaximumOutlierCountPath.c_str(), 6);
            settings->setDefaultFloat(m_slidingMaximumToleranceFactorPath.c_str(), 2.0f);

            static struct SetDefaultOnce
            {
                SetDefaultOnce()
                {
                    getCachedInterface<settings::ISettings>()->setDefaultBool(kSyncToPresentGlobal, false);
                }
            } setDefaultOnce;
        }

        const double freq = settings->getAsFloat64(m_minLoopTimeString.c_str());
        minLoopTime = duration_cast<microseconds>(seconds(1) / freq);
        rateLimitEnabled = settings->getAsBool(m_rateLimitEnabledString.c_str());
        rateLimitUseBusyLoop = settings->getAsBool(m_rateLimitUseBusyLoopString.c_str());
        rateLimitUsePrecisionSleep = settings->getAsBool(m_rateLimitUsePrecisionSleepString.c_str());
        syncToPresent = settings->getAsBool(m_syncToPresent.c_str());
        syncToPresentGlobal = settings->getAsBool(kSyncToPresentGlobal);
        useSlidingMaximum = settings->getAsBool(m_slidingMaximumEnabledPath.c_str());

        if (useSlidingMaximum)
        {
            slidingMaximumCount = static_cast<size_t>(settings->getAsInt(m_slidingMaximumCountPath.c_str()));
            slidingMaximumOutlierCount =
                static_cast<size_t>(settings->getAsInt(m_slidingMaximumOutlierCountPath.c_str()));
            slidingMaximumToleranceFactor = settings->getAsFloat(m_slidingMaximumToleranceFactorPath.c_str());
        }

        if (m_runLoopSynchronizer)
        {
            m_runLoopSynchronizer->setTargetFPS(freq);
            m_runLoopSynchronizer->setActive(syncToPresent && syncToPresentGlobal);
        }
    }
    void setManualStepSize(double dt)
    {
        mDeltaTime = dt;
    }
    void setManualMode(bool enabled)
    {
        mIsManualDt = enabled;
    }

private:
    void _initialize()
    {
        if (m_initialized)
        {
            return;
        }

        // Setup present thread from the runloop thread. If we setup it from
        // constructor it's possible we have infinity lock.
        if (!m_runLoopSynchronizer && name != "present")
        {
            m_runLoopSynchronizer = std::make_unique<RunLoopSynchronizer>();
        }

        m_initialized = true;
    }

    high_resolution_clock::time_point m_lastUpdateTime;

    std::unique_ptr<std::thread> m_thread;
    std::string m_minLoopTimeString;
    std::string m_rateLimitEnabledString;
    std::string m_rateLimitUseBusyLoopString;
    std::string m_rateLimitUsePrecisionSleepString;
    std::string m_syncToPresent;
    std::string m_slidingMaximumEnabledPath;
    std::string m_slidingMaximumCountPath;
    std::string m_slidingMaximumOutlierCountPath;
    std::string m_slidingMaximumToleranceFactorPath;

    std::unique_ptr<RunLoopSynchronizer> m_runLoopSynchronizer;

    bool m_initialized = false;

    // Variables for storing and handling manually set dt
    double mDeltaTime;
    bool mIsManualDt = false;

    //
    // It is convenient to have a counter that tracks what update
    // step of the runloop runner we are in. This is currently used to
    // track the "framenumber" for the application. This is passed through
    // into fabric so that we can have an index that ties an element of
    // SimStageWithHistory to the iteration of the update loop that the data
    // in the ring buffer was created from.
    //
    // Note this will wrap around, but it seems unlikley to cause problems
    // since someone would have to holding onto data from 65535 steps ago in order
    // to cause a collision
    //
    // would prefer to use an uint64_t here, however
    //      carb::dictionary::IDictionary::makeAtPath
    // only suppoers int64 in the template instantiation the we get to from
    //      carb::events::IEvent::setValues<unsigned __int64>
    // that is called when we try and add call
    //      IEventStream::push(EventType type, ValuesT&&... values)
    //
    int64_t m_runloopIterationCount;

    PrecisionSleep m_windowsSleep;
};
// public so we can access it in setters
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

                RunLoopThread* t = _getOrCreateThread(lock, name);
                t->updateSettings();
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
            t->running = true;
            m_mainThread = t;
        }

        if (m_started)
            t->run();
    }

    virtual void onRemoveRunLoop(const char* name, RunLoop* loop, bool bBlock) override
    {
        bool bRequestedQuit = false;

        {
            std::unique_lock<std::mutex> lock(m_mutex);
            auto it = m_runLoops.find(name);
            if (it != m_runLoops.end())
            {
                if (it->second->loop == loop)
                {
                    bRequestedQuit = true;
                    it->second->quit = true;
                }
            }
        }

        if (bRequestedQuit && bBlock)
        {
            static constexpr uint32_t kPollLimit = 100;
            static constexpr uint32_t kSleepTimeMs = 50;

            bool bRunning;
            uint32_t i = 0;
            do
            {
                bRunning = false;
                std::unique_lock<std::mutex> lock(m_mutex);
                auto it = m_runLoops.find(name);
                if (it != m_runLoops.end())
                {
                    if (it->second->loop == loop && it->second->running)
                    {
                        bRunning = true;
                        std::this_thread::sleep_for(std::chrono::milliseconds(kSleepTimeMs));
                    }
                }
            } while (bRunning && ++i < kPollLimit);

            if (bRunning)
            {
                CARB_LOG_WARN("onRemoveRunLoop failed to terminate runloop: %s", name ? name : "null");
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

static void SetManualStepSize(double dt, std::string name = "")
{
    for (auto& l : m_runLoops)
    {
        if (name.compare("") != 0)
        {
            if (l.first.compare(name) == 0)
                l.second->setManualStepSize(dt);
        }
        else
        {
            l.second->setManualStepSize(dt);
        }
    }
}
static void SetManualMode(bool enabled, std::string name = "")
{
    for (auto& l : m_runLoops)
    {
        if (name.compare("") != 0)
        {
            if (l.first.compare(name) == 0)
                l.second->setManualMode(enabled);
        }
        else
        {
            l.second->setManualMode(enabled);
        }
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

    iface.setManualMode = SetManualMode;
    iface.setManualStepSize = SetManualStepSize;
}

void fillInterface(omni::kit::IExtensionPluginImpl& iface)
{
}
