===================================
Redistributable Omniverse Software 
===================================

NVIDIA offers the following Omniverse components for distribution at no cost:

#. **Connect SDK** - The devkit for accelerating the development of connectors and converters.
#. **Kit Kernel and Extensions for Configurator Runtime** - These components can be distributed as part of an Omniverse Enterprise subscription for the sole purpose to create and redistribute Digital Product Configurators that run on the NVIDIA Graphics Delivery Network (GDN) service.  

Connect SDK
------------
The Connect SDK is the devkit for accelerating the development of connectors and converters. The Connect SDK binary artifacts are available via an install script in the `NVIDIA-Omniverse/connect-samples GitHub repository <https://github.com/NVIDIA-Omniverse/connect-samples>`__ and includes the required and optional components that make up the Connect SDK.

If you agree to the NVIDIA Omniverse License, you may modify and distribute the Connect SDK libraries subject to the software's License Terms.

Kit and Extensions for Configurator Runtime
---------------------------------------------
There are two components that can be distributed for Configurator Runtimes: 

#. **Kit Kernel** - This is the core of Kit which provides the base framework to run an application defined by a list of extensions and a configuration file. Kit Kernel is available via a download from Launcher and GitHub. (Available Soon)  
#. **Kit Extensions** - We provide a list of extensions which enable you to build a viewer-type application which are redistributable. Kit Extensions for redistribution are shared below. 

Configurator Runtime is defined in the License Terms to mean software-based tools or applications that facilitate the customization or modification of digital or physical products by selecting or adjusting the features, components, or design elements of a product through a digital interactive interface. If your configurator falls under this definition, you can redistribute these components. If you are uncertain, please contact us. 

Subject to the licensing terms of the Omniverse software and your license type, you can freely distribute the following features applicable to KIT version 105.1.*: 

+---------------------+--------------------------------------------------+-----------+
| Modules             | Extension                                        | Version   |
+=====================+==================================================+===========+
|| Activity Monitor   || omni.activity.core                              || 1.0.1    |
||                    || omni.activity.profiler                          || 1.0.2    |
||                    || omni.activity.pump                              || 1.0.0    |
||                    || omni.activity.ui                                || 1.0.21   |
||                    || omni.activity.usd_resolver                      || 1.0.1    |
+---------------------+--------------------------------------------------+-----------+
|| Animation Runtime  || omni.anim.curve                                 || 105.23.0 |
||                    || omni.anim.timeline                              || 105.0.15 |
+---------------------+--------------------------------------------------+-----------+
| Application Window  | omni.appwindow                                   | 1.1.1     |
+---------------------+--------------------------------------------------+-----------+
|| Miscellaneous      || omni.debugdraw                                  || 0.1.2    |
||                    || omni.genproc.core                               || 105.1.5  |
||                    || omni.gpu_foundation                             || 0.0.0    |
||                    || omni.gpucompute.plugins                         || 0.0.0    |
||                    || omni.iray.libs                                  || 0.0.0    |
+---------------------+--------------------------------------------------+-----------+
|| Omni Graph Runtime || omni.graph                                      || 1.106.0  |
||                    || omni.graph.action                               || 1.55.0   |
||                    || omni.graph.core                                 || 2.139.7  |
||                    || omni.graph.exec                                 || 0.2.7    |
||                    || omni.graph.io                                   || 1.5.1    |
||                    || omni.graph.nodes                                || 1.106.2  |
||                    || omni.graph.scriptnode                           || 1.1.6    |
||                    || omni.graph.tools                                || 1.41.2   |
||                    || omni.graph.ui                                   || 1.47.0   |
+---------------------+--------------------------------------------------+-----------+
|| Hydra              || omni.hydra.engine.stats                         || 1.0.1    |
||                    || omni.hydra.rtx                                  || 0.1.0    |
||                    || omni.hydra.scene_delegate                       || 0.3.2    |
||                    || omni.hydra.usdrt_delegate                       || 7.2.19   |
+---------------------+--------------------------------------------------+-----------+
| Inspection          | omni.inspect                                     | 1.0.1     |
+---------------------+--------------------------------------------------+-----------+
|| Kit Core           || carb.audio                                      || 0.1.0    |
||                    || carb.windowing.plugins                          || 1.0.0    |
||                    || omni.kit.actions.core                           || 1.0.0    |
||                    || omni.kit.audiodeviceenum                        || 1.0.1    |
||                    || omni.kit.clipboard                              || 1.0.3    |
||                    || omni.kit.commands                               || 1.4.6    |
||                    || omni.kit.context_menu                           || 1.6.3    |
||                    || omni.kit.exec.core                              || 0.4.1    |
||                    || omni.kit.helper.file_utils                      || 0.1.5    |
||                    || omni.kit.hotkeys.core                           || 1.3.0    |
||                    || omni.kit.hydra_texture                          || 1.1.6    |
||                    || omni.kit.loop-default                           || 0.2.0    |
||                    || omni.kit.mainwindow                             || 1.0.0    |
||                    || omni.kit.notification_manage                    || 1.0.6    |
||                    || omni.kit.pip_archive                            || 0.0.0    |
||                    || omni.kit.pipapi                                 || 0.0.0    |
||                    || omni.kit.primitive.mesh                         || 1.0.14   |
||                    || omni.kit.property.usd                           || 3.21.9   |
||                    || omni.kit.telemetry                              || 0.4.0    |
||                    || omni.kit.test                                   || 0.0.0    |
||                    || omni.kit.uiapp                                  || 0.0.0    |
||                    || omni.ramp                                       || 105.1.12 |
||                    || omni.resourcemonitor                            || 105.0.0  |
||                    || omni.scene.visualization.core                   || 105.4.10 |
||                    || omni.assets.plugins                             || 0.0.0    |
||                    || omni.client                                     || 1.0.1    |
||                    || omni.kit.async_engine                           || 0.0.0    |
||                    || omni.volume                                     || 0.3.0    |
+---------------------+--------------------------------------------------+-----------+
|| Manipulators       || omni.kit.manipulator.camera                     || 105.0.4  |
||                    || omni.kit.manipulator.prim                       || 105.0.9  |
||                    || omni.kit.manipulator.selection                  || 104.0.7  |
||                    || omni.kit.manipulator.selector                   || 1.0.1    |
||                    || omni.kit.manipulator.tool.snap                  || 1.3.1    |
||                    || omni.kit.manipulator.transform                  || 104.6.14 |
||                    || omni.kit.manipulator.viewport                   || 104.0.8  |
+---------------------+--------------------------------------------------+-----------+
|| Menus              || omni.kit.menu.file                              || 1.1.7    |
||                    || omni.kit.menu.utils                             || 1.5.3    |
+---------------------+--------------------------------------------------+-----------+
| Raycast             | omni.kit.mesh.raycast                            | 105.3.1   |
+---------------------+--------------------------------------------------+-----------+
|| Render             || omni.kit.renderer.capture                       || 0.0.0    |
||                    || omni.kit.renderer.core                          || 0.0.0    |
||                    || omni.kit.renderer.imgui                         || 0.0.0    |
||                    || omni.kit.renderer.init                          || 0.0.0    |
||                    || omni.rtx.settings.core                          || 0.5.11   |
||                    || omni.rtx.shadercache.d3d12                      || 1.0.0    |
||                    || omni.rtx.shadercache.vulkan                     || 1.0.0    |
||                    || omni.rtx.window.settings                        || 0.6.9    |
+---------------------+--------------------------------------------------+-----------+
| Search              | omni.kit.search_core                             | 1.0.4     |
+---------------------+--------------------------------------------------+-----------+
| Selection           | omni.kit.selection                               | 0.1.2     |
+---------------------+--------------------------------------------------+-----------+
| Stages              | omni.kit.stage_templates                         | 1.1.19    |
+---------------------+--------------------------------------------------+-----------+
|| Viewport           || omni.kit.viewport.actions                       || 105.0.9  |
||                    || omni.kit.viewport.bundle                        || 104.0.1  |
||                    || omni.kit.viewport.legacy_gizmos                 || 1.0.14   |
||                    || omni.kit.menubar.bottom                         || 1.0.3    |
||                    || omni.kit.viewport.menubar.camera                || 105.1.6  |
||                    || omni.kit.viewport.menubar.core                  || 105.0.17 |
||                    || omni.kit.viewport.menubar.display               || 105.0.2  |
||                    || omni.kit.viewport.menubar.lighting              || 105.0.5  |
||                    || omni.kit.viewport.menubar.render                || 105.1.0  |
||                    || omni.kit.viewport.menubar.resolution            || 1.1.4    |
||                    || omni.kit.viewport.navigation.camera_manipulator || 1.0.20   |
||                    || omni.kit.viewport.navigation.core               || 1.0.15   |
||                    || omni.kit.viewport.registry                      || 104.0.4  |
||                    || omni.kit.viewport.utility                       || 1.0.16   |
||                    || omni.kit.viewport.window                        || 105.1.7  |
+---------------------+--------------------------------------------------+-----------+
|| Widgets            || omni.kit.widget.browser_bar                     || 2.0.8    |
||                    || omni.kit.widget.filebrowser                     || 2.3.34   |
||                    || omni.kit.widget.filter                          || 1.1.2    |
||                    || omni.kit.widget.graph                           || 1.8.2    |
||                    || omni.kit.widget.highlight_label                 || 1.0.1    |
||                    || omni.kit.widget.nucleus_connector               || 1.1.0    |
||                    || omni.kit.widget.nucleus_info                    || 1.0.1    |
||                    || omni.kit.widget.options_menu                    || 1.0.5    |
||                    || omni.kit.widget.path_field                      || 2.0.7    |
||                    || omni.kit.widget.prompt                          || 1.0.5    |
||                    || omni.kit.widget.search_delegate                 || 1.0.5    |
||                    || omni.kit.widget.searchable_combobox             || 1.1.1    |
||                    || omni.kit.widget.searchfield                     || 1.0.3    |
||                    || omni.kit.widget.settings                        || 1.0.3    |
||                    || omni.kit.widget.spinner                         || 1.0.5    |
||                    || omni.kit.widget.stage                           || 2.9.2    |
||                    || omni.kit.widget.text_editor                     || 1.0.2    |
||                    || omni.kit.widget.toolbar                         || 1.5.6    |
||                    || omni.kit.widget.versioning                      || 1.4.4    |
||                    || omni.kit.widget.viewport                        || 105.1.2  |
||                    || omni.kit.widgets.custom                         || 1.0.5    |
+---------------------+--------------------------------------------------+-----------+
|| Window             || omni.kit.window.about                           || 1.2.3    |
||                    || omni.kit.window.cursor                          || 1.1.1    |
||                    || omni.kit.window.drop_support                    || 1.0.1    |
||                    || omni.kit.window.file                            || 1.3.41   |
||                    || omni.kit.window.file_exporter                   || 2.10.2   |
||                    || omni.kit.window.file_importer                   || 1.0.22   |
||                    || omni.kit.window.filepicker                      || 1.0.21   |
||                    || omni.kit.window.popup_dialog                    || 2.0.22   |
||                    || omni.kit.window.preferences                     || 1.3.20   |
||                    || omni.kit.window.property                        || 1.9.6    |
||                    || omni.kit.window.status_bar                      || 0.1.5    |
||                    || omni.kit.window.title                           || 1.1.3    |
+---------------------+--------------------------------------------------+-----------+
|| Materials          || omni.mdl                                        || 0.1.2    |
||                    || omni.mdl.neuraylib                              || 0.2.0    |
||                    || omni.mtlx                                       || 0.1.0    |
+---------------------+--------------------------------------------------+-----------+
|| Services           || omni.services.core                              || 1.6.3    |
||                    || omni.services.facilities.base                   || 1.0.3    |
||                    || omni.services.transport.server.base             || 1.1.1    |
||                    || omni.services.transport.server.http             || 1.3.0    |
||                    || omni.services.usd                               || 1.1.0    |
||                    || omni.stats                                      || 0.0.0    |
||                    || omni.timeline                                   || 1.0.9    |
+---------------------+--------------------------------------------------+-----------+
|| User Interface     || omni.ui                                         || 2.16.8   |
||                    || omni.ui.scene                                   || 1.6.12   |
||                    || omni.ui_query                                   || 1.1.1    |
||                    || omni.uiaudio                                    || 1.0.0    |
+---------------------+--------------------------------------------------+-----------+
|| USD                || omni.usd                                        || 1.10.11  |
||                    || omni.usd.config                                 || 1.0.3    |
||                    || omni.usd.core                                   || 1.1.5    |
||                    || omni.usd.libs                                   || 1.0.0    |
||                    || omni.usd.schema.anim                            || 0.0.0    |
||                    || omni.usd.schema.audio                           || 0.0.0    |
||                    || omni.usd.schema.geospatial                      || 0.0.0    |
||                    || omni.usd.schema.omnigraph                       || 1.0.0    |
||                    || omni.usd.schema.omniscripting                   || 1.0.0    |
||                    || omni.usd.schema.physics                         || 0.0.0    |
||                    || omni.usd.schema.physx                           || 0.0.0    |
||                    || omni.usd.schema.scene.visualization             || 2.0.2    |
||                    || omni.usd.schema.semantics                       || 0.0.0    |
||                    || omni.usd_resolver                               || 1.0.0    |
||                    || omni.kit.usd.layers                             || 2.1.17   |
||                    || omni.kit.usd_undo                               || 0.1.2    |
||                    || usdrt.scenegraph                                || 7.1.6    |
+---------------------+--------------------------------------------------+-----------+





