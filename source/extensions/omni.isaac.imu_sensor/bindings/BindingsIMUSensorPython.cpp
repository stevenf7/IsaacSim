// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//


#include <carb/BindingsUtils.h>

#include <omni/isaac/imu_sensor/IMUSensor.h>
#include <pybind11/pybind11/functional.h>
#include <pybind11/pybind11/numpy.h>
#include <pybind11/pybind11/pybind11.h>
#include <pybind11/pybind11/stl.h>

#include <string>
CARB_BINDINGS("omni.isaac.imu_sensor.python")


namespace
{
namespace py = pybind11;

template <typename InterfaceType>
py::class_<InterfaceType> defineInterfaceClass(py::module& m,
                                               const char* className,
                                               const char* acquireFuncName,
                                               const char* releaseFuncName = nullptr,
                                               const char* docString = "")
{
    m.def(acquireFuncName,
          [](const char* pluginName, const char* libraryPath)
          {
              return libraryPath ? carb::acquireInterfaceFromLibraryForBindings<InterfaceType>(libraryPath) :
                                   carb::acquireInterfaceForBindings<InterfaceType>(pluginName);
          },
          py::arg("plugin_name") = nullptr, py::arg("library_path") = nullptr, py::return_value_policy::reference,
          "Acquire IMU Sensor interface. This is the base object that all of the IMU Sensor functions are defined on");

    if (releaseFuncName)
    {
        m.def(
            releaseFuncName, [](InterfaceType* iface) { carb::getFramework()->releaseInterface(iface); },
            "Release IMU Sensor interface. Generally this does not need to be called, the IMU Sensor interface is released on extension shutdown");
    }

    return py::class_<InterfaceType>(m, className, docString);
}


PYBIND11_MODULE(_imu_sensor, m)
{


    using namespace carb;
    using namespace omni::isaac::imu_sensor;

    auto carb_module = py::module::import("carb");
    auto numpy_common_module = py::module::import("omni.kit.numpy.common");


    // PYBIND11_NUMPY_DTYPE(carb::Float3, x, y, z);

    py::class_<IsProperties>(m, "SensorProperties", "Sensor Properties")
        .def(py::init<>())
        .def_readwrite("position", &IsProperties::position,
                       "Position relative to the parent body where the sensor is placed. (:obj:`carb.Float3`)")
        .def_readwrite(
            "orientation", &IsProperties::orientation,
            "Quaternion orientation (x,y,z,w) relative to the parent body where the sensor is placed. (:obj:`carb.Float4`)")

        .def_readwrite("sensorPeriod", &IsProperties::sensorPeriod,
                       "Sensor reading period in seconds. zero means sync with simulation timestep (:obj:`float`)");

    py::class_<IsReading>(m, "SensorReading", "Sensor Reading")
        .def(py::init<>())
        .def_readwrite("time", &IsReading::time, "timestamp of the reading, in seconds . (:obj:`float`)")
        .def_readwrite("lin_acc_x", &IsReading::lin_acc_x, "Accelerometer reading value x axis, in m/s^2. (:obj:`float`)")
        .def_readwrite("lin_acc_y", &IsReading::lin_acc_y, "Accelerometer reading value y axis, in m/s^2. (:obj:`float`)")
        .def_readwrite("lin_acc_z", &IsReading::lin_acc_z, "Accelerometer reading value z axis, in m/s^2. (:obj:`float`)")
        .def_readwrite("ang_vel_x", &IsReading::ang_vel_x, "Gyroscope reading value x axis, in rad/s. (:obj:`float`)")
        .def_readwrite("ang_vel_y", &IsReading::ang_vel_y, "Gyroscope reading value y axis, in rad/s. (:obj:`float`)")
        .def_readwrite("ang_vel_z", &IsReading::ang_vel_z, "Gyroscope reading value z axis, in rad/s. (:obj:`float`)");

    PYBIND11_NUMPY_DTYPE(IsReading, time, lin_acc_x, lin_acc_y, lin_acc_z, ang_vel_x, ang_vel_y, ang_vel_z);

    m.doc() = R"pbdoc(
    This Extension provides an interface to 'omni.isaac.imu_sensor' to be used in a stage. 
    )pbdoc";

    m.attr("INVALID_HANDLE") = py::int_(kIsInvalidHandle);

    defineInterfaceClass<IMUSensorInterface>(
        m, "IMUSensorInterface", "acquire_imu_sensor_interface", "release_imu_sensor_interface")
        .def("get_num_sensors_on_body", wrapInterfaceFunction(&IMUSensorInterface::getNumSensorsOnBody),
             R"pbdoc(
                Gets the number of sensors that were attached to the given body.
                Args:
                    arg0 (:obj:`str`): USD Path to body as string

                Returns:
                    :obj:`int`: The number of sensors attached to body.)pbdoc")
        .def("get_sensors_on_body",
             [](const IMUSensorInterface* li, const char* body_path) -> py::object
             {
                 if (!li)
                     return py::none();
                 size_t num_data = 0;
                 IsHandle* data = li->getSensorsOnBody(body_path, num_data);
                 return py::array(py::buffer_info(data, sizeof(IsHandle), py::format_descriptor<IsHandle>::value, 1,
                                                  { num_data }, { sizeof(IsHandle) }));
             },
             R"pbdoc(
                Gets the list of sensor handles attached to a given body. 
                Args:
                    arg0 (:obj:`str`): USD Path to body as string
                Returns:
                    :obj:`numpy.array`: The list of sensor handles on a body.)pbdoc")
        .def("get_sensor_readings_size", wrapInterfaceFunction(&IMUSensorInterface::getSensorReadingsSize),
             R"pbdoc(
                Gets the number of readings ready on the buffer
                Args:
                    arg0 (:obj:`int`): the sensor handle
                Returns:
                    :obj:`int`: Number of readings ready on the buffer.)pbdoc")
        .def("get_sensor_readings",
             [](const IMUSensorInterface* li, IsHandle sensorId) -> py::object
             {
                 if (!li)
                     return py::none();
                 size_t num_data = 0;
                 IsReading* data = li->getSensorReadings(sensorId, num_data);
                 return py::array(py::buffer_info(data, sizeof(IsReading), py::format_descriptor<IsReading>::format(),
                                                  1, { num_data }, { sizeof(IsReading) }));
             },
             R"pbdoc(   
                Gets the list of sensor readings for the given sensor. Clears the reading buffer once values are acquired.
                Args:
                    arg0 (:obj:`int`): the sensor handle
                Returns:
                    :obj:`numpy.array`: The list of readings for the sensor ready on the buffer.)pbdoc")
        .def("get_sensor_sim_reading", wrapInterfaceFunction(&IMUSensorInterface::getSensorSimReading),
             R"pbdoc(   
                Args:
                    arg0 (:obj:`int`): the sensor handle
                Returns:
                    :obj:`numpy.array`: The reading for the current simulation time.)pbdoc")
        .def("add_sensor_on_body", wrapInterfaceFunction(&IMUSensorInterface::addSensorOnBody),
             R"pbdoc(
                Args:
                    arg0 (:obj:`SensorProperties`): the sensor properties
                Returns:
                    :obj:`int`: The sensor handle)pbdoc")
        .def("remove_sensor", wrapInterfaceFunction(&IMUSensorInterface::removeSensor),
             R"pbdoc(
                Args:
                    arg0 (:obj:`int`): the sensor handle
                Returns:
                    :obj:`boolean`: True if succesful, False otherwise.)pbdoc");
}
}
