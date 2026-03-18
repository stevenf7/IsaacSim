```{csv-table}
**Extension**: {{ extension_version }},**Documentation Generated**: {sub-ref}`today`
```

# Settings

## Settings Provided by the Extension

## exts."isaacsim.app.compatibility_check".gpu_driver
- **Default Value**: [
  {'platform': 'linux', 'minimum': '535.161', 'unsupported': []},
  {'platform': 'win32', 'minimum': '537.58', 'unsupported': []}
]
- **Description**: GPU: Supported driver versions.

## exts."isaacsim.app.compatibility_check".gpu_vram
- **Default Value**: {'minimum': 10, 'good': 16, 'ideal': 48}
- **Description**: GPU: VRAM requirements (GB).

## exts."isaacsim.app.compatibility_check".cpu_cores
- **Default Value**: {'minimum': 4, 'good': 8, 'ideal': 16}
- **Description**: CPU: Core requirements.

## exts."isaacsim.app.compatibility_check".ram
- **Default Value**: {'minimum': 32, 'good': 64, 'ideal': 128}
- **Description**: RAM requirements (GB).

## exts."isaacsim.app.compatibility_check".storage
- **Default Value**: {'minimum': 50, 'good': 500, 'ideal': 1000}
- **Description**: Available storage requirements (GB).

## exts."isaacsim.app.compatibility_check".operating_system
- **Default Value**: [
  {'name': 'ubuntu', 'versions': ['22.04', '24.04']},
  {'name': 'windows', 'versions': ['10', '11']}
]
- **Description**: Supported operating systems.

## exts."isaacsim.app.compatibility_check".test_kit_app
- **Default Value**: "omni.app.mini"
- **Description**: Test case: Kit app relative to the `kit` folder.

## exts."isaacsim.app.compatibility_check".test_kit_args
- **Default Value**: [
  "--/app/quitAfter=100",
  "--no-window"
]
- **Description**: Test case: Kit app arguments.
