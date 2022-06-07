## [0.3.4] - 2022-05-24

- fix property orientation loading bug

## [0.3.3] - 2022-04-22

- Moved sensor data aquisition function from tick to onPhysicsStep

## [0.3.2] - 2022-04-14

- Fixed component visualization

## [0.3.1] - 2022-04-07

- Fixed visualization error of the isaac sensors
- Changed draw function to run onUpdate instead of physics call back

## [0.3.0] - 2022-04-04

- Added Imu sensor to isaac sensor
- Changed extension name to omni.isaac.isaac_sensor
- Changed Imu sensor getSensorReadings to output the readings from the last frame
- Updated index.rst documentation for contact sensor and imu sensors

## [0.2.1] - 2022-03-28

- Converted contact sensor namespaces to isaac sensor namespaces
- Add UI element to create contact sensor 
- Modified draw function to use USD util's global pose

## [0.2.0] - 2022-03-18

- Converted contact sensors into usdSchemas
- Enable visualization of contact sensors in the stage

## [0.1.3] - 2022-03-16

- Bugfix for failing tests and missing updates

## [0.1.2] - 2022-01-26

- Compatibility for sdk 103

## [0.1.1] - 2021-07-26

### Added
- New UI

## [0.1.0] - 2021-07-08

### Added
- Initial version of Isaac Sim Contact Sensor Extension
