**********
CHANGELOG
**********


[0.1.1] - 2020-11-25
========================

Added
-------
- Improved python APIs based on omni.kit.commads
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


