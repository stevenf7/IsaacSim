// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <carb/graphics/GraphicsTypes.h>

#include <omni/isaac/utils/Buffer.h>
#include <omni/isaac/utils/ScopedCudaDevice.h>
#include <plugins/Core/GxfNode.h>

#include <OgnGXFPublishImageDatabase.h>
using namespace omni::isaac::gxf_bridge;

extern "C" void textureFloatCopyToRawBuffer(cudaTextureObject_t, uint8_t*, uint32_t, uint32_t, cudaStream_t);


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

        // get inputs
        auto encoding = db.inputs.encoding();
        int width = static_cast<int>(db.inputs.width()); // Eigen types define scalar as int
        int height = static_cast<int>(db.inputs.height());

        if (db.inputs.cudaDeviceIndex() == -1)
        {
            if (db.inputs.dataPtr() != 0 && db.inputs.bufferSize() > 0)
            {
                // Data is on host as ptr, buffer size matches
                state.mDataOnCPU.resize(db.inputs.bufferSize());
                memcpy(state.mDataOnCPU.data(), reinterpret_cast<void*>(db.inputs.dataPtr()), db.inputs.bufferSize());
            }
            else if (db.inputs.dataPtr() == 0 && db.inputs.data.size() > 0)
            {
                // data is on host as ogn data, copy from cpu
                state.mDataOnCPU.resize(db.inputs.data.size());
                memcpy(state.mDataOnCPU.data(), reinterpret_cast<const uint8_t*>(db.inputs.data.cpu().data()),
                       db.inputs.data.size());
            }
            else
            {
                db.logError("dataPtr null and data has size zero");
                return false;
            }
        }
        else
        {
            omni::isaac::utils::ScopedDevice(db.inputs.cudaDeviceIndex());

            if (db.inputs.bufferSize() == 0)
            {
                omni::isaac::utils::ScopedCudaTextureObject srcTexObj(
                    reinterpret_cast<cudaMipmappedArray_t>(db.inputs.dataPtr()), 0);
                switch (static_cast<carb::graphics::Format>(db.inputs.format()))
                {
                case carb::graphics::Format::eR32_SFLOAT:
                {
                    state.mBuffer.setDevice(db.inputs.cudaDeviceIndex());
                    state.mBuffer.resize(db.inputs.width() * db.inputs.height() * sizeof(float));
                    textureFloatCopyToRawBuffer(srcTexObj, state.mBuffer.data(), width, height, 0);
                    CUDA_CHECK(cudaGetLastError());
                    auto src = reinterpret_cast<void*>(state.mBuffer.data());
                    state.mDataOnCPU.resize(db.inputs.width() * db.inputs.height() * sizeof(float));
                    CUDA_CHECK(cudaMemcpy(state.mDataOnCPU.data(), src,
                                          db.inputs.width() * db.inputs.height() * sizeof(float), cudaMemcpyDeviceToHost));
                }
                break;

                default:
                    CARB_LOG_ERROR("SdRenderVarToRawArray : input texture format (%d) is not supported.",
                                   static_cast<int>(db.inputs.format()));
                    return false;
                }
            }
            else
            {
                state.mDataOnCPU.resize(db.inputs.bufferSize());
                CUDA_CHECK(cudaMemcpy(state.mDataOnCPU.data(), reinterpret_cast<void*>(db.inputs.dataPtr()),
                                      db.inputs.bufferSize(), cudaMemcpyDeviceToHost));
            }
        }

        bool success = false;
        const double current_time = db.inputs.timeStamp();
        if (encoding == db.tokens.Type_RGB8)
        {
            success = publishColorImage<nvidia::gxf::VideoFormat::GXF_VIDEO_FORMAT_RGB>(
                db, height, width, state.mDataOnCPU.data(), current_time);
        }
        else if (encoding == db.tokens.Type_U8)
        {
            success = publishColorImage<nvidia::gxf::VideoFormat::GXF_VIDEO_FORMAT_GRAY>(
                db, height, width, state.mDataOnCPU.data(), current_time);
        }
        else if (encoding == db.tokens.Type_U16)
        {
            publishColorImage<nvidia::gxf::VideoFormat::GXF_VIDEO_FORMAT_GRAY16>(
                db, height, width, state.mDataOnCPU.data(), current_time);
        }
        else if (encoding == db.tokens.Type_F32)
        {
            success = publishDepthImage<float>(db, height, width, 1, state.mDataOnCPU.data(), current_time);
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
    static bool publishColorImage(
        OgnGXFPublishImageDatabase& db, int height, int width, const uint8_t* dataAsCPU, double time_seconds)
    {
        auto& state = db.internalState<OgnGXFPublishImage>();
        // Create Camera message
        auto maybe_message = nvidia::isaac::CreateCameraMessage<Format>(
            state.getGxfContext(), width, height, nvidia::gxf::SurfaceLayout::GXF_SURFACE_LAYOUT_PITCH_LINEAR,
            nvidia::gxf::MemoryStorageType::kHost, state.mAllocator);
        if (!maybe_message)
        {
            db.logError("Could not create image message: %d", maybe_message.error());
            return false;
        }
        auto message = std::move(maybe_message.value());

        // Populate timestamp
        message.timestamp->acqtime = static_cast<int64_t>(time_seconds * 1e9);
        message.timestamp->pubtime = message.timestamp->acqtime;

        // Populate VideoBuffer
        // Note: VideoBuffer is strided for some resolutions so we need to be careful here.
        const size_t dst_stride = message.frame->video_frame_info().color_planes[0].stride;
        const size_t src_stride = width * message.frame->video_frame_info().color_planes[0].bytes_per_pixel;
        cudaMemcpy2D(
            message.frame->pointer(), dst_stride, &dataAsCPU[0], src_stride, src_stride, height, cudaMemcpyHostToHost);

        // Populate intrinsics
        const auto& focalLength = db.inputs.focalLength();
        const auto& horizontalAperture = db.inputs.horizontalAperture();
        const auto& verticalAperture = db.inputs.verticalAperture();
        const auto& cameraFisheyeParams = db.inputs.cameraFisheyeParams();
        const std::string projectionType = db.tokenToString(db.inputs.projectionType());
        const std::string physicalDistortionModel = db.tokenToString(db.inputs.physicalDistortionModel());

        if (physicalDistortionModel.find("rationalPolynomial") != std::string::npos)
        {
            auto fthetaWidth = cameraFisheyeParams[0];
            auto fthetaHeight = cameraFisheyeParams[1];
            auto fthetaCx = cameraFisheyeParams[2];
            auto fthetaCy = cameraFisheyeParams[3];

            message.intrinsics->dimensions.x = fthetaWidth;
            message.intrinsics->dimensions.y = fthetaHeight;
            message.intrinsics->focal_length.x = fthetaWidth * focalLength / horizontalAperture;
            message.intrinsics->focal_length.y = fthetaHeight * focalLength / verticalAperture;
            message.intrinsics->principal_point.x = fthetaCx;
            message.intrinsics->principal_point.y = fthetaCy;
            message.intrinsics->skew_value = 0.0;
            message.intrinsics->distortion_type = nvidia::gxf::DistortionType::Polynomial;

            const auto& physicalDistortionCoefficients = db.inputs.physicalDistortionCoefficients();
            for (int i = 0; i < message.intrinsics->kMaxDistortionCoefficients; i++)
            {
                message.intrinsics->distortion_coefficients[i] = physicalDistortionCoefficients[i];
            }
        }
        else if (projectionType.find("pinhole") != std::string::npos)
        {
            message.intrinsics->dimensions.x = width;
            message.intrinsics->dimensions.y = height;
            message.intrinsics->focal_length.x = width * focalLength / horizontalAperture;
            message.intrinsics->focal_length.y = height * focalLength / verticalAperture;
            message.intrinsics->principal_point.x = width * 0.5;
            message.intrinsics->principal_point.y = height * 0.5;
            message.intrinsics->skew_value = 0.0;
            message.intrinsics->distortion_type = nvidia::gxf::DistortionType::Perspective;
            for (int i = 0; i < message.intrinsics->kMaxDistortionCoefficients; i++)
            {
                message.intrinsics->distortion_coefficients[i] = 0.0;
            }
        }
        else if (projectionType.find("fisheye") != std::string::npos)
        {
            auto fthetaWidth = cameraFisheyeParams[0];
            auto fthetaHeight = cameraFisheyeParams[1];
            auto fthetaCx = cameraFisheyeParams[2];
            auto fthetaCy = cameraFisheyeParams[3];

            message.intrinsics->dimensions.x = fthetaWidth;
            message.intrinsics->dimensions.y = fthetaHeight;
            message.intrinsics->focal_length.x = fthetaWidth * focalLength / horizontalAperture;
            message.intrinsics->focal_length.y = fthetaHeight * focalLength / verticalAperture;
            message.intrinsics->principal_point.x = fthetaCx;
            message.intrinsics->principal_point.y = fthetaCy;
            message.intrinsics->skew_value = 0.0;
            message.intrinsics->distortion_type = nvidia::gxf::DistortionType::FisheyeEquidistant;
            for (int i = 0; i < 5; i++)
            {
                message.intrinsics->distortion_coefficients[i] = cameraFisheyeParams[i + 5];
            }
            for (int i = 5; i < message.intrinsics->kMaxDistortionCoefficients; i++)
            {
                message.intrinsics->distortion_coefficients[i] = 0.0;
            }
        }
        else
        {
            db.logError("Unexpected projection type: %s", projectionType);
            return false;
        }

        // Populate extrinsics
        for (int i = 0; i < 3; ++i)
        {
            message.extrinsics->translation[i] = db.inputs.stereoOffset()[i];
            for (int j = 0; j < 3; ++j)
            {
                message.extrinsics->rotation[3 * i + j] = i == j ? 1 : 0;
            }
        }

        // Publish message
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

    void setMetadata(const double time_seconds, const nvidia::gxf::Handle<nvidia::gxf::Timestamp>& msgTimestamp)
    {
        msgTimestamp->pubtime = static_cast<int64_t>(time_seconds * 1e9);
        msgTimestamp->acqtime = static_cast<int64_t>(time_seconds * 1e9);
    }

    void setIntrinsicsCameraImage(const nvidia::gxf::Handle<::nvidia::isaac::geometry::PinholeD>& intrinsics,
                                  const nvidia::gxf::Handle<::nvidia::isaac::geometry::CameraDistortionInfo>& distIntrinsics,
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

            distIntrinsics->model = ::nvidia::isaac::geometry::DistortionModel::kPolynomial;
            auto data = physicalDistortionCoefficients.data();
            const std::array<double, ::nvidia::isaac::geometry::CameraDistortionInfo::kMaxNumCoefficients>
                distortionCoefficients{ data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7] };
        }
        else
        {
            if (cameraFisheyeParams.size() == 19)
            {
                auto data = cameraFisheyeParams.data();
                const std::array<double, ::nvidia::isaac::geometry::CameraDistortionInfo::kMaxNumCoefficients>
                    distortionCoefficients{ data[5], data[6], data[7], data[8], data[9] };
                distIntrinsics->distortion_coefficients = distortionCoefficients;
            }
            else
            {
                const std::array<double, ::nvidia::isaac::geometry::CameraDistortionInfo::kMaxNumCoefficients>
                    distortionCoefficients{ 0, 0, 0, 0, 0 };
                distIntrinsics->distortion_coefficients = distortionCoefficients;
            }

            distIntrinsics->model = (projectionType.find("fisheye") != std::string::npos ?
                                         ::nvidia::isaac::geometry::DistortionModel::kFisheye :
                                         ::nvidia::isaac::geometry::DistortionModel::kPerspective);
        }
    }
    omni::isaac::utils::DeviceBuffer mBuffer;
    omni::isaac::utils::HostBuffer mDataOnCPU;
};

REGISTER_OGN_NODE()
