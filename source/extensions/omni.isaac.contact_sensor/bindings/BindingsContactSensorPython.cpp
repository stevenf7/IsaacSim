// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//


#include <carb/BindingsPythonUtils.h>

#include <omni/isaac/contact_sensor/ContactSensor.h>
#include <pybind11/pybind11/functional.h>
#include <pybind11/pybind11/numpy.h>
#include <pybind11/pybind11/pybind11.h>
#include <pybind11/pybind11/stl.h>

#include <string>
CARB_BINDINGS("omni.isaac.contact_sensor.python")


namespace omni
{
namespace isaac
{
namespace contact_sensor
{
// Recreate CsRawData casting body0 and body1 to uintptr_t to pass through pybind pipeline. This allows for numpy arrays
// to be sent over with the body names pointers.
struct CsRawPython
{
    float time; //<! Simulation timestamp
    uintptr_t body0; //<! First body on contact
    uintptr_t body1; //<! Second body on contact
    carb::Float3 position; //<! Contact Position, in world coordinates
    carb::Float3 normal; //<! Contact Normal, in world coordinates
    carb::Float3 impulse; //<! Contact Impulse, in world coordinates
};

}
}
}

namespace
{
namespace py = pybind11;

PYBIND11_MODULE(_contact_sensor, m)
{


    using namespace carb;
    using namespace omni::isaac::contact_sensor;

    py::class_<CsRawPython>(m, "CsRawData", "Contact Raw Data")
        .def(py::init<>())
        .def_readwrite("time", &CsRawPython::time, "time, (:obj:`float`)")
        .def_readonly("body0", &CsRawPython::body0, "Body 0 name handle, (:obj:`int`)")
        .def_readonly("body1", &CsRawPython::body1, "Body 1 name handle, (:obj:`int`)")
        .def_readwrite("position", &CsRawPython::position, "position, global coordinates, (:obj:`carb.Float3`)")
        .def_readwrite("normal", &CsRawPython::normal, "normal, global coordinates , (:obj:`carb.Float3`)")
        .def_readwrite("impulse", &CsRawPython::impulse, "impulse, global coordinates , (:obj:`carb.Float3`)");


    // PYBIND11_NUMPY_DTYPE(carb::Float3, x, y, z);
    // PYBIND11_NUMPY_DTYPE(CsRawData, time, body0, body1, position, normal, impulse);

    py::class_<CsProperties>(m, "SensorProperties", "Sensor Properties")
        .def(py::init<>())
        .def_readwrite("position", &CsProperties::position,
                       "Position relative to the parent body where the sensor is placed. (:obj:`carb.Float3`)")
        .def_readwrite("radius", &CsProperties::radius,
                       "Sensor radius. Negative values indicate it's a full body sensor. (:obj:`float`)")
        .def_readwrite("minThreshold", &CsProperties::minThreshold,
                       "Sensor radius. Negative values indicate it's a full body sensor. (:obj:`float`)")
        .def_readwrite("maxThreshold", &CsProperties::maxThreshold,
                       "Sensor radius. Negative values indicate it's a full body sensor. (:obj:`float`)")
        .def_readwrite("sensorPeriod", &CsProperties::sensorPeriod,
                       "Sensor reading period in seconds. zero means sync with simulation timestep (:obj:`float`)");

    py::class_<CsReading>(m, "SensorReading", "Sensor Reading")
        .def(py::init<>())
        .def_readwrite("time", &CsReading::time, "timestamp of the reading, in seconds . (:obj:`float`)")
        .def_readwrite("value", &CsReading::value, "sensor force reading value. (:obj:`float`)")
        .def_readwrite(
            "inContact", &CsReading::inContact, "boolean that flags if the sensor registers a contact. (:obj:`bool`)");

    PYBIND11_NUMPY_DTYPE(CsReading, time, value, inContact);
    PYBIND11_NUMPY_DTYPE(CsRawPython, time, body0, body1, position, normal, impulse);

    m.doc() = R"pbdoc(
    This Extension provides an interface to 'omni.isaac.contact_sensor' to be used in a stage. 
    )pbdoc";

    m.attr("INVALID_HANDLE") = py::int_(kCsInvalidHandle);

    defineInterfaceClass<ContactSensorInterface>(
        m, "ContactSensorInterface", "acquire_contact_sensor_interface", "release_contact_sensor_interface")
        .def("get_num_sensors_on_body", wrapInterfaceFunction(&ContactSensorInterface::getNumSensorsOnBody), R"pbdoc(
        Args:
            arg0 (:obj:`str`): USD Path to body as string

        Returns:
            :obj:`int`: The number of sensors attached to body.)pbdoc")
        .def("get_sensors_on_body",
             [](const ContactSensorInterface* li, const char* body_path) -> py::object {
                 if (!li)
                     return py::none();
                 size_t num_data = 0;
                 CsHandle* data = li->getSensorsOnBody(body_path, num_data);
                 return py::array(py::buffer_info(data, sizeof(CsHandle), py::format_descriptor<CsHandle>::value, 1,
                                                  { num_data }, { sizeof(CsHandle) }));
             },
             R"pbdoc(
                Args:
                    arg0 (:obj:`str`): USD Path to body as string
                Returns:
                    :obj:`numpy.array`: The list of sensor handles on a body.)pbdoc")
        .def("get_body_contact_raw_data",
             [](ContactSensorInterface* li, const char* body_path) -> py::object {
                 if (!li)
                     return py::none();
                 size_t num_data = 0;
                 CsRawData* data = li->getBodyCsRawData(body_path, num_data);
                 return py::array(py::buffer_info(data, sizeof(CsRawPython), py::format_descriptor<CsRawPython>::format(),
                                                  1, { num_data }, { sizeof(CsRawPython) }));
             },
             R"pbdoc(
            Args:
                arg0 (:obj:`str`): USD Path to body as string

            Returns:
                    :obj:`numpy.array`: The list of contact raw data that contains the specified body.)pbdoc")
        .def("decode_body_name", [](ContactSensorInterface* csi, uintptr_t body) { return std::string((char*)body); },
             R"pbdoc(
            Args:
                arg0 (:obj:`int`): body name handle
            Returns:
                    :obj:`str`: The body name.)pbdoc")
        .def("get_sensor_readings_size", wrapInterfaceFunction(&ContactSensorInterface::getSensorReadingsSize),
             R"pbdoc()pbdoc")
        .def("get_sensor_readings",
             [](const ContactSensorInterface* li, CsHandle sensorId) -> py::object {
                 if (!li)
                     return py::none();
                 size_t num_data = 0;
                 CsReading* data = li->getSensorReadings(sensorId, num_data);
                 return py::array(py::buffer_info(data, sizeof(CsReading), py::format_descriptor<CsReading>::format(),
                                                  1, { num_data }, { sizeof(CsReading) }));
             },
             R"pbdoc(   
            Args:
                arg0 (:obj:`int`): the sensor handle
            Returns:
                    :obj:`numpy.array`: The list of readings for the step interpolated for the sensor period.)pbdoc")
        .def("get_sensor_sim_reading", wrapInterfaceFunction(&ContactSensorInterface::getSensorSimReading),
             R"pbdoc(   
            Args:
                arg0 (:obj:`int`): the sensor handle
            Returns:
                    :obj:`numpy.array`: The reading for the current simulation time.)pbdoc")
        .def("add_sensor_on_body", wrapInterfaceFunction(&ContactSensorInterface::addSensorOnBody),
             R"pbdoc(
            Args:
                arg0 (:obj:`SensorProperties`): the sensor properties
            Returns:
                    :obj:`int`: The sensor handle)pbdoc")
        .def("remove_sensor", wrapInterfaceFunction(&ContactSensorInterface::removeSensor), R"pbdoc(Args:
                arg0 (:obj:`int`): the sensor handle
            Returns:
                    :obj:`boolean`: True if succesful, False otherwise.)pbdoc");
}
}
