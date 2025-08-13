
# Autogenerate Robot Assets

  

This is the first set of scripts to autogenerate robot assets in the Isaac Sim documentation. This set of scripts lies in the Isaac Sim repository, not the Isaac Sim documentation repository.
 
  
  

## Usage/Examples

In the repository, build Isaac Sim first. Then, use the release folder's ```python.sh/bat``` to run the scripts, which are located in ```tools/isaac/robot_asset_autogenerate```. 

First, we need to find the list of robots we will use. To do this, use ```robot_list_download.py```.  It has an optional ```--csv``` or ```-c``` argument, which is the path of the output csv file that will contain the list of robots. If no argument is provided, it will default to outputting to ``/tools/isaac/robot_asset_autogenerate/outputs/robot_list.csv``, which is very close to where the script itself is located.

Linux usage:
Default:
 - ``./_build/linux-x86_64/release/python.sh tools/isaac/robot_asset_autogenerate/robot_list_download.py``

With optional arguments:
 - ``./_build/linux-x86_64/release/python.sh tools/isaac/robot_asset_autogenerate/robot_list_download.py -r /home/horde/robot_list.csv``

Windows usage:
Default:
 - ``.\_build\windows-x86_64\release\python.bat tools\isaac\robot_asset_autogenerate\robot_list_download.py``
With optional arguments:
 - ``.\_build\windows-x86_64\release\python.bat tools\isaac\robot_asset_autogenerate\robot_list_download.py c:\Users\{USERNAME}\Downloads\robot_list.csv``




Now, we can use this robot list to do 2 things:

 - Download all the corresponding thumbnails (```thumbnail_downloader.py```)
 - Output the RST file (```output_rst.py```)
 The order of these two does not matter.

 For the thumbnail downloader, we can take an ```--input_file``` or ``-i`` argument containing the path of a list of robots to download (By default, it will take the file output by ``robot_list_download.py``). We also require the version of Isaac Sim being worked on, with the ``--version`` or ``-v`` flag. Then, there are some other optional arguments.
 

 - ``output-dir``, which defaults to ``tools/isaac/robot_asset_autogenerate/thumbnails`` folder in the Isaac Sim repo
 - ``resolution``, which defaults to 1920x1080 
 - ``--force-create-scene``, if you want to force create a scene.

Linux usage:
Default:
 - ``./_build/linux-x86_64/release/python.sh tools/isaac/robot_asset_autogenerate/thumbnail_downloader.py -v 5.1``

With optional arguments:
 - ``./_build/linux-x86_64/release/python.sh tools/isaac/robot_asset_autogenerate/thumbnail_downloader.py -i /home/horde/robot_list.csv --force_create_scene --version 5.1``

Windows usage:
Default:
 - ``.\_build\windows-x86_64\release\python.bat tools\isaac\robot_asset_autogenerate\thumbnail_downloader.py --version 5.1`` 
With optional arguments:
 - ``.\_build\windows-x86_64\release\python.bat tools\isaac\robot_asset_autogenerate\thumbnail_downloader.py --input_file c:\Users\{USERNAME}\Downloads\robot_list.csv -r 1280x720 -v 5.1`` 



For the RST generator, we take the following arguments:

 - ``--version`` or ``-v``, the version of Isaac Sim being worked on. (Required)
 - ``--rst`` or ``-r``, the path where you want the outputted RST to be saved to. (Optional)
 - ``--list`` or ``l``, the path of the list of robots. (Optional)
By default, the RST output path will be ``tools/isaac/robot_asset_autogenerate/outputs/usd_assets_robots.rst``, and the list path will take the output file from ``robot_list_download.py``.

Linux usage:
Default:
 - ``./_build/linux-x86_64/release/python.sh tools/isaac/robot_asset_autogenerate/output_rst.py -v 5.1``

With optional arguments:
 - ``./_build/linux-x86_64/release/python.sh tools/isaac/robot_asset_autogenerate/output_rst.py -r /home/horde/usd_assets_robots.rst -l /home/horde/robot_list.csv --version 5.1``

Windows usage:
Default:
 - ``.\_build\windows-x86_64\release\python.bat tools\isaac\robot_asset_autogenerate\thumbnail_downloader.py --version 5.1`` 
With optional arguments:
 - ``.\_build\windows-x86_64\release\python.bat tools\isaac\robot_asset_autogenerate\output_rst.py -r  c:\Users\{USERNAME}\Downloads\output.rst -l c:\Users\{USERNAME}\Downloads\robot_list.csv -v 5.1``




Once you have both the thumbnails and the RST generated, you can move onto inserting it into the documentation, instructions are under  ``tools/generate_robot_assets_docs/README.md``.
