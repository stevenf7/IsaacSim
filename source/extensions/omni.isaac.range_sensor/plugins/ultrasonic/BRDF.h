#include <foundation/PxVec3.h>

#include <vector>

class BRDF
{
public:
    BRDF(const ::physx::PxVec3& emitterOrigin) : mEmitterOrigin(emitterOrigin)
    {
    }
    ::physx::PxVec3 getMirrorRay(const ::physx::PxVec3& normal, const ::physx::PxVec3& worldPoint) const;
    float getReturnedIntensity(const ::physx::PxVec3& receiverOrigin,
                               const ::physx::PxVec3& normal,
                               const ::physx::PxVec3& worldPoint,
                               const float incidentIntensity) const;
    std::vector<float> getReturnedIntensities(const ::physx::PxVec3& receiverOrigin,
                                              const std::vector<::physx::PxVec3>& normals,
                                              const std::vector<::physx::PxVec3>& worldPoints,
                                              const std::vector<float>& incidentIntensities) const;

private:
    ::physx::PxVec3 mEmitterOrigin;
    const float kPi = 3.141592653589f;
    const float kDegToRad = kPi / 180.0f;
    const float kRadToDeg = 180.0f / kPi;
};
