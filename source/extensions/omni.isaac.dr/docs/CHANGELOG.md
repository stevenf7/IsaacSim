**********
CHANGELOG
**********

[0.1.5] - 2021-03-28
========================

Added
-------
- Attribute randomization component: Randomize any usd attribute and variant
- Specify different distribution per attribute

Fixed
------
- Look-at movement behavior for non-camera assets
- Set rotation properly for rigid body assets

[0.1.4] - 2021-02-26
========================

Added
-------
- Transform randomization component
- Point Instancer based transform randomization: random and sequence behavior based on the position and orientation specified in the point instancers
- Parameterize position and orientation offset in transform randomization

[0.1.3] - 2021-02-22
========================

Added
-------
- Load DR components as a layer
- Point based movement randomization: random and sequence behavior
- update to python 3.7
- update to omni.kit.uiapp

[0.1.2] - 2021-01-28
========================

Added
-------
- Polygon movement randomization

Fixed
------
- DR not working properly with grouped classes for texture, material components

[0.1.1] - 2020-11-25
========================

Added
-------
- Improved python APIs based on omni.kit.commands
- Added more samples
- Updated documentation: https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/domain-randomization.html

[0.1.0] - 2020-07-29
========================

Added
------
- Based on USD Schema
- Support randomization of:
    - Materials and its properties like color, texture etc.
    - Light parameters
    - Object position (supports look at)
    - Object orientation
    - Object scale
    - Object visibility
- Create component to enable various randomization behavior
    - Color component
    - Texture component
    - Material component
    - Light component
    - Movement component
    - Rotation component
    - Scale component
    - Visibility component
    - Mesh component
- Invoke randomization manually (based on user request) or given duration
- Specify seed to introduce consistency in the randomization process
- Documentation: https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/domain-randomization.html


