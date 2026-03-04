```{csv-table}
**Extension**: {{ extension_version }},**Documentation Generated**: {sub-ref}`today`
```

# Settings

### app.sensors.nv.lidar.outputBufferOnGPU
- **Default Value**: true
- **Description**: Keeps Lidar return buffer on GPU for post-processing operations.

### app.sensors.nv.radar.outputBufferOnGPU
- **Default Value**: true
- **Description**: Keeps Radar return buffer on GPU for post-processing operations.

### rtx.materialDb.nonVisualMaterialCSV.enabled
- **Default Value**: false
- **Description**: Enables non-visual materials using USD attributes for material database processing.

### rtx.materialDb.nonVisualMaterialSemantics.prefix
- **Default Value**: "omni:simready:nonvisual"
- **Description**: Specifies the USD attribute prefix for non-visual material semantics identification.

### rtx.rtxsensor.useHydraTimeAlways
- **Default Value**: true
- **Description**: Uses Hydra time from omni.timeline in RTX Sensor models for time synchronization.
