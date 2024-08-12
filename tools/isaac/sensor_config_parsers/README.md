
# Using Parsers

## JSON to CSV Parser:

1. Modify key list to look for desired key values in json files.

2. Open Terminal and `cd` to the folder with the `lidar_json_parser.py` file:
    ```bash
    cd /path/to/tools/isaac
    ```

3. In Terminal, launch argument on json folder file path:
    ```bash
        python json_parser.py -l /path/of/folder/containing/json/files
    ```

4. Press enter, and the csv files containing the json information should populate into the folder containing the `lidar_json_parser.py` file.
    - should be located in ``/tools/isaac/sensor_config_parsers/lidar_json_parser``

## USD to CSV Parser:

1. Modify values to parse desired information:
    - change values in `attr_list` to look for desired attribute values in the USD files
    - modify `object_prim.GetAttribute('').Get()` to find desired values

2. Open Terminal and `cd` to the Isaac Sim release folder. The path should be similar to this one:
    ```bash
        cd ../../isaac_sim/_build/linux-x86_64/release
    ```

3. In Terminal, launch argument on usd file path:
    ```bash
    ./python.sh /path/to/usd_parser.py --usd /path/to/usd/file
    ```
    - append `omniverse://isaac-dev.ov.nvidia.com` to beginning of file path if the USD file is located in the Omniverse directory
    - use quotation marks if file path has any spaces
        - ex: `"omniverse://Isaac/Sensors/Orbbec/Gemini 2/orbbec_gemini2_V1.0.usd"`
        
4. Press enter, and the csv files containing the usd information should populate into the folder containing the `camera_usd_parser.py` file.
    - should be located in ``/tools/isaac/sensor_config_parsers/camera_usd_parser``
