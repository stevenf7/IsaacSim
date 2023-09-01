// Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <omni/isaac/core_nodes/CoreNodes.h>
#include <rtx/hydra/HydraRenderResults.h>

#include <OgnIsaacReadTimesDatabase.h>

namespace omni
{
namespace isaac
{

typedef struct
{
    double simulationTime;
    double simulationTimeMonotonic;
    double systemTime;
    int64_t swhFrameNumber;
    int64_t rationalTimeOfSimNumerator;
    uint64_t rationalTimeOfSimDenominator;
    int64_t frameNumber;
    int64_t durationNumerator;
    uint64_t durationDenominator;
    uint64_t sampleTimeOffsetInSimFrames;
    int64_t externalTimeOfSimNs;
} TimesAOV;

namespace core_nodes
{

/**
 * @brief Node to expose the Isaac times. This nod need to be instantiated for every render product in the post-render
 * graph to create the render results "IsaacFabricTimes" AOV and in the action graph to actually read the AOV and expose
 * the value as its outputs.
 *
 */
class OgnIsaacReadTimes
{
    CoreNodes* mCoreNodeFramework = nullptr;

public:
    static void initialize(const GraphContextObj& context, const NodeObj& nodeObj)
    {
        auto& state = OgnIsaacReadTimesDatabase::sInternalState<OgnIsaacReadTimes>(nodeObj);
        state.mCoreNodeFramework = carb::getCachedInterface<CoreNodes>();
    }

    static bool compute(OgnIsaacReadTimesDatabase& db)
    {
        // const auto& contextObj = db.abi_context();
        // const IGraphContext* const iContext = contextObj.iContext;
        auto& state = db.internalState<OgnIsaacReadTimes>();
        CARB_ASSERT(state.mCoreNodeFramework);

        auto renderProduct = reinterpret_cast<usd::hydra::HydraRenderProduct*>(db.inputs.renderResults());
        if (!renderProduct || renderProduct->status == usd::hydra::RenderStatus::eFailed)
        {
            db.outputs.simulationTime() = state.mCoreNodeFramework->getSimTime();
            db.outputs.simulationTimeMonotonic() = state.mCoreNodeFramework->getSimTimeMonotonic();
            db.outputs.systemTime() = state.mCoreNodeFramework->getSystemTime();
            db.outputs.swhFrameNumber() = -1;
            db.outputs.rationalTimeOfSimNumerator() = 0;
            db.outputs.rationalTimeOfSimDenominator() = -1;
            db.outputs.frameNumber() = 0;
            db.outputs.durationNumerator() = 0;
            db.outputs.durationDenominator() = -1;
            db.outputs.sampleTimeOffsetInSimFrames() = 0;
            db.outputs.externalTimeOfSimNs() = -1;
            db.outputs.execOut() = ExecutionAttributeState::kExecutionAttributeStateEnabled;
            return true;
        }
        auto renderProductTimesAOV =
            omni::usd::hydra::getRenderVarFromProduct(renderProduct, db.tokens.IsaacFabricTimes.token);
        const bool inPostRenderGraph = db.inputs.gpu() > 0;
#if 0
        omni::usd::ITokenAbi* iToken = nullptr;
        iToken = carb::getCachedInterface<omni::usd::ITokenAbi>();
        if (inPostRenderGraph) std::cout << "PostRenderGraph(" << db.inputs.gpu() << ")\n";
        else std::cout << "ActionGraph\n";
        std::cout << "renderProduct->vars[\n";
        for (uint32_t i = 0; i < renderProduct->renderVarCnt; ++i)
        {
            // search cudaRsrcMap[iToken->getText(aovs[i].aov)] = renderVarData; in Graphene
            std::cout << "\t" << iToken->getText(renderProduct->vars[i].aov) << ",\n";
        }
        std::cout << "]\n";
        std::cout << "renderProduct->availableAovs.aovs[\n";
        for (uint32_t i = 0; i < renderProduct->availableAovs.aovCnt; ++i)
        {
            // search cudaRsrcMap[iToken->getText(aovs[i].aov)] = renderVarData; in Graphene
            std::cout << "\t" << iToken->getText(renderProduct->availableAovs.aovs[i]) << ",\n";
        }
        std::cout << "]\n";
#endif

        // the AOV has already been created : read the data from the AOV
        if (renderProductTimesAOV)
        {
            CARB_ASSERT(!inPostRenderGraph);
            const TimesAOV* timesAOV = static_cast<const TimesAOV*>(renderProductTimesAOV->rawResource);
            const bool validTimesAOV = !renderProductTimesAOV->isRpResource && timesAOV &&
                                       (renderProductTimesAOV->rawResourceBufferSize == sizeof(TimesAOV));
            CARB_ASSERT(validTimesAOV);
            if (!validTimesAOV)
            {
                CARB_LOG_ERROR_ONCE("OgnIsaacReadTimes : invalid IsaacFabricTimes AOV");
                return false;
            }
            db.outputs.simulationTime() = timesAOV->simulationTime;
            db.outputs.simulationTimeMonotonic() = timesAOV->simulationTimeMonotonic;
            db.outputs.systemTime() = timesAOV->systemTime;
            db.outputs.swhFrameNumber() = timesAOV->swhFrameNumber;
            db.outputs.rationalTimeOfSimNumerator() = timesAOV->rationalTimeOfSimNumerator;
            db.outputs.rationalTimeOfSimDenominator() = timesAOV->rationalTimeOfSimDenominator;
            db.outputs.frameNumber() = timesAOV->frameNumber;
            db.outputs.durationNumerator() = timesAOV->durationNumerator;
            db.outputs.durationDenominator() = timesAOV->durationDenominator;
            db.outputs.sampleTimeOffsetInSimFrames() = timesAOV->sampleTimeOffsetInSimFrames;
            db.outputs.externalTimeOfSimNs() = timesAOV->externalTimeOfSimNs;
        }
        // the AOV has not been created
        // (for the pipeline to work this is supposed to be the case only in the post-render graph)
        else
        { // read the data from fabric
            // TODO105 : uncomment this when updating to KIT 105 with asyncRendering support
            // also what about this ///< only valid if eConstantFramerateFrameNumber in
            // <rtx/hydra/FrameIdentifier.h>
            const omni::usd::hydra::FrameIdentifier& frameIdentifier = renderProduct->renderTime;

            // TODO105 assume valid sim time?
            // always valid
            const auto simTime = omni::fabric::RationalTime{ frameIdentifier.rationalTimeOfSimNumerator,
                                                             frameIdentifier.rationalTimeOfSimDenominator };
            db.outputs.simulationTime() = state.mCoreNodeFramework->getSimTimeAtTime(simTime);
            const auto durationTime = omni::fabric::RationalTime{ renderProduct->renderTime.durationNumerator,
                                                                  renderProduct->renderTime.durationDenominator };
            db.outputs.simulationTimeMonotonic() = state.mCoreNodeFramework->getSimTimeMonotonicAtTime(durationTime);
            db.outputs.systemTime() = state.mCoreNodeFramework->getSystemTimeAtTime(durationTime);
            // TODO105 The numerator does not reset.. is this really the time we want?
            db.outputs.swhFrameNumber() =
                int64_t(db.outputs.simulationTime() * double(frameIdentifier.rationalTimeOfSimDenominator));

            db.outputs.rationalTimeOfSimNumerator() = frameIdentifier.rationalTimeOfSimNumerator;
            db.outputs.rationalTimeOfSimDenominator() = frameIdentifier.rationalTimeOfSimDenominator;
            // only valid if not eNoFrameNumber
            db.outputs.frameNumber() = frameIdentifier.type == usd::hydra::FrameIdentifier::Type::eNoFrameNumber ?
                                           0 :
                                           frameIdentifier.frameNumber;
            bool validSimTime = frameIdentifier.validSimTime();
            db.outputs.durationNumerator() = validSimTime ? frameIdentifier.durationNumerator : 0;
            db.outputs.durationDenominator() = validSimTime ? frameIdentifier.durationDenominator : -1;
            db.outputs.sampleTimeOffsetInSimFrames() = validSimTime ? frameIdentifier.sampleTimeOffsetInSimFrames : -1;
            db.outputs.externalTimeOfSimNs() = validSimTime ? frameIdentifier.externalTimeOfSimNs : -1;
#if 0
                std::cout << db.outputs.simulationTime() << ", " << db.outputs.simulationTimeMonotonic() << ", "
                          << db.outputs.systemTime() << ", " << db.outputs.swhFrameNumber() << ", "
                          << db.outputs.rationalTimeOfSimNumerator() << "/" << db.outputs.rationalTimeOfSimDenominator()
                          << ", " << db.outputs.frameNumber() << ", " << db.outputs.durationNumerator() << "/"
                          << db.outputs.durationDenominator() << ", " << db.outputs.sampleTimeOffsetInSimFrames()
                          << ", " << db.outputs.externalTimeOfSimNs() << "\n";
#endif
            if (inPostRenderGraph)
            {
                // TODO 105 how many of these do we want to put in the AOV? or output at all?
                // create and fill the AOV buffer
                TimesAOV* timesAOV = static_cast<TimesAOV*>(CARB_MALLOC(sizeof(TimesAOV)));
                timesAOV->simulationTime = db.outputs.simulationTime();
                timesAOV->simulationTimeMonotonic = db.outputs.simulationTimeMonotonic();
                timesAOV->systemTime = db.outputs.systemTime();
                timesAOV->swhFrameNumber = db.outputs.swhFrameNumber();
                timesAOV->rationalTimeOfSimNumerator = db.outputs.rationalTimeOfSimNumerator();
                timesAOV->rationalTimeOfSimDenominator = db.outputs.rationalTimeOfSimDenominator();
                timesAOV->frameNumber = db.outputs.frameNumber();
                timesAOV->durationNumerator = db.outputs.durationNumerator();
                timesAOV->durationDenominator = db.outputs.durationDenominator();
                timesAOV->sampleTimeOffsetInSimFrames = db.outputs.sampleTimeOffsetInSimFrames();
                timesAOV->externalTimeOfSimNs = db.outputs.externalTimeOfSimNs();

                // setup the AOV in the render results
                usd::hydra::HydraRenderVar* newRenderVars =
                    new usd::hydra::HydraRenderVar[renderProduct->renderVarCnt + 1];
                const size_t renderVarArraySize = sizeof(usd::hydra::HydraRenderVar) * renderProduct->renderVarCnt;
                std::memcpy(newRenderVars, renderProduct->vars, renderVarArraySize);
                newRenderVars[renderProduct->renderVarCnt].aov = db.tokens.IsaacFabricTimes.token;
                newRenderVars[renderProduct->renderVarCnt].isRpResource = false;
                newRenderVars[renderProduct->renderVarCnt].isBufferRpResource = false;
                newRenderVars[renderProduct->renderVarCnt].rawResource = timesAOV;
                newRenderVars[renderProduct->renderVarCnt].rawResourceBufferSize = sizeof(TimesAOV);
                newRenderVars[renderProduct->renderVarCnt].isFrameLifetimeRsrc = true;
                delete[] renderProduct->vars;
                renderProduct->vars = newRenderVars;
                renderProduct->renderVarCnt++;
            }
        }

        db.outputs.execOut() = ExecutionAttributeState::kExecutionAttributeStateEnabled;
        return true;
    }
};

REGISTER_OGN_NODE()
}
}
}
