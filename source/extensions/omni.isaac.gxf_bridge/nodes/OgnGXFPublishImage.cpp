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
        const double current_time = db.inputs.timeStamp();
        if (encoding == db.tokens.Type_RGB8)
        {
            success = publishColorImageMessage<nvidia::gxf::VideoFormat::GXF_VIDEO_FORMAT_RGB>(
                db, height, width, dataAsCPU, current_time);
        }
        else if (encoding == db.tokens.Type_U8)
        {
            success = publishColorImageMessage<nvidia::gxf::VideoFormat::GXF_VIDEO_FORMAT_GRAY>(
                db, height, width, dataAsCPU, current_time);
        }
        else if (encoding == db.tokens.Type_U16)
        {
            publishColorImageMessage<nvidia::gxf::VideoFormat::GXF_VIDEO_FORMAT_GRAY16>(
                db, height, width, dataAsCPU, current_time);
        }
        else if (encoding == db.tokens.Type_F32)
        {
            success = publishDepthImage<float>(db, height, width, 1, dataAsCPU, current_time);
        }
        else
        {
            db.logError("encoding %s unknown", db.tokenToString(db.inputs.encoding()));
            return false;
        }
        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return success;
    }

private:
    template <nvidia::gxf::VideoFormat Format>
    static bool publishColorImageMessage(
        OgnGXFPublishImageDatabase& db, int height, int width, const uint8_t* dataAsCPU, double time_seconds)
    {
        auto& state = db.internalState<OgnGXFPublishImage>();
        auto maybe_message = nvidia::isaac::CreateCameraMessage<Format>(
            state.getGxfContext(), width, height, nvidia::gxf::SurfaceLayout::GXF_SURFACE_LAYOUT_PITCH_LINEAR,
            nvidia::gxf::MemoryStorageType::kHost, state.mAllocator);
        if (!maybe_message)
        {
            db.logError("Could not create image message: %d", maybe_message.error());
            return false;
        }
        auto message = std::move(maybe_message.value());
        message.timestamp->acqtime = static_cast<int64_t>(time_seconds * 1e9);
        message.timestamp->pubtime = message.timestamp->acqtime;
        // GXF VideoBuffer is strided for some resolutions so we need to be careful here.
        const size_t dst_stride = message.frame->video_frame_info().color_planes[0].stride;
        const size_t src_stride = width * message.frame->video_frame_info().color_planes[0].bytes_per_pixel;
        cudaMemcpy2D(
            message.frame->pointer(), dst_stride, &dataAsCPU[0], src_stride, src_stride, height, cudaMemcpyHostToHost);
        state.setIntrinsicsCamera(
            message.intrinsics, width, height, db.inputs.focalLength(), db.inputs.horizontalAperture(),
            db.inputs.verticalAperture(), db.tokenToString(db.inputs.projectionType()), db.inputs.cameraFisheyeParams(),
            db.tokenToString(db.inputs.physicalDistortionModel()), db.inputs.physicalDistortionCoefficients());
        for (int i = 0; i < 3; ++i)
        {
            message.extrinsics->rotation[3 * i] = 1.f;
            message.extrinsics->translation[i] = db.inputs.stereoOffset()[i];
            for (int j = 1; j < 3; ++j)
            {
                message.extrinsics->rotation[3 * i + j] = 0.f;
            }
        }
        const gxf_result_t result = state.publish(db.inputs.outputEntity(), db.inputs.outputComponent(), message.entity);
        return (result == GXF_SUCCESS);
    }

    template <typename T>
    static bool publishDepthImage(
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
        state.setIntrinsicsCameraImage(
            message.intrinsics_info, message.distortion_info, width, height, db.inputs.focalLength(),
            db.inputs.horizontalAperture(), db.inputs.verticalAperture(), db.tokenToString(db.inputs.projectionType()),
            db.inputs.cameraFisheyeParams(), db.tokenToString(db.inputs.physicalDistortionModel()),
            db.inputs.physicalDistortionCoefficients());

        const size_t totalBytes = height * width * sizeof(T) * channels;
        memcpy(static_cast<T*>(message.image_tensor_view.element_wise_begin()), &dataAsCPU[0], totalBytes);

        const gxf_result_t result = state.publish(db.inputs.outputEntity(), db.inputs.outputComponent(), message.entity);
        return (result == GXF_SUCCESS);
    }

    double getCurrentTime()
    {
        return mClock->time();
    }

    void setMetadata(const double time_seconds, const nvidia::gxf::Handle<nvidia::gxf::Timestamp>& msgTimestamp)
    {
        msgTimestamp->pubtime = static_cast<int64_t>(time_seconds * 1e9);
        msgTimestamp->acqtime = static_cast<int64_t>(time_seconds * 1e9);
    }

    void setIntrinsicsCameraImage(const nvidia::gxf::Handle<::isaac::geometry::PinholeD>& intrinsics,
                                  const nvidia::gxf::Handle<::isaac::geometry::CameraDistortionInfo>& distIntrinsics,
                                  const int width,
                                  const int height,
                                  float focalLength,
                                  float horizontalAperture,
                                  float verticalAperture,
                                  const std::string projectionType,
                                  const omni::graph::core::ogn::const_array<float>& cameraFisheyeParams,
                                  const std::string physicalDistortionModel,
                                  const omni::graph::core::ogn::const_array<float>& physicalDistortionCoefficients)
    {
        intrinsics->dimensions[0] = height; // rows
        intrinsics->dimensions[1] = width; // columns
        intrinsics->focal[0] = height * focalLength / verticalAperture;
        intrinsics->focal[1] = width * focalLength / horizontalAperture;
        intrinsics->center[0] = height * 0.5;
        intrinsics->center[1] = width * 0.5;
        if (physicalDistortionModel.find("rationalPolynomial") != std::string::npos &&
            physicalDistortionCoefficients.size() == 8)
        {

            distIntrinsics->model = ::isaac::geometry::DistortionModel::kPolynomial;
            auto data = physicalDistortionCoefficients.data();
            const std::array<double, ::isaac::geometry::CameraDistortionInfo::kMaxNumCoefficients> distortionCoefficients{
                data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7]
            };
            distIntrinsics->distortion_coefficients = distortionCoefficients;
        }
        else
        {
            if (cameraFisheyeParams.size() == 19)
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

            distIntrinsics->model = (projectionType.find("fisheye") != std::string::npos ?
                                         ::isaac::geometry::DistortionModel::kFisheye :
                                         ::isaac::geometry::DistortionModel::kPerspective);
        }
    }

    void setIntrinsicsCamera(const nvidia::gxf::Handle<nvidia::gxf::CameraModel>& intrinsics,
                             const int width,
                             const int height,
                             float focalLength,
                             float horizontalAperture,
                             float verticalAperture,
                             const std::string projectionType,
                             const omni::graph::core::ogn::const_array<float>& cameraFisheyeParams,
                             const std::string physicalDistortionModel,
                             const omni::graph::core::ogn::const_array<float>& physicalDistortionCoefficients)
    {
        intrinsics->dimensions.x = height; // rows
        intrinsics->dimensions.y = width; // columns
        intrinsics->focal_length.x = height * focalLength / verticalAperture;
        intrinsics->focal_length.y = width * focalLength / horizontalAperture;
        intrinsics->principal_point.x = height * 0.5;
        intrinsics->principal_point.y = width * 0.5;
        intrinsics->skew_value = 0.0;

        if (physicalDistortionModel.find("rationalPolynomial") != std::string::npos &&
            physicalDistortionCoefficients.size() == intrinsics->kMaxDistortionCoefficients)
        {
            intrinsics->distortion_type = nvidia::gxf::DistortionType::Polynomial;
            for (int i = 0; i < intrinsics->kMaxDistortionCoefficients; i++)
            {
                intrinsics->distortion_coefficients[i] = physicalDistortionCoefficients[i];
            }
        }
        else
        {
            if (cameraFisheyeParams.size() == 19)
            {
                for (int i = 0; i < 5; i++)
                {
                    intrinsics->distortion_coefficients[i] = cameraFisheyeParams[i + 5];
                }
                for (int i = 5; i < intrinsics->kMaxDistortionCoefficients; i++)
                {
                    intrinsics->distortion_coefficients[i] = 0.0;
                }
            }
            else
            {
                for (int i = 0; i < intrinsics->kMaxDistortionCoefficients; i++)
                {
                    intrinsics->distortion_coefficients[i] = 0.0;
                }
            }

            intrinsics->distortion_type =
                (projectionType.find("fisheye") != std::string::npos ? nvidia::gxf::DistortionType::FisheyeEquidistant :
                                                                       nvidia::gxf::DistortionType::Perspective);
        }
    }
};

REGISTER_OGN_NODE()
