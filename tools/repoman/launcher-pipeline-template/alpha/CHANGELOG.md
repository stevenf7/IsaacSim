## [2020.3.2-gm.1] - 2021-01-07

### *Changed*

- updated SDK to 100.2.108-f5dd6556-release

### Bug Fixes

- Add an UsdManager::advanceSyncScopes that releases all deferred resources
- OM-25455: crashreporter: Report submission id to log
- Better treatment for unrecognized primvar from USD

## [2020.3.2-rc.1] - 2021-01-06

### *Changed*

- updated SDK to 100.2.100-89440370-release

### Bug Fixes

- mmarks/OM-24236
- nnikfetrat/OM-25099-exclude-geforce-pascal-gpus
- fix bug that was resulting in alpha-masked materials exported from UE4 not having allowCutoutOpacity set.

## [2020.3.0-rc.29.2] - 2020-12-11

### *Changed*

- updated SDK to 100.1.45151-46fe41c2-release

### Bug Fixes

- Avoid navigating to localhost on startup
- Fixed issue with Double extensions
- Avoid double Paste on the BrowserBar 

## [2020.3.0-rc.29] - 2020-12-11

### *Changed*

- updated SDK to 100.1.45069-5b03d8d9-release
- Merging RTX MRs from master to release/100.1 - MRs 159-161

### Bug Fixes

- OM-23363: Improve the property window light style
- Clear the GI output pstf hash code for invalid GBuffer pixels.
- Enable GI in non-sampled lighting reflections.
- OM-23122 a few workaround to not crash the system while single vertex buffer exceed 4 GB
- further cleanup of render settings 2.0:
  - remove redundant enable settings for frames that already have a _frame_setting_path defined
  - unify Direct Lighting settings (sampled and non-sampled) under a single frame, toggling the subset o
- Build flags for the release
- OM-15364 removing the PACKAGE-INFO files from some packages

## [2020.3.0-rc.28] - 2020-12-10

### *Changed*

- updated SDK to 100.1.45069-5b03d8d9-release
- Merging RTX MRs from master to release/100.1 - MRs 151-158
- Developer Documentation Polish #1
- kit welcome app: doc, splash
- Physics release pakage update

### Bug Fixes

- Prefer lod-clamp over BC when there aren't enough mip-levels to do both
- Fix crash when turning off OptiX denoiser with the "new attic" scene (currently at )
- Disable atomic fp32 until r460 driver issues are resolved
- Simple workaround for GPU profiler in nonAsyncMode
- blacklist r460 drivers, due to known driver crashes and device lost in both vk and d3d
- fix flow in diffuse gi
- Disabled the camera gizmos for iray (now they are invisible) and filtered out all the instance transform changes for them. This makes camera updates much faster in iray.
- Setting string obfuscation
- render settings 2.0: fix mistakes introduced in omniverse/kit!7919 + make Render Settings 2.0 the new default + remove old render settings
- OM-24321: Update asset importer to improve import
- OM-24567: Outline prim when hovering material in Drag N Drop worlflow 
- OM-24631: Fix invalid layer open
- OM-24506: Render Settings 2.0 Tooltip colors
- cleanup Render Settings 2.0, improve settings defaults, auto-enable sampled lighting
- change several setting defaults
  - make sure MGPU settings are only shown when number of GPU devices is > 1
- Add special default value for xformOp:scale 
- Remove VR from release
- Fix drag/drop and camera mesh not loading properly when on Linux in a remote stage
- Update to newest omni config, that changes all global omniverse paths (data, cache, logs
- OM-14541 Turn on instanceable by default when creating reference
- OM-24337: Property window icons
- Content window fix double overlay

## [2020.3.0-rc.27] - 2020-12-9

### *Changed*

- updated SDK to 100.1.44350-550c5d8f-release
- Merging RTX MRs from master to release/100.1 - MRs 145-150
- physics package release update

### Bug Fixes

- OM-22964:  Change the size of dialogs to ensure they have proper size for different fonts (View)
- Added ortho projection handling when the ray misses
- OM-23936 Fix pdf of surface contribution to MIS for sphere lights
- OM-24429: Fixes dome light enable/disable which broke when optimizing dome light update performance.
- Fixed temporal resource pointer ownership
- IRay: Jhedstrom/light cleanup
- Image Viewer description, icon, preview image
- description for usda_editor

## [2020.3.0-rc.26] - 2020-12-8

### *Changed*

- updated SDK to 100.1.43780-9e773859-release
- Update UI for light mode of new content browser
- Merging RTX MRs from master to release/100.1 - MRs 141-144
- Omni.UI: Added UIntSlider and UIntDrag
- physics release package update
  
### Bug Fixes

- OM-20275: Fix instance order RTX hydra and update semantics
- Disabled the most important lights for refl in transl for now - it really, really doesnt work
- OM-24248 Make sure to setup XR compositing parameters when capturing movie alpha channel
- Release GIL while creating a new stage
- OM-23656: Fix multiple prims transform
- Fixed Content Browser search flicking
- Usability improvements to copy and content browser apps
- OM-24377 Fixed drag-and-drop from content browser to stage
- OM-24435: Fixed exception in `omni.kit.property.usd` related to PhysX
- OM-23878 Add stage reload hint for changing mat network
- OM-24443, OM-24229: * Update asset importer to set default prim, * Fix menu action 'convert to usd'
- update carbonite, disable python from using user site
- OM-23103: Update to nv_usd with improved UsdSkel dependency tracking reported by error spewage
- Property window raw empty fix
- OM-24332: updated about window
- OM-24426: Path is parent wrong drive fix
- OM-24335: Content browser options width fix
- Fix broken undo group if drag and drop USD into viewport is canceled.
- OM-24433 reset default value in property window with one click
- OM-24309: new stage reset undo stack
- OM-23861: Fix material binding when it does not have a subIdentifier as the name of mdl file name

## [2020.3.0-rc.25] - 2020-12-7

### *Changed*

- updated SDK to 100.1.43400-23076824-release
- updated physics release package
- Adjusted Color for Property Window
- Flow Property Widget
- add Default Meters Per Unit preference setting
- PxrHydraEngine now use Camera Light
- preferences slider clamp zero range fix
- extensions UI: location tag and few bugs
- Merging RTX MRs from master to release/100.1 - MRs 132-140
- updating the licensing module to 0.3.25
 
### Bug Fixes

- OM-23667 Adds 'reconnect server' action to context menu
- OM-23357 Asks to reconnect server if error encountered while adding.
- OM-23575 Fixes bookmarks not finding local paths
- [omni.usd, omni.kit.window.viewport] Flush changeblocks from xform gizmo when creating xformOps.
- OM-23510: fix for renaming camera without bad perspective
- Checking sock.bind is not enough on windows to detect if socket is in use.
  - Use sock.connect_ex instead for windows as slower than sock.bind
- OM-23482 OM-24351 Fix grid
- OM-24197 "Transform property ui hints"
- Exclude PIL directories from symbol stripping, bump repo_package version
- OM-3391 Support undo/redo on drag'n'drop in Viewport for USD/MDL/Audio
- OM-21304: add logic to check the value of a bool parameter called 'enable_opacity'
- fix logic that made selection outline go missing
- OM-24257, OM-24268: Workaround for line rendering crashes
- OM-23671 flip normal when triangle normal and normal are facing opposite, mostly happen on changing mesh orientation
- Moved the logic back into carb::graphics. 
  - We call `carb::graphics::getTextureDesc()` in many places, so carb::graphics needs to be aware of the origianl format
- Fix 460 driver crash with float atomics
- Fix iray tonemapper
- OM-24060: Kit: Load Privacy Peferences
- OM-24354: Fix camera resync after absolute root refresh

## [2020.3.0-rc.24] - 2020-12-4

### *Changed*

- updated SDK to 100.1.42875-abe4e84b-release
- kit.exe now don't try to run kit-default is missing ( new kit.exe flow )
  - backward compatible with previous workflow but kit-default will be deprecated 
- Merging RTX MRs from master to release/100.1 - MRs 112-131
- Update client library to 0.18.1257
- [omni.ui] Auto-scroll in TreeView when drag and drop
- physics release package update
- Fix debug build for aiohttp tests.
- OM-12265: Adding timestamp to the log filename [ Rotating Logs ]
- Improve movie capture UI and add IRay capture support

### Bug Fixes

- OM-23860 Support Usd Property default value from schema definition and value type
- OM-18853: File menu add reference
- OM-23514: Context menu rename active camera
- [usda_edit] Added dependency to watchdog
- OM-23739: Fixed for Transparent thumbnails
- OM-7760: preference sliders clamp entered values
- Added null check for settings string
- OM-24031: Fix MGPU translated world space
- Fix a couple of bugs in how we pass normals to ReLAX denoiser:
  - 1. they were not in the correct buffer format and encoding
  - 2. we were not passing the correct value at line 332 in DirectLightingSampled.rgs.hlsl
- OM-23572: fixed missed selection outline on mesh recreation
- OM-23970 GI in Reflections does not work without Sampled Lighting and looks Blocky
- Removed tasking from generateRaygenPermutations (formerly generateRaygenFlowThreaded)
- Load-time BC optimizations
  - Limit the number of loader threads to 4 when BC is enabled
  - BlockCompression temp buffers are released immediatly.
- Fixed incorrect range update in ResourceUtils
- Fixed pdf of surface contribution to MIS for rect lights
- Changed the threshold to use area sampling of rect lights to be based on solid angle
- OM-20425: Improved acquire plugin logic 
- OM-23491: fixed broken query path
- OM-18826: Can't select lights or imported geo
- Fix the resource manager leak for Vulkan and sync rendering
- Fixed shader compilation warning
- OM-19491: Autoexposure median filter 
- Enable reshade in PT + fixed shader loading from string
- Don't avoid dome lights in the mcsMateriaLighting lighting loop when using importance sampling.
- Remove references to deepwall in python code
- OM-24301 Content Browser ability to rename connections and bookmarks
- OM-21983 Fixes Content Browser excessive error spew
- OM-24301 Adds ability to rename connections and bookmarks
## [2020.3.0-rc.23] - 2020-12-3

### *Changed*

- updated SDK to 100.1.42426-392cddad-release
- Update client library to fix carb_sdk license problem
- Search remove cpp components

### Bug Fixes

- OM-24229: Update asset importer to set up default world prim to match Kit
- property widget add reference to refresh after adding
- OM-24060: privacy file load
- Stage hotfixes: start a search on end edit, bug with double defaultPrims, consider filtering when select
- OM-24230: ext manager: fix launch of kit file from remote
- exts tweaks: strip repostiory, hide non-toggleable, convert snippets tabs
- OM-24090 Renames "Content Browser 2.0" to just "Content"
- Bug Fixes for RC.21: Right mouse click in Content Browser should not select items in tree view.
- OM-18228: Update preview surface texture material v2
- OM-23453 Do not load/save builtin ortho camera's position
- Render settings 2.0 polish #4
- OM-24182: Update asset importer to fix transform export
- Update asset importer to fix transform export
- Add vcruntime140_1.dll for cchardet used by aiohttp
- Omni physics release update

## [2020.3.0-rc.22] - 2020-12-2

### *Changed*

- updated SDK to 100.1.41954-8470d414-release
- Adding 3 more AppWindow event types: on window drop, on window focus, on window minimize
- IApp, IAppWindow, IExtensions Interfaces now all in version 1.0

### Bug Fixes

- OM-23000: Fixed F7 crashed when the profiler extension is not loaded
- OM-23969: Fixed crash in property window
- Property window material shader fix
- Adding sampler wrapping mode selection, setting default to repeatMirrored to avoid lerp artifacts around edges
- Usd paths apply button fix
- OM-23933 Fix console window scrolling when multi-line messages are logged.
- Allow servers to validate and change their port number within a range to allow
- property window allow add reference to any prim
- fix material widget combobox index fix

## [2020.3.0-rc.21] - 2020-12-1

### *Changed*

- updated SDK to 100.1.41500-e0c51b6b-release
- Merging RTX MRs from master to release/100.1 - MRs 93-111
- omni_physics_release_update
- int64 support in property window
- ptvsd license swipat + various fixes
- Add https server. Add option to add websocket endpoint directly without needing the router.
- Cleanup kit.capture logging
- Remove deprecated cpp tagging extension, window

### Bug Fixes

- OM-23833: Fix issue that it loses focus after replacing sublayer
- OM-23937: Fix movie capture input fields' spinners status at dragging
- Tagging
  - OM-23704: Fixed tagging sort and added test
  - OM-23435: changes idl.py to a named package from a label
  - OM-23183: removes cpp packages like discovery.client.c
  - OM-23934: gets rid of tagging settings warnining

- Content Browser
  - OM-24022 Check that settings exist before subscribing to their changes.
  - OM-23355 Fixes: Search results not applying visibility filter
  - OM-24009 Fixes: connection name different from connection path
  - OM-23341 : Add missing icons for content browser light style
- RTX
  - OM-23970 GI in Reflections does not work without Sampled Lighting and looks Blocky
  - Update min driver requirements. Windows: min 456.39, recommend 456.71. Linux min 450.57, recommended 455.24
  - disable spatial and temporal rays
  - Return the geometry normal from mdlGeometryNormal
  - OM-18621: Primitive List Crash
  - Fixed incorrect initialization of depth and motion textures
  - Verify we have actual primitive line data to update and/or within range
  - This pass shouldn't be executed in transparency
  - OM-22620 Diffuse GI looks darker with PSTF
  - Release temporary load-time resources immediately
  - Always turn on progressive_aux_canvas for iray in OV.
  - Call timeBeginPeriod(1) to ensure a high resolution timer is used for the process.
  - OM-22779 View has a weird spotty shadowing even with a clear sky
  - disable light cache in rtx and kit test.
  - OM-23033 Added Support for the Color Weighted Layer Bsdf in Real-time
  - All async hydra engines share the same sync scope


## [2020.3.0-rc.20] - 2020-11-30

### *Changed*

- updated SDK to 100.1.41038-b0944ee1-release
- Updated client library to 0.18.1231 ( Critical Bug fixes)
- [omni.ui] Stop using OpenCV for tests ( Licences issues )
- gather extension pip licenses
- Add option in settings to enable/disable thumbnail generation for image files on Nucleus
- Allow endpoints to be deregistered within kit microservices.

### Bug Fixes

- OM-23515 Pasting a URL into browser bar opens the file
- display_orient_as_rotate
- OM-23914: Fix the movie capture window title
- Fixing mipgen for VectorImageProvider
- create material bind to selected PreviewSurfaceTexture fix

## [2020.3.0-rc.19] - 2020-11-26

### *Changed*

- updated SDK to 100.1.40707-a4e04f41-release
- [omni.ui] Using int64 for int based model
- Using gpu.foundation in Kit Next, improving gpu.foundation to support different modes

### Bug Fixes
- OM-23341: Support light ui style in content browser for View
- Fix missing Iray shader, iray unit test loading fix
- Don't add the GPU stats define if it isn't enabled.
- OM-23866: menu create material bind to selected fix
- OM-13522: Content window bind material
- OM-23613: replace omni.kit.ui.FilePicker with omni.kit.window.filepicker
- OM-23665: Usd paths string replace
- OM-23802: Property window move set flags under rendering
- OM-18228: added PreviewSurfaceTexture


## [2020.3.0-rc.18] - 2020-11-26

### *Changed*

- updated SDK to 100.1.40446-13ba8557-release
- Omni.UI:
  - More tests for CollapsableFrame
  - Minor change in float format in Drag/Slider/Field
- Render Settings 2.0: IRay support, renderer registration, minor improvements

### Bug Fixes
- OM-23102: Update asset importer to support simple fbx constraint
- OM-25313: Improve mangling so textures are always resolved properly
- OM-23183: discovery.client.c license check
- OM-23055: update viewport "reset all"
- OM-23833: Fix regression to replace layer in layer property widget
- OM-23243 Pasting a filename into browser bar opens the file
- OM-23515 Pasting a URL into browser bar opens the file
- OM-23746 Pasting an image URL into browser bar opens the file in image viewer
- OM-23699: move property add reference to path add menu
- OM-15582 Fix Console Window flickering and icon color
- Manual calculation of mip stride for VectorImageProvider
- OM-22803: make property references widget add window draggable
  

## [2020.3.0-rc.17] - 2020-11-25

### Changed

- updated SDK to 100.1.40060-112d454b-release
- Prevent moving of popup window
- Transform Widget: display orient as rotate
- release_omni_physics_update
- added Create App Launcher

## [2020.3.0-rc.16] - 2020-11-24

### Changed


- updated SDK to 100.1.39841-12e1550e-release
- OM-19903: Improve workflow to show layer conflict
- OM-23053: Fix RasterImageProvider mipmapping not working with legacy renderer
- move update mdl schema to material library
- IApp: fix print empty string
- IApp: allow app/name override user settings
- [stage] Refusing selection of grayed prims in search mode
- Fix event stream python leak in some apps
- OM-23626: Fix layer reorder
- OM-5169: Material widget add sub-identifiers
- Set toggleability for service/headless extensions
- OM-23604 Enable content browser to copy multiple files at once
  - Double clicking in filepicker executes apply callback.
- Fix slowdown when agent fails to start. Check port is available.
- OM-23657: Fix crash after stage failed to open
- SdfAssetPathAttributeModel edit fix


## [2020.3.0-rc.15] - 2020-11-23

### Changed

- updated SDK to 100.1.39514-2c497556-release
- Fixed IRay App, omni.create.iray
- Include new App: Create Streaming, Create HydraEngines
- OM-23408: Multi-file delete
- OM-20357: avoid_write_errors
- xform-gizmo-optimization on many object moved at once
- [next] Added support for menu hotkeys in 'Next'
- filebrowser modified_time fixed 
- filebrowser improved support for multiple files selection
- Omni.UI Removed ScrollBar color override
- Fixed crash when searching on the Content Browser
- OM-23277: fixed small issue with taggins
- Fixing crashes for the app when IRay is selected as an active renderer in config

## [2020.3.0-rc.14] - 2020-11-20

### Changed

- updated SDK to 100.1.39081-05eccb38-release
- Mipmapping for RasterImageProvider
- Achieving Kit Next parity: throttling
- Merging RTX MRs from master to release/100.1 - MRs 88-91
- Jitter for distance based hash shouldnt use cone radius (uses the distance based voxel size now)
- OM-23381 Fix uninitialized axis variable on ToolBar
- Create material select new Material
- Early log messages recording and replay for console
- OM-23351: Fix crash that is caused by saving read-only layers
- Content Browser multi-file download
- [omniui][TreeView] Don't highlight item blocked with another window

## [2020.3.0-rc.13.1] - 2020-11-19

### Changed

- updated SDK to 100.1.38677-43cfc305-release
- Only log errors and higher to stderr for Uvicorn.
- property window load material thumbnails async
- In PT, use PSTF after first bounce
- Updating Windows DLSS snippet to 29301719
- Fix OM-22911 - load time deadlock
- removed uv.y flipping from hydra mesh.cpp, subdivision.cpp
- Fixes to DLSS in reflections
- Use a similar strategy for firefly filtering during translucency computation as in the pt.
- fix multiple instance update per frame
- changing the default caustics multiplier to 20. Leaving the unit test intact.
- Flow Fixes
- FlowUsd. Automatically promote float to float3 to avoid errors with cloud render parameters on old assets.
  
## [2020.3.0-rc.13] - 2020-11-19

### Changed

- updated SDK to 100.1.38582-ac4cc907-release
- UI rendering moved to Kit Next , No editor Plugins Loaded 
- OM-7339: Merge change "Improve selection perf" to release
- [omni.ui] Added keyboard callback to ui.Window
- OM-23099: Update asset importer to referesh license and fix camera import crash
- [omni.ui] Elide text in ui.Label
- Unfocused docking tabs are darker
- OM-20935: Context menu "find in browser" fix
- OM-18282 Fix missing MDL Enum option in property widget
- [release] Turn off WebView
- Merge movie capture fixes OM-18167, 23123, 23124 and 23089 into release
- OM-23127: capture all python stdout and stderr for console and log + ext bugs fix
- Update to nv_usd with usdSkelImaging resync fix.
- OmniGraph: Fix startup issues
- Fix Windows Path Length problem when loading Textures
- shadercache fix for Create, streamclient war
- OM-15628 Hide transform and frustum gizmo when current camera is selected
- added package-info.yaml to openvr
- prevent console spam as slows dragging prims in create
- OM-15663 Livestream - replace with native StreamSdk plugin
  
## [2020.3.0-rc.12] - 2020-11-18

- updated SDK to 100.1.38111-2a2296c2-release
- physics release package update
- Render settings 2.0 - Additional polish
- OM-22918: UI: fixed some grammatical errors in file replacement confirmation dialogs.
- Improve layer merge down to match photoshop
- Increase Default Tesselation of Sphere created from the menu
- OM-23279 Remember Property Widget collapsed state. OM-23181 Move "Attribute" widget to the end
- Content Browser bug fixes for Open Beta
  - OM-23129: Crashes on double clicking in table view to open a folder
  - OM-23046: Cannot select item at bottom of table view
  - OM-23112: C: drive still showing up in omniverse collection
  - OM-22856: Fix issue that saves wrong extension
- Merging RTX MRs from master to release/100.1 - MRs 64-77
  - Faster waitForRendering to complete, add back in waitForIdle
  - Fixed a memory leak in block compression
  - enable block compression
  - Support partial device-masks in getBufferDesc() and getTextureDesc()
  - OM-19491: Autoexposure fix
  - Fixed incorrect coordinates that are used to read from stable depth
  - Compensate for the fact that the indirect GI pass runs at reduced sample rate
- OmniGraph:
  - OM-20357 Refactored creation of a new node
- Close OM-23308: Disable camera scroll only when key a-z pressed
- OM-22866: Preferences file picker fixes


## [2020.3.0-rc.11] - 2020-11-17

- updated SDK to 100.1.37439-ed8580dc-release
- OM-22722: search-service-disconnect
- ImGui: Adding stream buffer size as an option, and increasing default value two-fold
- remove omniverse-kit executable, Kit is not properly kit.exe !
- OM-22948: Preliminary support for variants (replicated from details window)
- Render Settings 2.0: now available by default in Create ( Rendering settings 1.0 deprecated in few versions)
- OM-23112: Various fixes to content browser
- OM-23161: Improve property window multi-editing perf
- OmniGraph: Fix crash on disconnction in python graphs 
- HdStorm: Added UsdPreviewSurface to Kit distribution
- Property.usd (v3.1.0): 
  - Added `target_picker_filter_lambda` to `RelationshipEditWidget`'s `additional_widget_kwargs`
  - giving access to a custom lambda filter for relationships when filtering by type is not enough.
  - Skip `displayName`, `displayGroup` and `documentation` when writing metadata for a `PlaceholderAttribute`.
- physics package update for release
- Omni.UI Fixe: button update width when text changes
- Omni.UI hard and soft min and max for fields and drags
- Splah: Add a watcher option to the Kit process for kit agent processes.
- All stage templates prims use full xform
- OM-21708: property window material name cleanup
- OM-23091: Fix icon refresh and undo bugs in layer window, Fix layer tests
- Add omni.kit.ui import to tagging window
- Created tagging property, tags column in cw2, and tagging python code to replace cpp
- Remove deepwall/cloudxr features (not scheduled for release)

## [2020.3.0-rc.10] - 2020-11-16

- updated SDK to 100.1.36882-e0596d39-release
- MR 7314: fix spash screen scaling
- OM-22034: fixes to Transform Widget
- replacing use of experience with app
- OM-20357: verify_default_values
- fixed_vulkan_depth issue
- Merging RTX MRs from master to release/100.1 - MRs 52-62
- finished work on getroughness, reflectance transmittance, and diffuse reflectance for normalized mix.
- Invalidate picking rectangle when changing resolution
- Line rendering uses stable depth
- Added a frame index to TextureLoader
- Added an interface to resource manager to get stats
- OM-22897: Improve Hydra Time in rendering
- Lower the light cache loads into the light loop.
- SLI Fixes (single-device MGPU resources, multiple resource & device release)
- Fix USD model not updating in Property Window
- OM-23008 still show xformOp attributes when xformOpOrder is empty
- Properly rename "Attribute" to "Property" in omni.kit.property.usd
- Cherry pick omnigraph changes for open beta
- OM-22322 "Kpicott//add state attribute check"
- OM-21483 Fixed visibility button in Stage Window
- OM-18713 Refactored copy service to utilize Filepicker module
- Install hdStorm per other USD plugins.
- omni_physics release update
- Make movie maker work with async rendering and fix reference to the capture extension error message at quiting

## [2020.3.0-rc.9] - 2020-11-13

- updated SDK to 100.1.36188-3684179b-release
- Add Storm to the Kit distribution
- Merging RTX MRs from master to release/100.1 - MRs 49-51
- OM-19506 Light Cache SpatialHash not working correctly with multiple GPUs
- OM-22779 View has a weird spotty shadowing even with a clear sky
- OM-22669 To stochastic LC update pass for PT
- OM-22246 Parallel shader compilation
- ext manager: update launch and install button style and behavior
- Merging RTX MRs from master to release/100.1 - MRs 35-36
- OM-22821 Property window select texture file browser error fix
- Fixed Material Menu Missing in Create
- OM-22905 Disable Rotator XYZ order editing in multiple prim selection mode
- OM-22906 Update transform property widget's preview image
- OM-22906 Make the preview image consistent with the transform widget looking
- OM-22728 rebuild transform property widget only if the current prim's xformOpOrder is updated
- OM-22823 fix material property binding display
- Fixed: Profiler available in Kit Next App
- Fixed: USDA_Edit Extension on Layers referencing omniverse files
- Improved Omni.UI Multiline field examples

## [2020.3.0-rc.8] - 2020-11-12

* updated SDK to 100.1.35726-b548abf2-release
* Editor based Create Tagged as Legacy still default for few days but almost gone..
* Omni UI Documentation App directly from the help Menu
* omni.create.vr application added ! Experimental but very cool!
* omni.create.xr renamed to omni.create.ar
* Improve layer window alignment
* Improve icons alignment in layer window
* usda_edit 1.1.3 : Fixed usda damage. Added support for content_browser
* OM-22845: Create rotate and scale for grouping operation
* OM-22899: App launch improvements
* OM-22857: Flatcache fixed
* OM-18355 OM-19490 Scale camera speed to stage unit
* Fix leak on SimplePropertyWidget build_fn
* Make splash screen optional with an option to disable
* Support Hide UI in Kit-next
* Fix multi-prim editing when attribute has None value
* USD thumbnail generation changes for windows
* Property window move audio settings to layer
* Fix Usd model/builder for Quat type when mixed
* Property window material show colourspace
* OM-22676: remove unnecessary numpy include
* Update the audio record icon

2020.3-rc.7

* updated SDK to 100.1.35138-47576970-release
* Merging RTX MRs from master to release/100.1 - MRs 1-35
* OM-21136 sphere light sample improvement
* Match Kit-next docking space style with Kit-default
* fix_progress_of_uploading_files'
* nv-usd-licensing
* omniui_profiling_release
* RTX : Use max instance of avg for LC for the time being
* Add prompt in Viewport when drawable/RTX is not available yet
* Add --/renderer/multiGpu/activeGpus option
* OM-22433, OM-22682: RT/PT MGPU mode switch fixes
* OM-21888 Sampled lighting doesnt work with fog
* Change iray_max_path_length default from -1 to 23.
* XR and Async intergration
* Poor performance of indirect diffuse (GI) in drive-sim scene (frame time from 33ms to 20ms)
* Blacklist driver up to 460.53 that has the corruption fix
* Fixing DOMELIGHT_CUBEMAP_ARRAY warning when building mdl as library.
* Updated textured lights (dome and rect) such that they now use the TextureManager to load textures.
* OM-22311: Light Gizmos are not hidden when a light's visibility is set to false
* Fixed TAA resize of vectors that keep time stamps
* fix OM-22394: match the way Arnold deals with UDIM. There are two fixes:
* Adding support for diffuse transmission in sampled lighting

2020.3-rc.6

* New SDK 
* OM-xxxx fixed

2020.3-rc.5

* New SDK 
* OM-xxxx fixed

2020.3-rc.4

* New SDK 

2020.3-rc.3

* New SDK 

2020.3-rc.2

* Improved Images and desciptions new SDK

2020.3-rc.1

* First Release