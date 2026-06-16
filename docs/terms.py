TERMS = """
.. role:: raw-html(raw)
   :format: html
.. |br| raw:: html

   <br />
.. |hr| raw:: html

   <hr />
.. |h2_topics| raw:: html

   <h2>Topics</h2>
.. |spark_long| replace:: NVIDIA DGX™ Spark
.. |spark_short| replace:: DGX Spark
.. |a2f_long| replace:: NVIDIA Omniverse™ Audio2Face
.. |a2f_short| replace:: Audio2Face
.. |a2f| replace:: Omniverse Audio2Face
.. |action_graph| replace:: Action Graph
.. |aec_long| replace:: NVIDIA Omniverse™ AEC Experience
.. |aec| replace:: Omniverse™ AEC Experience
.. |application_short| replace:: App
.. |application| replace:: Omniverse App
.. |applications_short| replace:: Apps
.. |apps_long| replace:: NVIDIA Omniverse™ Apps
.. |apps_short| replace:: Apps
.. |alias_short| replace:: Alias Connector
.. |apps| replace:: Omniverse Apps
.. |blast_long| replace:: NVIDIA Omniverse™ Blast
.. |blast_short| replace:: Blast
.. |blast| replace:: Omniverse™ Blast
.. |boom_long| replace:: NVIDIA Omniverse™ Boom
.. |boom_short| replace:: Boom
.. |boom| replace:: Omniverse™ Boom
.. |cloudxr_long| replace:: NVIDIA Omniverse™ CloudXR
.. |cloudxr_short| replace:: CloudXR
.. |cloudxr| replace:: Omniverse CloudXR
.. |code_long| replace:: NVIDIA Omniverse™ Code
.. |code_short| replace:: Code
.. |code| replace:: Omniverse Code
.. |con_short| replace:: Connect
.. |connect_long| replace:: NVIDIA Omniverse™ Connect
.. |connect_short| replace:: Omniverse Connect
.. |connect| replace:: NVIDIA Omniverse™ Connect
.. |connect_sdk_short| replace:: Connect SDK
.. |connector_short| replace:: Connector
.. |connectors_long| replace:: NVIDIA Omniverse™ Connectors
.. |connectors_short| replace:: Connectors
.. |connectors| replace:: Omniverse Connectors
.. |create_long| replace:: NVIDIA Omniverse™ Create
.. |create_short| replace:: Create
.. |create| replace:: Omniverse Create
.. |composer| replace:: Omniverse USD Composer
.. |composer_long| replace:: NVIDIA Omniverse™ USD Composer
.. |usd_composer| replace:: USD Composer
.. |composer_short| replace:: Composer
.. |presenter| replace:: Omniverse USD Presenter
.. |usd_presenter| replace:: USD Presenter
.. |presenter_short| replace:: Presenter
.. |presenter_long| replace:: NVIDIA Omniverse™ USD Presenter
.. |drive_long| replace:: NVIDIA Omniverse™ Drive
.. |drive| replace:: Omniverse Drive
.. |exp_long| replace:: NVIDIA Omniverse™ Experiences
.. |exp| replace:: Omniverse Experiences
.. |ext_long| replace:: NVIDIA Omniverse™ Extensions
.. |ext_short| replace:: Extensions
.. |ext| replace:: Omniverse Extensions
.. |extension_short| replace:: Extension
.. |flow_long| replace:: NVIDIA Omniverse™ Flow
.. |flow_short| replace:: Flow
.. |flow| replace:: Omniverse™ Flow
.. |houdini_short| replace:: Houdini Connector
.. |interactive_render| replace:: RTX – Interactive (Path Tracing)
.. |iray_long| replace:: NVIDIA® Iray®
.. |iray_render| replace:: RTX – Accurate (Iray)
.. |iray| replace::  Iray®
.. |isaac-sdk_long| replace:: NVIDIA Isaac SDK™
.. |isaac-sdk_short| replace:: Isaac SDK
.. |isaac-sdk| replace:: Isaac SDK
.. |isaac-sim_long| replace:: NVIDIA Isaac Sim
.. |isaac-sim_short| replace:: Isaac Sim
.. |isaac-sim_version| replace:: 6.0.1
.. |isaac-sim_version_strong| replace:: :raw-html:`<strong>6.0.1</strong>`
.. |isaac-sim| replace:: NVIDIA Isaac Sim
.. |cumotion| replace:: `cuMotion <https://nvidia-isaac.github.io/cumotion/>`__
.. |kaolin_long| replace:: NVIDIA Omniverse™ Kaolin
.. |kaolin_short| replace:: Kaolin
.. |kaolin| replace:: Omniverse Kaolin
.. |kit_long| replace:: NVIDIA Omniverse™ Kit
.. |kit_short| replace:: Kit
.. |kit| replace:: Omniverse Kit
.. |launcher_long| replace:: NVIDIA Omniverse™ Launcher
.. |launcher_short| replace:: Launcher
.. |launcher| replace:: Omniverse Launcher
.. |mach_long| replace:: NVIDIA Omniverse™ Machinima
.. |mach_short| replace:: Machinima
.. |mach| replace:: Omniverse Machinima
.. |machinima_short| replace:: Machinima
.. |machinima_long| replace:: NVIDIA Omniverse™ Machinima
.. |machinima| replace:: Omniverse Machinima
.. |max_long| replace:: NVIDIA Omniverse™ 3ds Max Connector
.. |max_short| replace:: 3DS Max Connector
.. |max| replace:: Omniverse 3ds Max Connector
.. |maya_long| replace:: NVIDIA Omniverse™ Maya Connector
.. |maya_short| replace:: Maya Connector
.. |maya| replace:: Omniverse Maya Connector
.. |mdl| replace:: MDL
.. |mdl_long| replace:: NVIDIA Material Definition Language
.. |mtl| replace:: Omniverse™ Materials
.. |microsvc_short| replace:: Microservices
.. |ngsearch| replace:: NGSearch
.. |nuc_long| replace:: NVIDIA Omniverse™ Nucleus
.. |nuc_short| replace:: Nucleus
.. |nuc| replace:: Omniverse Nucleus
.. |nv_rtx| replace:: NVIDIA RTX
.. |nv| replace:: NVIDIA
.. |omni_ent_long| replace:: NVIDIA Omniverse™ Enterprise
.. |omni_ind_long| replace:: NVIDIA Omniverse™ for Individuals
.. |omni_long| replace:: NVIDIA Omniverse™
.. |omni| replace:: Omniverse
.. |omnigraph_long| replace:: NVIDIA Omniverse™ OmniGraph
.. |omnigraph_short| replace:: OmniGraph
.. |omnigraph| replace:: Omniverse OmniGraph
.. |ovc_long| replace:: NVIDIA Omniverse Cloud™ Platform-as-a-Service (PaaS)
.. |ovc| replace:: Omniverse Cloud PaaS
.. |optix_denoiser_long| replace:: NVIDIA OptiX™ AI-Accelerated Denoiser
.. |optix_denoiser| replace:: OptiX Denoiser
.. |paraview_long| replace:: NVIDIA Omniverse™ ParaView Connector
.. |paraview_short| replace:: ParaView Connector
.. |paraview| replace:: Omniverse ParaView Connector
.. |physics_short| replace:: Physics
.. |omni_physics| replace:: Omniverse™ Physics
.. |physx_long| replace:: NVIDIA PhysX SDK
.. |physx_sdk| replace:: PhysX SDK
.. |physx_short| replace:: PhysX
.. |physx| replace:: PhysX SDK
.. |plat_long| replace:: NVIDIA Omniverse™ Platform
.. |plat| replace:: Omniverse Platform
.. |push_graph| replace:: Push Graph
.. |real_time_render| replace:: RTX - Real-Time
.. |reshade| replace:: ReShade
.. |revit_long| replace:: NVIDIA Omniverse™ Revit Connector
.. |revit_short| replace:: Revit Connector
.. |revit| replace:: Omniverse Revit Connector
.. |rhino_long| replace:: NVIDIA Omniverse™ Rhino Connector
.. |rhino_short| replace:: Rhino Connector
.. |rhino| replace:: Omniverse Rhino Connector
.. |robotics_long| replace:: NVIDIA Omniverse™ Robotics Experience
.. |robotics_short| replace:: Robotics Experience
.. |robotics| replace:: Omniverse™ Robotics Experience
.. |rtx_long| replace:: NVIDIA Omniverse RTX™ Renderer
.. |rtx| replace:: Omniverse RTX Renderer
.. |showroom_long| replace:: NVIDIA Omniverse™ Showroom
.. |showroom_short| replace:: Showroom
.. |showroom| replace:: Omniverse Showroom
.. |sim_long| replace:: NVIDIA Omniverse™ Simulation
.. |sim_short| replace:: Simulation
.. |sim| replace:: Omniverse Simulation
.. |skup_long| replace:: NVIDIA Omniverse™ SketchUp Connector
.. |skup_short| replace:: SketchUp Connector
.. |skup| replace:: Omnvierse SketchUp Connector
.. |sun_study| replace:: Sun Study
.. |ue4_long| replace:: NVIDIA Omniverse™ Unreal Engine Connector
.. |ue4_short| replace:: Unreal Engine Connector
.. |ue4| replace:: Omniverse Unreal Engine Connector
.. |usdview| replace:: USDView
.. |view_long| replace:: NVIDIA Omniverse™ View
.. |view_short| replace:: View
.. |view| replace:: View
.. |viewport| replace:: Viewport
.. |warp_short| replace:: Warp
.. |warp| replace:: Omniverse Warp
.. |warp_long| replace:: NVIDIA Omniverse™ Warp
.. |web_long| replace:: NVIDIA Omniverse™ Web
.. |web| replace:: Omniverse Web
.. |dev| replace:: Omniverse Developer
.. |proj| replace:: Omniverse Project
.. _isaac-sim_long: ../../isaacsim/index.html
.. |dev_app_description| replace:: An Omniverse App is built upon a specific set of Extensions to provide a desired functionality. An App gives the user a customized experience by implementing the UI’s of its Extensions with a custom layout. You can quickly and easily create customized Apps comprised of any number of Extensions developed by you, the Omniverse Community or NVIDIA. An App can be as simple as a 3D viewer or as complex as an AI suite. This modular approach to building Apps makes it easy to create a customized workflow or a global scale cloud application
.. |dev_connector_description| replace:: An Omniverse Connector is middleware with which Omniverse and other software applications communicate with each other. They enable the import/export 3D assets, data, and models between different tools and workflows. It's important to note that this means using USD as the "go between" format to convert 3D data.
.. |dev_service_description| replace:: Omniverse comes with a built-in services framework based on Omniverse Kit and its extensions. Its aim is to provide the tooling required to easily and quickly build services, that can leverage the power of any of the Kit Extensions. The services framework enables developers to deploy services.
.. |dev_extension_description| replace:: An extension is a uniquely named and versioned package loaded at runtime. Extensions are are powerful plugins that can be used to extend the functionality of existing apps such as USD Explorer and Omniverse Code.
.. |dev_guide_create_description| replace:: Before development can begin, you must first create a new Project. There are many ways to create an Omniverse Project, and the method you choose depends on what you intend to build and how you prefer to work. Projects tend to align within distinct categories, yet there remains remarkable flexibility within each category to help you address the needs of the user.
.. |dev_guide_package_description| replace:: At the conclusion of your development and testing phases, packaging your project is often necessary in preparation for publishing. While some extensions may not require this step, it becomes essential for applications and more complex extensions involving advanced features. The packaging process organizes and structures your project assets for delivery and deployment. The specifics of the packaging step depend on your desired method of distribution.
.. |dev_guide_kit_project_template_tutorial| replace:: `Kit Project Template Tutorial <https://docs.omniverse.nvidia.com/kit/docs/kit-project-template/latest/tutorial.html>`__
.. |dev_guide_kit_app_template_tutorial| replace:: `Kit App Template Tutorial <https://docs.omniverse.nvidia.com/kit/docs/kit-app-template/latest/index.html>`__
.. |dev_guide_develop_description| replace:: After creating a new Project, the development phase begins. In this phase, you configure and use an assortment of tools and extensions to fit the needs of your project.
.. |dev_guide_build_description| replace:: Depending on the nature of your project, a 'build step' may be required as development progresses. Omniverse supports this step with a variety of scripts and tools that generate a representation of the final product, enabling subsequent testing, debugging, and packaging.
.. |dev_guide_debug_description| replace:: Recognizing the critical role of debugging in development, Omniverse offers tools and automation to streamline and simplify debugging workflows. In combination with third-party tools, Omniverse accelerates bug and anomaly detection, aiming for steady increases in project stability throughout the development process.
.. |explorer_short| replace:: USD Explorer
.. |explorer| replace:: Omniverse USD Explorer
.. |explorer_long| replace:: NVIDIA Omniverse™ USD Explorer
.. |dev_guide_basic_template| replace:: `Basic Template Repository <https://github.com/NVIDIA-Omniverse/kit-project-template>`__
.. |dev_guide_advanced_template| replace:: `Advanced Template Repository <https://github.com/NVIDIA-Omniverse/kit-app-template>`__
.. |repo_tools_documentation| replace:: `Repo Tools <http://omniverse-docs.s3-website-us-east-1.amazonaws.com/repo_man/>`__
.. |carbonite_sdk| replace:: `Carbonite SDK <https://docs.omniverse.nvidia.com/kit/docs/carbonite/latest/index.html>`__
.. |thin_package_type| replace:: :term:`Thin Package`
.. |fat_package_type| replace:: :term:`Fat Package`
.. |linux| replace:: :term:`Linux`
.. |windows| replace:: :term:`Windows`
.. |nvidia_eula| replace:: `NVIDIA Omniverse License Agreement <https://docs.omniverse.nvidia.com/dev-guide/latest/common/NVIDIA_Omniverse_License_Agreement.html>`__
.. |omniverse_dev_page| replace:: `Omniverse <https://developer.nvidia.com/omniverse/>`__
"""
