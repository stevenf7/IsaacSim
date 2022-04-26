Installation
------------

Install scene builder package with python -m pip install source/tools/scene_blox (using the omniverse python).

Running
-------

To generate some warehouses run

python source/tools/scene_blox/src/scene_blox/generate_scene.py <full_path_to_generated_scene_folder> --grid_config source/tools/scene_blox/parameters/warehouse/tile_config.yaml --generation_config source/tools/scene_blox/parameters/warehouse/tile_generation.yaml --cols 15 --rows 11 --constraints_config source/tools/scene_blox/parameters/warehouse/constraints.yaml --variants 1 --units_in_meters 0.01 --collisions

To generate some labyrinths run

python source/tools/scene_blox/src/scene_blox/generate_scene.py <full_path_to_generated_scene_folder> --grid_config source/tools/scene_blox/parameters/labyrinth/rules.yaml --generation_config source/tools/scene_blox/parameters/labyrinth/generation.yaml --cols 9 --rows 9 --constraints_config source/tools/scene_blox/parameters/labyrinth/constraints.yaml --variants 1 --units_in_meters 0.01

See docs folder for detailed information on the scripts and usage.
