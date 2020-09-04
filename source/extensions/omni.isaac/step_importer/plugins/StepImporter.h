#include <carb/logging/Log.h>

#include <omni/isaac/step_importer/StepImporter.h>
#include <step_reader/step_reader.hpp>

#include <memory>
#include <unordered_map>
namespace omni
{
namespace isaac
{
namespace step_importer
{

struct StepReader_Deleter
{
    void operator()(step_reader::StepReader* r)
    {
        // CARB_LOG_INFO("Destryoing file reader %ld", r);
        step_reader::DestroyReader(r);
    }
};

typedef std::unique_ptr<step_reader::StepReader, StepReader_Deleter> SiStepReaderPtr;

class SiContext
{
public:
    explicit SiContext()
    {
    }
    SiHandle addStepReader(step_reader::StepReader* r)
    {
        SiHandle handle = mNextId++;
        mStepReaderMap[handle] = SiStepReaderPtr(r, StepReader_Deleter());
        return handle;
    }
    step_reader::StepReader* getStepReader(int32_t id)
    {
        auto it = mStepReaderMap.find(id);
        if (it != mStepReaderMap.end())
        {
            return it->second.get();
        }
        else
        {
            return nullptr;
        }
    }
    void removeStepReader(uint32_t id)
    {
        auto it = mStepReaderMap.find(id);
        if (it != mStepReaderMap.end())
        {
            mStepReaderMap.erase(it);
        }
    }
    void clearStepReaders()
    {
        mStepReaderMap.clear();
    }

private:
    int32_t mNextId{ 0 };
    std::unordered_map<SiHandle, SiStepReaderPtr> mStepReaderMap;
};
}
}
}
