# Commands
Public command API for module **isaacsim.asset.importer.mjcf**:

- [MJCFCreateAsset](#mjcfcreateasset)
- [MJCFCreateImportConfig](#mjcfcreateimportconfig)


## MJCFCreateAsset
This command parses and imports a given mjcf file.

### Arguments
- mjcf_path
- import_config
- prim_path
- dest_path

### Usage

```python
import omni.kit.commands
from isaacsim.asset.importer.mjcf import _mjcf

# Create import configuration
import_config = omni.kit.commands.execute("MJCFCreateImportConfig")

# Import MJCF file to USD stage
mjcf_path = "/path/to/your/robot.xml"
prim_path = "/World/Robot"
dest_path = "/path/to/output/robot.usd"

asset_path = omni.kit.commands.execute(
    "MJCFCreateAsset",
    mjcf_path=mjcf_path,
    import_config=import_config,
    prim_path=prim_path,
    dest_path=dest_path
)
```

## MJCFCreateImportConfig
Returns an ImportConfig object that can be used while parsing and importing.
Should be used with the `MJCFCreateAsset` command

Returns:
:obj:`isaacsim.asset.importer.mjcf._mjcf.ImportConfig`: Parsed MJCF stored in an internal structure.


### Usage

```python
import omni.kit.commands

# Create an MJCF import configuration
config = omni.kit.commands.execute("MJCFCreateImportConfig")
```

