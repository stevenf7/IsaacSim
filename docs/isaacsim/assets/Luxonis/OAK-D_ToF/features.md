## Features and Specification

### Camera Features

| Parameter | Camera_33d | Camera_left_ov9782 | Camera_right_ov9782 | Camera_pseudo_depth | Camera_pseudo_depth_tof |
|-----------|------------|--------------------|--------------------|---------------------|------------------------|
| focalLength | 3.1991 | 2.2882 | 2.2882 | 2.2882 | 3.1991 |
| focusDistance | 500.0 | 196.0 | 196.0 | 196.0 | 500.0 |
| fStop | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| projection | perspective | perspective | perspective | perspective | perspective |
| stereoRole | mono | left | right | mono | mono |
| horizontalAperture | 4.480 | 3.840 | 3.840 | 3.840 | 4.480 |
| verticalAperture | 3.360 | 2.400 | 2.400 | 2.400 | 3.360 |
| horizontalApertureOffset | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| verticalApertureOffset | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| clippingRange | (0.01, 100.0) | (0.01, 100.0) | (0.01, 100.0) | (0.01, 100.0) | (0.01, 100.0) |
| cameraProjectionType | pinhole | pinhole | pinhole | pinhole | pinhole |
| nominalWidth | 640 | 1280 | 1280 | 1280 | 640 |
| nominalHeight | 480 | 800 | 800 | 800 | 480 |
| opticalCenterX | 320.00 | 640.00 | 640.00 | 640.00 | 320.00 |
| opticalCenterY | 240.00 | 400.00 | 400.00 | 400.00 | 240.00 |
| maxFOV | 70.0 | 80.0 | 80.0 | 80.0 | 70.0 |
| polyK0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| polyK1 | 0.00245 | 0.00245 | 0.00245 | 0.00245 | 0.00245 |
| polyK2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| polyK3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| polyK4 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| polyK5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| p0 | -0.00037 | -0.00037 | -0.00037 | -0.00037 | -0.00037 |
| p1 | -0.00074 | -0.00074 | -0.00074 | -0.00074 | -0.00074 |
| s0 | -0.00058 | -0.00058 | -0.00058 | -0.00058 | -0.00058 |
| s1 | -0.00022 | -0.00022 | -0.00022 | -0.00022 | -0.00022 |
| s2 | 0.00019 | 0.00019 | 0.00019 | 0.00019 | 0.00019 |
| s3 | -0.0002 | -0.0002 | -0.0002 | -0.0002 | -0.0002 |

### Other Features

- Platform: Intel Myriad X VPU (RVC2)
- IMU: Yes
- Stereo Baseline: 20 mm
- ToF Baseline (simulation): 0.5 mm
- Ideal Range (stereo): 0.3 m to 1 m
- Ideal Range (ToF): 0.2 m to 5 m
- Depth Accuracy (ToF): < 1% indoors, < 2% outdoors
- Dual depth sensing: stereo disparity-based and Time-of-Flight

## Datasheet

For the datasheet and full list of specifications, visit the [OAK-D ToF product page](https://shop.luxonis.com/products/oak-d-tof).
