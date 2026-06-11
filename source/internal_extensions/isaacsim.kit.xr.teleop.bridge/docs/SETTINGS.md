```{csv-table}
**Extension**: {{ extension_version }},**Documentation Generated**: {sub-ref}`today`
```

# Settings

### exts."isaacsim.kit.xr.teleop.bridge".openxr.requiredExtensions.set
- **Default Value**: [
  "XR_KHR_convert_timespec_time",
  "XR_NVX1_tensor_data"
]
- **Description**: Base required OpenXR extension list for this bridge component. If non-empty, this list becomes the starting value before add/remove are applied.

### exts."isaacsim.kit.xr.teleop.bridge".openxr.requiredExtensions.add
- **Default Value**: [
]
- **Description**: Additional OpenXR extensions to append to the resolved required extension list. Duplicate values are ignored.

### exts."isaacsim.kit.xr.teleop.bridge".openxr.requiredExtensions.remove
- **Default Value**: [
]
- **Description**: OpenXR extensions to remove from the resolved required extension list.
