// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <carb/graphics/GraphicsTypes.h>

#include <plugins/Core/GxfNode.h>

#include <OgnGXFPublishImageDatabase.h>
using namespace omni::isaac::gxf_bridge;


class OgnGXFPublishImage : public GxfNode
{
public:
    static bool compute(OgnGXFPublishImageDatabase& db)
    {
        auto& state = db.internalState<OgnGXFPublishImage>();
        if (!state.getGxfContext())
        {
            if (state.setGxfContext(db.inputs.context()) != GXF_SUCCESS)
            {
                return false;
            }
            return true;
        }
        auto encoding = db.inputs.encoding();
        int width = static_cast<int>(db.inputs.width()); // Eigen types define scalar as int
        int height = static_cast<int>(db.inputs.height());
        const uint8_t* dataAsCPU = reinterpret_cast<const uint8_t*>(db.inputs.data.cpu().data());
        bool success = false;
        const double current_time = state.getCurrentTime();
        if (encoding == db.tokens.Type_RGB8)
        {
            success = publishImage<uint8_t>(db, height, width, 3, dataAsCPU, current_time);
        }
        else if (encoding == db.tokens.Type_U8)
        {
            success = publishImage<uint8_t>(db, height, width, 1, dataAsCPU, current_time);
        }
        else if (encoding == db.tokens.Type_U16)
        {
            success = publishImage<uint16_t>(db, height, width, 1, dataAsCPU, current_time);
        }
        else if (encoding == db.tokens.Type_F32)
        {
            success = publishImage<float>(db, height, width, 1, dataAsCPU, current_time);
        }
        else
        {
            db.logError("encoding, %d", db.tokenToString(db.inputs.encoding()));
            return false;
        }
        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return success;
    }

private:
    template <typename T>
    static bool publishImage(
        OgnGXFPublishImageDatabase& db, int height, int width, int channels, const uint8_t* dataAsCPU, double time)
    {
        auto& state = db.internalState<OgnGXFPublishImage>();
        auto maybe_message = nvidia::isaac::CreateCameraImageMessage<T>(
            state.getGxfContext(), state.mAllocator, { height, width, channels });
        if (!maybe_message)
        {

            db.logError("could not create image message, %d", maybe_message.error());
            return false;
        }
        auto message = std::move(maybe_message.value());
        state.setMetadata(time, message.timestamp);
        const std::string frame_name = db.inputs.poseFrame();
        message.pose_frame_uid->uid = state.findFrameUid(frame_name.c_str());
        state.setIntrinsics(message.intrinsics_info, message.distortion_info, width, height, db.inputs.focalLength(),
                            db.inputs.horizontalAperture(), db.inputs.verticalAperture(),
                            db.tokenToString(db.inputs.projectionType()), db.inputs.cameraFisheyeParams());

        const size_t totalBytes = height * width * sizeof(T) * channels;
        memcpy(static_cast<T*>(message.image_tensor_view.element_wise_begin()), &dataAsCPU[0], totalBytes);

        const gxf_result_t result = state.publish(db.inputs.outputEntity(), db.inputs.outputComponent(), message.entity);
        return (result == GXF_SUCCESS);
    }

    double getCurrentTime()
    {
        return mClock->time();
    }

    void setMetadata(const double timestamp, const nvidia::gxf::Handle<nvidia::gxf::Timestamp>& msgTimestamp)
    {
        msgTimestamp->pubtime = static_cast<int64_t>(timestamp * 1e9);
        msgTimestamp->acqtime = static_cast<int64_t>(timestamp * 1e9);
    }

    void setIntrinsics(const nvidia::gxf::Handle<::isaac::geometry::PinholeD>& intrinsics,
                       const nvidia::gxf::Handle<::isaac::geometry::CameraDistortionInfo>& distIntrinsics,
                       const int width,
                       const int height,
                       float focalLength,
                       float horizontalAperture,
                       float verticalAperture,
                       const std::string projectionType,
                       const omni::graph::core::ogn::const_array<float>& cameraFisheyeParams)
    {
        intrinsics->dimensions[0] = height; // rows
        intrinsics->dimensions[1] = width; // columns
        intrinsics->focal[0] = height * focalLength / verticalAperture;
        intrinsics->focal[1] = width * focalLength / horizontalAperture;
        intrinsics->center[0] = height * 0.5;
        intrinsics->center[1] = width * 0.5;
        if (cameraFisheyeParams.size() == 10)
        {
            auto data = cameraFisheyeParams.data();
            const std::array<double, ::isaac::geometry::CameraDistortionInfo::kMaxNumCoefficients> distortionCoefficients{
                data[5], data[6], data[7], data[8], data[9]
            };
            distIntrinsics->distortion_coefficients = distortionCoefficients;
        }
        else
        {
            const std::array<double, ::isaac::geometry::CameraDistortionInfo::kMaxNumCoefficients> distortionCoefficients{
                0, 0, 0, 0, 0
            };
            distIntrinsics->distortion_coefficients = distortionCoefficients;
        }

        distIntrinsics->model =
            (projectionType.find("fisheye") != std::string::npos ? ::isaac::geometry::DistortionModel::kFisheye :
                                                                   ::isaac::geometry::DistortionModel::kPerspective);
    }
};

REGISTER_OGN_NODE()
