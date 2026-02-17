# Autogenerate Robot Assets 

  

This is the second part of instructions to autogenerate robot assets in the Isaac Sim documentation. This set of scripts lies in the Isaac Sim documentation repository, not the Isaac Sim repository.
 
  
  

## Usage/Examples

 
 1. Remove all the previous version's now unused assets in ``/docs/app_isaacsim/images/usd_assets_robots/robot_assets_docs_thumbnails``. Paste all the newly generated thumbnails from ``thumbnail_downloader.py`` from the previous part into ``/docs/app_isaacsim/images/usd_assets_robots/robot_assets_docs_thumbnails``. The default location of these thumbnails is ``{Your Isaac Sim repository location}/tools/isaac/robot_asset_autogenerate/thumbnails``.
 2. Replace all the content in ``docs/app_isaacsim/assets/usd_assets_robots.rst`` with the content from the previous part's ``output.rst`` file output. The default location of this file is at ``{Your Isaac Sim repository location}/tools/isaac/robot_asset_autogenerate/output/usd_assets_robots.rst``. 
 3. Don't forget to save the repo so everything is actually saved!
 3. Run ``python tools/generate_robot_assets_docs/add_example.py``. This will add the information from the list of examples to the corresponding robots automatically to the ``usd_assets_robots.rst`` file.
 4. Build the documentation with ``./build.bat`` or ``./build.sh`` depending on your OS. It's possible a couple images may not be readable, but it will still build regardless.
 5. Congrats! The robots assets page has been completely generated. 

Further action:
 - Some assets will have to be manually combed through to decide on their inclusion. For example, at the time of writing, there are 3 files corresponding to the AllegroHand, which even we do not know what to choose. As such, they will have to be manually selected and cleaned up.
 

