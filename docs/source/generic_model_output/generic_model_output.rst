.. _generic_model_output:

GenericModelOutput
==================

``GenericModelOutput`` is a common data structure that is used by all sensor extensions to represent the output of the sensor.
The output is defined according to `ISO8855 <https://www.iso.org/obp/ui/#iso:std:iso:8855:ed-2:v1:en:en?>`_ sensor frame, which means the following:

  - Angles are in degrees from [-180, 180] for azimuth and [-90, 90] for elevation in a right-handed coordinate system.
  - Front is +x, left is +y, up is +z.

.. image:: iso8855.png
   :alt: ISO8855 coordinate system


Structure Output Members
------------------------
The following table summarizes the members of the ``GenericModelOutput`` structure.


+-------------------------------+-------------------------+----------------------------------------------------------+
| Attribute                     | Type                    | Description                                              |
+===============================+=========================+==========================================================+
| magicNumber                   | uint32_t                | A unique identifier for the output. Should reflect       |
|                               |                         | ``0x4E474D4F``, which is the ASCII for "NGMO".           |
+-------------------------------+-------------------------+----------------------------------------------------------+
| majorVersion                  | uint32_t                | The major version number of the model output.            |
+-------------------------------+-------------------------+----------------------------------------------------------+
| minorVersion                  | uint32_t                | The minor version number of the model output.            |
+-------------------------------+-------------------------+----------------------------------------------------------+
| patchVersion                  | uint32_t                | The patch version number of the model output.            |
+-------------------------------+-------------------------+----------------------------------------------------------+
| sizeInBytes                   | uint64_t                | The size in bytes of the contiguous buffer of the        |
|                               |                         | model output (incl. the struct itself).                  |
+-------------------------------+-------------------------+----------------------------------------------------------+
| numElements                   | uint32_t                | The number of elements in the array members of the       |
|                               |                         | model output.                                            |
+-------------------------------+-------------------------+----------------------------------------------------------+
| frameOfReference              | FrameOfReference        | The frame of reference for the model output.             |
|                               |                         | Can be ``FrameOfReference::SENSOR``,                     |
|                               |                         | ``FrameOfReference::PARENT``,``FrameOfReference::WORLD``,|
|                               |                         | or ``FrameOfReference::CUSTOM``. The default value is    |
|                               |                         | ``FrameOfReference::SENSOR``.                            |
+-------------------------------+-------------------------+----------------------------------------------------------+
| motionCompensationState       | MotionCompensationState | The motion compensation state for the model output.      |
|                               |                         | Can be ``MotionCompensationState::NONCOMPENSATED``,      |
|                               |                         | ``MotionCompensationState::COMPENSATED``, or             |
|                               |                         | ``MotionCompensationState::NOT_APPLICABLE``.             |
|                               |                         | The default value is                                     |
|                               |                         | ``MotionCompensationState::NOT_APPLICABLE``.             |
+-------------------------------+-------------------------+----------------------------------------------------------+
| frameId                       | uint64_t                | The model (simulation) frame ID of the model output.     |
+-------------------------------+-------------------------+----------------------------------------------------------+
| timestampNs                   | uint64_t                | The timestamp of the model output in nanoseconds.        |
+-------------------------------+-------------------------+----------------------------------------------------------+
| coordsType                    | CoordsType              | The type of coordinates used in the model output.        |
|                               |                         | Can be ``CoordsType::SPHERICAL`` or                      |
|                               |                         | ``CoordsType::CARTESIAN``. The default value is          |
|                               |                         | ``CoordsType::SPHERICAL``.                               |
+-------------------------------+-------------------------+----------------------------------------------------------+
| outputType                    | OutputType              | The type of output.                                      |
|                               |                         | The default value is ``OutputType::POINTCLOUD``.         |
+-------------------------------+-------------------------+----------------------------------------------------------+
| modelToAppTransform           | float[16]               | A transformation matrix that transforms from the model's |
|                               |                         | coordinate system to the application's coordinate system.|
+-------------------------------+-------------------------+----------------------------------------------------------+
| frameStart                    | FrameAtTime             | The start frame of the model output. It transforms from  |
|                               |                         | the model's coordinate system to the global coordinate   |
|                               |                         | system at frame start time.                              |
+-------------------------------+-------------------------+----------------------------------------------------------+
| frameEnd                      | FrameAtTime             | The end frame of the model output. It transforms from the|
|                               |                         | model's coordinate system to the global coordinate system|
|                               |                         | at frame end time.                                       |
+-------------------------------+-------------------------+----------------------------------------------------------+
| auxType                       | AuxType                 | The specific level of auxiliary data. The default value  |
|                               |                         | is ``AuxType::NONE`` for no auxilary data. See below for |
|                               |                         | more information.                                        |
+-------------------------------+-------------------------+----------------------------------------------------------+
| modality                      | Modality                | The modality which produced this output. The default     |
|                               |                         | value is ``Modality::UNDEFINED``. See below for more     |
|                               |                         | information.                                             |
+-------------------------------+-------------------------+----------------------------------------------------------+
| elements                      | BasicElements           | The basic elements of the model output.                  |
|                               |                         | See below for more information.                          |
+-------------------------------+-------------------------+----------------------------------------------------------+
| auxiliaryData                 | void*                   | A pointer to the auxiliary data. This may not be filled. |
|                               |                         | Can be ``AuxType::NONE``, ``AuxType::BASIC``,            |
|                               |                         | ``AuxType::EXTRA``, or ``AuxType::FULL``. See below      |
|                               |                         | for more information.                                    |
+-------------------------------+-------------------------+----------------------------------------------------------+



BasicElements
^^^^^^^^^^^^^

This table represents the basic elements of the model output.

+-------------------------------+-------------------------+----------------------------------------------------------+
| Attribute                     | Type                    | Description                                              |
+===============================+=========================+==========================================================+
| timeOffsetNs                  | int32_t*                | The offset time of this element with respect to the      |
|                               |                         | parent GenericModelOutput structure's timestampNs.       |
+-------------------------------+-------------------------+----------------------------------------------------------+
| x                             | float*                  | Azimuth in degrees [-180,180] or Cartesian x in m.       |
+-------------------------------+-------------------------+----------------------------------------------------------+
| y                             | float*                  | Elevation in degrees or Cartesian y in m.                |
+-------------------------------+-------------------------+----------------------------------------------------------+
| z                             | float*                  | Distance in m or Cartesian z in m.                       |
+-------------------------------+-------------------------+----------------------------------------------------------+
| scalar                        | float*                  | Sensor modality specific output scalar.                  |
|                               |                         | Lidar and Ultrasonic give a normalized scaled value      |
|                               |                         | (check modality specific documentation for more details).|
|                               |                         | Radar fills an RCS value in dBsm.                        |
+-------------------------------+-------------------------+----------------------------------------------------------+
| flags                         | uint8_t*                | Sensor specific flags representing ElementFlags enum     |
|                               |                         | values, eg. element validity.                            |
+-------------------------------+-------------------------+----------------------------------------------------------+



FrameAtTime
^^^^^^^^^^^

This table represents a frame at a specific time.

+-------------------------------+-------------------------+----------------------------------------------------------+
| Attribute                     | Type                    | Description                                              |
+===============================+=========================+==========================================================+
| timestampNs                   | uint64_t                | The timestamp of the frame in nanoseconds. The default   |
|                               |                         | value is ``0UL``.                                        |
+-------------------------------+-------------------------+----------------------------------------------------------+
| orientation                   | float4                  | The quaternion orientation of the frame.                 |
+-------------------------------+-------------------------+----------------------------------------------------------+
| posM                          | float3                  | The position of the frame in meters.                     |
+-------------------------------+-------------------------+----------------------------------------------------------+
| padding                       | uint8_t[4]              | Padding to align the structure to a multiple of 8 bytes. |
+-------------------------------+-------------------------+----------------------------------------------------------+


FrameOfReference
^^^^^^^^^^^^^^^^

This table represents the frame of reference for the model output.

+-------------------------------+-------------------------+----------------------------------------------------------+
| Attribute                     | Type                    | Description                                              |
+===============================+=========================+==========================================================+
| SENSOR                        | enum                    | The sensor frame of reference. The sensor pose           |
|                               |                         | defines the origin.                                      |
+-------------------------------+-------------------------+----------------------------------------------------------+
| PARENT                        | enum                    | The parent frame of reference.                           |
|                               |                         | For example, the origin of an asset the sensor is mounted|
|                               |                         | on.                                                      |
+-------------------------------+-------------------------+----------------------------------------------------------+
| WORLD                         | enum                    | The world frame of reference.                            |
|                               |                         | The origin is the center of the world.                   |
+-------------------------------+-------------------------+----------------------------------------------------------+
| CUSTOM                        | enum                    | The custom frame of reference.                           |
|                               |                         | The origin and orientation are defined by the user.      |
+-------------------------------+-------------------------+----------------------------------------------------------+


MotionCompensationState
^^^^^^^^^^^^^^^^^^^^^^^

This table represents the motion compensation state for the model output. 
a motion compensated output (ex: a pointcloud) means that if each element/point had a different detection time and 
the sensor was moving then the actual coordinates of the elements are figured out and corrected accounting for the 
sensor's motion.

Examples:

- a rotary scanning Lidar moving forward and detecting a circle on the ground.

  - non compensated: the circle will look as a complete closed circle, with all points at same range (sensor to ground distance)
  - compensated: the circle will have a tear in it because the when completing the scan the sensor would have moved.

- a soild state line scanning Lidar that is moving detecting a vertical pole.

  - non compensated: the pole will look slanted
  - compensated: the pole will look vertical


.. image:: motion_compensation.png
   :width: 400
   :alt: Motion compensation example (orange: compensated, grey: non-compensated).



+-------------------------------+-------------------------+----------------------------------------------------------+
| Attribute                     | Type                    | Description                                              |
+===============================+=========================+==========================================================+
| NONCOMPENSATED                | enum                    | The non-compensated state.                               |
+-------------------------------+-------------------------+----------------------------------------------------------+
| COMPENSATED                   | enum                    | The compensated state.                                   |
+-------------------------------+-------------------------+----------------------------------------------------------+
| NOT_APPLICABLE                | enum                    | The not applicable state.                                |
+-------------------------------+-------------------------+----------------------------------------------------------+


CoordsType
^^^^^^^^^^

This table represents the type of coordinates used in the model output.

+-------------------------------+-------------------------+----------------------------------------------------------+
| Attribute                     | Type                    | Description                                              |
+===============================+=========================+==========================================================+
| CARTESIAN                     | enum                    | The Cartesian coordinates.                               |
+-------------------------------+-------------------------+----------------------------------------------------------+
| SPHERICAL                     | enum                    | The spherical coordinates.                               |
|                               |                         | The x, y, z of BasicElements contains:                   |
|                               |                         | azimuth, elevation, distance.                            |
+-------------------------------+-------------------------+----------------------------------------------------------+
| UNDEFINED                     | enum                    | The undefined coordinates.                               |
+-------------------------------+-------------------------+----------------------------------------------------------+


ElementFlags
^^^^^^^^^^^^

This table represents flags for elements. each value is a bit mask for the uint8_t flags member of BasicElements.
currently only the VALID flag is used, and modalities do not add any additional flags.

+-------------------------------+-------------------------+----------------------------------------------------------+
| Attribute                     | Type                    | Description                                              |
+===============================+=========================+==========================================================+
| FLAG_1                        | enum                    | The first flag. Placeholder for modality specific flags. |
+-------------------------------+-------------------------+----------------------------------------------------------+
| FLAG_2                        | enum                    | The second flag. Placeholder for modality specific flags.|
+-------------------------------+-------------------------+----------------------------------------------------------+
| FLAG_3                        | enum                    | The third flag. Placeholder for modality specific flags. |
+-------------------------------+-------------------------+----------------------------------------------------------+
| FLAG_4                        | enum                    | The fourth flag. Placeholder for modality specific flags.|
+-------------------------------+-------------------------+----------------------------------------------------------+
| FLAG_5                        | enum                    | The fifth flag. Placeholder for modality specific flags. |
+-------------------------------+-------------------------+----------------------------------------------------------+
| FLAG_6                        | enum                    | The sixth flag. Placeholder for modality specific flags. |
+-------------------------------+-------------------------+----------------------------------------------------------+
| FLAG_7                        | enum                    |The seventh flag. Placeholder for modality specific flags.|
+-------------------------------+-------------------------+----------------------------------------------------------+
| VALID                         | enum                    | The valid flag. Set if element is valid.                 |
+-------------------------------+-------------------------+----------------------------------------------------------+


OutputType
^^^^^^^^^^

This table represents the type of output.

+-------------------------------+-------------------------+----------------------------------------------------------+
| Attribute                     | Type                    | Description                                              |
+===============================+=========================+==========================================================+
| POINTCLOUD                    | enum                    | The point cloud type. Only option available curently     |
+-------------------------------+-------------------------+----------------------------------------------------------+


Modality
^^^^^^^^

This table represents the modality of the model which produced this output.

+-------------------------------+-------------------------+----------------------------------------------------------+
| Attribute                     | Type                    | Description                                              |
+===============================+=========================+==========================================================+
| UNDEFINED                     | enum                    | The undefined modality.                                  |
+-------------------------------+-------------------------+----------------------------------------------------------+
| LIDAR                         | enum                    | The Lidar sensor modality.                               |
+-------------------------------+-------------------------+----------------------------------------------------------+
| RADAR                         | enum                    | The Radar sensor modality.                               |
+-------------------------------+-------------------------+----------------------------------------------------------+
| USS                           | enum                    | The ultrasonic sensor modality.                          |
+-------------------------------+-------------------------+----------------------------------------------------------+
| IDS                           | enum                    | The Idealized Depth Sensor modality.                     |
+-------------------------------+-------------------------+----------------------------------------------------------+

AuxType
^^^^^^^

This table represents the type of auxiliary data that can be filled for a sensor. The tables below detail the different types of auxiliary data for each modality.

+-------------------------------+-------------------------+----------------------------------------------------------+
| Attribute                     | Type                    | Description                                              |
+===============================+=========================+==========================================================+
| NONE                          | enum                    | No auxilary data.                                        |
+-------------------------------+-------------------------+----------------------------------------------------------+
| BASIC                         | enum                    | Basic auxilary data.                                     |
+-------------------------------+-------------------------+----------------------------------------------------------+
| EXTRA                         | enum                    | Extra auxilary data.                                     |
+-------------------------------+-------------------------+----------------------------------------------------------+
| FULL                          | enum                    | Full auxilary data.                                      |
+-------------------------------+-------------------------+----------------------------------------------------------+

AuxiliaryData
^^^^^^^^^^^^^

Every modality has its specific auxiliary data. See AuxType enum above for a list of available auxiliary data types.
Below are the structures for the supported modalities:

LidarAuxiliaryData
^^^^^^^^^^^^^^^^^^

The ``LidarAuxiliaryData`` structure contains auxiliary data for a Lidar sensor. Every pointer instance is an array of size ``numElements``.

+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| Attribute                     | Type                    | Description                                              | AuxType Support         |
+===============================+=========================+==========================================================+=========================+
| scanComplete                  | uint32_t                | Whether the scan is complete.                            | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| azimuthOffset                 | float                   | The offset to +x in radians for specific sensors.        | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| filledAuxMembers              | LidarAuxHas             | Which auxiliary data is filled.                          | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| padding                       | uint8_t[4]              | Padding to align the structure to a multiple of 8 bytes. | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| emitterId                     | uint32_t*               | The emitter index array for a hit from a ray firing.     | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| channelId                     | uint32_t*               | The channel index array for a hit from a ray firing.     | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| matId                         | uint32_t*               | The material index array. Identifies with a geom matID.  | >= EXTRA                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| tickId                        | uint32_t*               | The tick index array. Identifies the current tick.       | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| hitNormals                    | float*                  | The hit normals array. Returned normals from geometries. | >= FULL                 |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| velocities                    | float*                  | The velocity array. Returned velocities from geometries. | >= FULL                 |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| objId                         | uint8_t*                | The object index array. Identifies a hit object ID.      | >= EXTRA                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| echoId                        | uint8_t*                | The echo index array. Identifies with multiple echos.    | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| tickStates                    | uint8_t*                | The tick states index array for multiple emitter states. | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+



The ``LidarAuxHas`` enum class is used to specify which auxiliary data is filled for a Lidar sensor. Values are bit masks for the 
filledAuxMembers member of LidarAuxiliaryData.

+-------------------------------+-------------------------+----------------------------------------------------------+
| Attribute                     | Type                    | Description                                              |
+===============================+=========================+==========================================================+
| NONE                          | enum                    | No auxiliary data is filled.                             |
+-------------------------------+-------------------------+----------------------------------------------------------+
| EMITTER_ID                    | enum                    | The emitter ID is filled.                                |
+-------------------------------+-------------------------+----------------------------------------------------------+
| CHANNEL_ID                    | enum                    | The channel ID is filled.                                |
+-------------------------------+-------------------------+----------------------------------------------------------+
| ECHO_ID                       | enum                    | The echo ID is filled.                                   |
+-------------------------------+-------------------------+----------------------------------------------------------+
| MAT_ID                        | enum                    | The material ID is filled.                               |
+-------------------------------+-------------------------+----------------------------------------------------------+
| OBJ_ID                        | enum                    | The object ID is filled.                                 |
+-------------------------------+-------------------------+----------------------------------------------------------+
| TICK_ID                       | enum                    | The tick ID is filled.                                   |
+-------------------------------+-------------------------+----------------------------------------------------------+
| TICK_STATES                   | enum                    | The tick states are filled.                              |
+-------------------------------+-------------------------+----------------------------------------------------------+
| HIT_NORMALS                   | enum                    | The hit normals are filled.                              |
+-------------------------------+-------------------------+----------------------------------------------------------+
| VELOCITIES                    | enum                    | The velocities are filled.                               |
+-------------------------------+-------------------------+----------------------------------------------------------+



USSAuxiliaryData
^^^^^^^^^^^^^^^^

The ``USSAuxiliaryData`` structure contains auxiliary data for an USS sensor.

+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| Attribute                     | Type                    | Description                                              | AuxType Support         |
+===============================+=========================+==========================================================+=========================+
| numSgws                        | uint32_t               | The number of Signal Ways.                               | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| numSamplesPerSgw               | uint32_t               | The number of samples per Signal Way.                    | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+


RadarAuxiliaryData
^^^^^^^^^^^^^^^^^^

The ``RadarAuxiliaryData`` structure contains auxiliary data for a Radar sensor.

+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| Attribute                     | Type                    | Description                                              | AuxType Support         |
+===============================+=========================+==========================================================+=========================+
| sensorID                      | uint8_t                 | The ID of the sensor that generated the scan.            | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| scanIdx                       | uint8_t                 | The scan index for sensors with multi-scan support.      | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| padding                       | uint8_t[6]              | Padding to align the structure to a multiple of 8 bytes. | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| cycleCnt                      | uint64_t                | The scan cycle count (unique per scan index).            | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| maxRangeM                     | float                   | The maximum unambiguous range for the scan in meters.    | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| minVelMps                     | float                   | The minimum unambiguous velocity for the scan in m/s.    | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| maxVelMps                     | float                   | The maximum unambiguous velocity for the scan in m/s.    | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| minAzRad                      | float                   | The minimum unambiguous azimuth for the scan in rads.    | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| maxAzRad                      | float                   | The maximum unambiguous azimuth for the scan in rads.    | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| minElRad                      | float                   | The minimum unambiguous elevation for the scan in rads.  | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| maxElRad                      | float                   | The maximum unambiguous elevation for the scan in rads.  | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| padding2                      | uint8_t[4]              | Padding to align the structure to a multiple of 8 bytes. | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| rv_ms                         | float*                  | The radial velocity (m/s), always filled.                | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+



IDSAuxiliaryData
^^^^^^^^^^^^^^^^

The ``IDSAuxiliaryData`` structure contains auxiliary data for an IDS (Idealized Depth Sensor) sensor.

+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| Attribute                     | Type                    | Description                                              | AuxType Support         |
+===============================+=========================+==========================================================+=========================+
| numRows                       | uint32_t                | The number of rows in the sensor's field of view.        | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| numCols                       | uint32_t                | The number of columns in the sensor's field of view.     | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| minColUnit                    | float                   | The minimum column unit of the specified field of view.  | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| maxColUnit                    | float                   | The maximum column unit of the specified field of view.  | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| minRowUnit                    | float                   | The minimum row unit of the specified field of view.     | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| maxRowUnit                    | float                   | The maximum row unit of the specified field of view.     | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| emitterCfgOriginX             | float                   | The x-coordinate (m) of the origin of the emitter config.| >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| emitterCfgOriginY             | float                   | The y-coordinate (m) of the origin of the emitter config.| >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| emitterCfgOriginZ             | float                   | The z-coordinate (m) of the origin of the emitter config.| >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| emitterGenType                | int                     | The type of the emitter generation.                      | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| elementSize                   | float                   | The maximum size of the spatial element to generate.     | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| radius                        | float                   | The radius (m) at which the element size is defined.     | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| filledAuxMembers              | IDSAuxHas               | Which auxiliary data is filled.                          | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| padding                       | uint8_t[4]              | Padding to align the structure to a multiple of 8 bytes. | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| originX                       | float*                  | The x-coordinates (m) of the origins.                    | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| originY                       | float*                  | The y-coordinates (m) of the origins.                    | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| originZ                       | float*                  | The z-coordinates (m) of the origins.                    | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| objectId                      | uint32_t*               | The object IDs.                                          | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| materialId                    | uint32_t*               | The material IDs.                                        | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+
| velocities                    | float*                  | The velocities in m/s.                                   | >= BASIC                |
+-------------------------------+-------------------------+----------------------------------------------------------+-------------------------+


The ``IDSAuxHas`` enum class is used to specify which auxiliary data is filled for an IDS sensor. Values are bit masks for the 
filledAuxMembers member of IDSAuxiliaryData.

+-------------------------------+-------------------------+----------------------------------------------------------+
| Attribute                     | Type                    | Description                                              |
+===============================+=========================+==========================================================+
| NONE                          | enum                    | No auxiliary data is filled.                             |
+-------------------------------+-------------------------+----------------------------------------------------------+
| VELOCITIES                    | enum                    | The velocities are filled.                               |
+-------------------------------+-------------------------+----------------------------------------------------------+

.. Note:: One important note is that, for the contiguous buffer, additional padding bytes are added after the last flags element (just before the auxiliary data struct) to ensure that the structure is aligned to a multiple of 8 bytes. This is done by the following code snippet:

    .. code-block:: cpp

        if (size % 8 != 0)
        {
            size += 8 - (size % 8); // This also has to be done for reading the auxiliary data from the buffer (where size is replaced by the offset to the start of the buffer)
        }

Utility Functions
-----------------

Additionally, the ``GenericModelOutput`` provides utility functions, e.g, for building the structure out of a contiguous memory block, or for copying the structure.
Below, is a list of the most important utility functions:

sizeInBytes
^^^^^^^^^^^

The ``sizeInBytes`` function is a part of the ``omni::sensors`` namespace. It calculates the total size of the ``GenericModelOutput`` structure and its elements.

Function Signature

.. code-block:: cpp

    NV_HOSTDEVICE
    inline size_t sizeInBytes(const GenericModelOutput& output)

Parameters

- ``output`` : ``const GenericModelOutput&``
    - The ``GenericModelOutput`` structure for which to calculate the size.

Returns

- ``size_t``
    - The total size of the ``GenericModelOutput`` structure and its elements.

Description

This function calculates the total size of the ``GenericModelOutput`` structure and its elements. This includes the common basic elements and the auxiliary data.
The auxiliary data is sensor modality specific and will reflect the correct size based upon the ``GenericModelOutput`` modality field.


getModelOutputPtrFromBuffer
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``getModelOutputPtrFromBuffer`` function is a part of the ``omni::sensors`` namespace. It retrieves a pointer to a ``GenericModelOutput`` structure from a buffer.

Function Signature

.. code-block:: cpp

    NV_HOSTDEVICE
    inline GenericModelOutput* getModelOutputPtrFromBuffer(void* inData)

Parameters

- ``inData`` : ``void*``
    - The input data buffer from which to retrieve the ``GenericModelOutput`` structure.

Returns

- ``GenericModelOutput*``
    - A pointer to the ``GenericModelOutput`` structure retrieved from the buffer.

Description

This function first checks if the magic number of the ``GenericModelOutput`` structure is correct. If it is, the function then checks if the version of the ``GenericModelOutput`` structure is supported. If the version is supported, the function sets the basic elements and auxiliary data of the ``GenericModelOutput`` structure. If the magic number or version is not correct, the function prints an error message.


cpyGMOToBuffer
^^^^^^^^^^^^^^

The ``cpyGMOToBuffer`` function is a part of the ``omni::sensors`` namespace. It copies a ``GenericModelOutput`` structure to a buffer.

Function Signature

.. code-block:: cpp

    inline void cpyGMOToBuffer(uint8_t* buffer,
                               const omni::sensors::GenericModelOutput* gpc,
                               const bool bufferOnHost = true, // not needed for cpu only
                               const bool pointerOnHost = true, // not needed for cpu only
                               const int32_t cudaDevice = -1, // not needed for cpu only
                               const cudaStream_t stream = 0) // not needed for cpu only

Parameters

- ``buffer`` : ``uint8_t*``
    - The buffer to which to copy the ``GenericModelOutput`` structure.

- ``gpc`` : ``const omni::sensors::GenericModelOutput*``
    - The ``GenericModelOutput`` structure to copy.

- ``bufferOnHost`` : ``bool``
    - Whether the buffer is on the host. Default is ``true``.

- ``pointerOnHost`` : ``bool``
    - Whether the pointer is on the host. Default is ``true``.

- ``cudaDevice`` : ``int32_t``
    - The CUDA device to use. Default is ``-1``.

- ``stream`` : ``cudaStream_t``
    - The CUDA stream to use. Default is ``0``.

Description

This function first checks if the magic number of the ``GenericModelOutput`` structure is correct. If it is, the function then checks if the version of the ``GenericModelOutput`` structure is supported. If the version is supported, the function sets the copy kind based on whether the buffer and pointer are on the host or device. If the magic number or version is not correct, the function prints an error message.
The function then copies the ``GenericModelOutput`` structure to the buffer using the appropriate copy kind.

Plugins
-------

.. _GenericModeloutIO:



IGenericModelOutputIO
^^^^^^^^^^^^^^^^^^^^^

The ``IGenericModelOutputIO`` class is an interface for generic model output I/O operations. It writes and reas into a hdf5 file.

Methods
"""""""

- ``void init(const GMOIOConfig& cfg)``
    - Initializes the ``IGenericModelOutputIO`` interface with the given configuration.

- ``void writeModelOutput(const GenericModelOutput& modelOutput)``
    - Writes the given model output.

- ``GenericModelOutput readModelOutput(const omni::string& sensorName = "", const int frameId = -1)``
    - Reads a model output. If a sensor name is given, it reads the model output for that sensor. If a frame ID is given, it reads the specific frame. If no arguments are given, it reads frames in order.

- ``void addPacket(void* packet, const size_t packetSize)``
    - Adds a packet with the given size.

Initialization
""""""""""""""

To get an object of the ``IGenericModelOutputIO`` interface, you need to call the ``carb::getFramework()->acquireInterface<omni::sensors::IGenericModelOutputIOFactory>()->createInstance()`` function.
To initialize the ``IGenericModelOutputIO`` interface, you need to create a ``GMOIOConfig`` structure and call the ``init`` method.

GMOIOConfig
"""""""""""

The ``GMOIOConfig`` structure is used to configure the ``IGenericModelOutputIO`` interface.


- ``AccessType accessType``
    - The access type for the ``IGenericModelOutputIO`` interface. Default is ``AccessType::RECORD_FULL``.

- ``bool onlyValid``
    - Whether to only consider valid data. Default is ``false``.

- ``bool loop``
    - Whether to loop the data. Default is ``false``. Only needed for ``AccessType::READ``.

- ``uint32_t maxPoints``
    - The maximum number of points. Default is ``0``. Only needed for ``AccessType::READ``.

- ``omni::string fileName``
    - The name of the file. Default is an empty string.

- ``omni::string sensorName``
    - The name of the sensor. Default is an empty string.



Python Bindings
---------------

Python bindings are available for the ``GenericModelOutput`` structure, utilities and the IGenericModelOutputIO interface.
