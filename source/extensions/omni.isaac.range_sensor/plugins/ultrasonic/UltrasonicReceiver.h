#include <foundation/PxVec3.h>

#include <vector>

class UltrasonicReceiver
{
public:
    UltrasonicReceiver(const ::physx::PxVec3& receiverOrigin) : mReceiverOrigin(receiverOrigin){};
    std::vector<float> getIndirectIntensities(const ::physx::PxVec3& emitterOrigin,
                                              const std::vector<::physx::PxVec3>& worldPoints);
    std::vector<float> getTotalPathLength(const ::physx::PxVec3& emitterOrigin,
                                          const std::vector<::physx::PxVec3>& worldPoints);

private:
    const ::physx::PxVec3& mReceiverOrigin;
};
