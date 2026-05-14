..
   Copyright (c) 2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaacsim_building_cpp_usd_plugins:

=========================================================
Building C++ USD Plugins Against the Standalone Installer
=========================================================

The standalone |isaac-sim_short| installer ships the USD runtime shared
libraries (under ``extscache/omni.usd.libs-*/bin/``) and the matching Python
bindings, but it does not ship the C++ headers or the ``pxrConfig.cmake``
package-config files needed to compile your own native USD plugins. This
page describes a supported workflow for obtaining matching headers and
linking native plugins against the USD libraries that |isaac-sim_short|
loads at runtime.

If you are developing in-tree against a Kit C++ extension template, use the
workflow described in :ref:`isaac_sim_cli_extension_templates` instead. The
page below is specifically for building standalone native USD plugins
(those discovered and loaded via ``Plug::Load()`` at runtime) against an
installed |isaac-sim_short| package.


When You Need This
====================

You need this workflow when you are building a C++ USD plugin that must be
loaded into a |isaac-sim_short| process, and you are starting from the
standalone installer rather than the source repository.

USD discovers your plugin at runtime by walking ``PXR_PLUGINPATH_NAME``,
parsing its ``plugInfo.json``, and then calling ``Plug::Load()``.
``Plug::Load()`` performs a normal ``dlopen()`` on your shared library,
which means your plugin must be ABI-compatible with the USD runtime
libraries already loaded in the |isaac-sim_short| process.


Prerequisites
===============

Inside the standalone installer, locate the bundled packman launcher and
the manifest that pins all of |isaac-sim_short|'s external dependencies:

.. code-block:: bash

    <isaac-sim-install>/kit/dev/tools/packman/packman
    <isaac-sim-install>/kit/dev/all-deps.packman.xml

Open ``all-deps.packman.xml`` and find the ``usd-release`` dependency
entry. It contains an inner ``<package>`` element whose ``name`` and
``version`` attributes identify the exact OpenUSD build that
|isaac-sim_short| was compiled against — for example:

.. code-block:: xml

    <dependency name="usd-release">
        <package name="usd.py312.manylinux_2_35_x86_64.stock.release"
                 version="0.25.11.kit.2-gl.19811"/>
    </dependency>

The ``name`` is platform- and Python-version-encoded; copy both
attributes verbatim into your own packman project file (see below).

You also need the Python development headers that ship inside the
installer:

.. code-block:: bash

    <isaac-sim-install>/kit/python/include/python3.XX/

The USD ``Ar`` and ``Tf`` headers transitively include Boost.Python via
``TfPyObjWrapper``, so even a plugin that does not directly call Python
must be able to ``#include <Python.h>``.


Pull Matching USD Dev Artifacts With Packman
==============================================

Create a small packman project file next to your plugin source — for
example, ``usd-dev.packman.xml``:

.. code-block:: xml

    <project toolsVersion="6.0">
      <!--
        Replace PACKAGE_NAME_FROM_ALL_DEPS and VERSION_FROM_ALL_DEPS with
        the inner <package> element's name and version copied verbatim
        from the usd-release entry in
        <isaac-sim-install>/kit/dev/all-deps.packman.xml.
      -->
      <dependency name="usd-release" linkPath="_deps/usd-release">
        <package name="PACKAGE_NAME_FROM_ALL_DEPS" version="VERSION_FROM_ALL_DEPS"/>
      </dependency>
    </project>

Then pull the matching dev artifacts using the packman bundled with the
installer:

.. code-block:: bash

    <isaac-sim-install>/kit/dev/tools/packman/packman pull \
        usd-dev.packman.xml --platform linux-x86_64

After ``packman pull`` finishes, ``_deps/usd-release/`` will contain the
USD development tree:

.. code-block:: bash

    _deps/usd-release/
      include/
        pxr/        # OpenUSD C++ headers; in OpenUSD 25.x and later,
                    # Boost.Python is vendored under pxr/external/boost/
        tbb/        # TBB headers used by USD
      lib/          # Packman-built USD libraries (do NOT link against these)
      pxrConfig.cmake
      cmake/

Use ``include/`` for compilation. ``pxrConfig.cmake`` is shipped in the
drop, but it transitively ``find_dependency()``-loads the
``*Config.cmake`` files for TBB, MaterialX, Imath, and OpenSubdiv, and
the ``usd-release`` packman drop does not include them. A plain
``find_package(pxr REQUIRED)`` therefore fails to resolve. The recipe in
the next section sidesteps this by pointing CMake at ``include/``
directly. **Do not** link your plugin against the libraries under
``_deps/usd-release/lib/`` — see the next section.


Compile and Link
==================

The build needs:

* Headers from ``_deps/usd-release/include/`` and from
  ``<isaac-sim-install>/kit/python/include/python3.XX/``.
* Link directory ``<isaac-sim-install>/extscache/omni.usd.libs-*/bin/``
  (the libraries |isaac-sim_short| loads at runtime), **not**
  ``_deps/usd-release/lib/``.
* Link libraries ``usd_ar``, ``usd_sdf``, ``usd_tf``, ``usd_plug``,
  ``usd_vt`` (add more as your plugin requires).
* Linker flag ``-Wl,--no-as-needed`` around those libraries.

The same paths and flags apply to any build system, but how each tool
expresses them differs — some accept absolute filesystem paths
directly, others encourage wrapping pre-built libraries as targets or
referencing them through workspace-local paths. Use whatever mechanism
is idiomatic for your build system. As an example, in CMake:

.. code-block:: cmake

    cmake_minimum_required(VERSION 3.20)
    project(my_usd_plugin LANGUAGES CXX)

    set(CMAKE_CXX_STANDARD 17)
    set(CMAKE_CXX_STANDARD_REQUIRED ON)

    # Python development headers shipped inside Isaac Sim.
    set(ISAAC_SIM_INSTALL "/path/to/isaac-sim" CACHE PATH "Isaac Sim install root")
    set(ISAAC_SIM_USD_LIBS "${ISAAC_SIM_INSTALL}/extscache/omni.usd.libs-<version>/bin"
        CACHE PATH "Directory containing libusd_*.so shipped with Isaac Sim")
    set(ISAAC_SIM_PYTHON_INCLUDE "${ISAAC_SIM_INSTALL}/kit/python/include/python3.XX"
        CACHE PATH "Python development headers shipped inside Isaac Sim")

    add_library(my_usd_plugin SHARED my_usd_plugin.cpp)

    # Use the packman-pulled headers directly; do not call find_package(pxr).
    # See the prose above for why pxrConfig.cmake is intentionally bypassed.
    target_include_directories(my_usd_plugin PRIVATE
        "${CMAKE_SOURCE_DIR}/_deps/usd-release/include"
        "${ISAAC_SIM_PYTHON_INCLUDE}"
    )

    # Link against the USD libraries Isaac Sim actually loads at runtime,
    # not the libraries packman pulled. Linking against packman's libs
    # produces a binary that resolves to one set of pxrInternal_v0_* symbols
    # at link time and a (potentially different) set at runtime, which
    # manifests as undefined-symbol errors inside Plug::Load().
    target_link_directories(my_usd_plugin PRIVATE "${ISAAC_SIM_USD_LIBS}")
    target_link_libraries(my_usd_plugin PRIVATE
        -Wl,--no-as-needed
        usd_ar
        usd_sdf
        usd_tf
        usd_plug
        usd_vt
        -Wl,--as-needed
    )

Two link-line details matter:

1. ``-Wl,--no-as-needed`` is required around the ``usd_*`` libraries.
   Without it, the linker drops any USD library whose symbols are only
   referenced through the C++ vtable and RTTI of your plugin class — and
   for any class discovered by ``Plug`` that is essentially every USD
   library you depend on. The result is a plugin that links cleanly but
   fails inside ``Plug::Load()`` at runtime with undefined-symbol errors
   against ``pxrInternal_v0_*::...``.
2. The library search path passed to the linker must be
   ``<isaac-sim-install>/extscache/omni.usd.libs-*/bin/``, **not**
   ``_deps/usd-release/lib/``. The packman-pulled libraries are built
   with the same OpenUSD version but are not necessarily the exact same
   binaries |isaac-sim_short| ships, and any mismatch (including build
   flags or symbol versioning) produces silent ABI breakage.

At runtime, set ``PXR_PLUGINPATH_NAME`` (or place your ``plugInfo.json``
under a directory USD already scans) so that |isaac-sim_short| discovers
your plugin during stage open.


Plugin Source Requirements
============================

USD's plugin registration macros (``TF_REGISTRY_FUNCTION``,
``TF_REGISTRY_FUNCTION_WITH_TAG``) expand at global namespace scope and
reference unqualified ``Tf_RegistryInit`` and the per-library tag
``MFB_ALT_PACKAGE_NAME``. Two source-level requirements are not
optional:

1. Define three preprocessor macros at compile time, one per plugin
   target. They identify the plugin to USD's registry; the values are
   conventionally the same short name in three case variants. In CMake,
   this looks like:

   .. code-block:: cmake

       target_compile_definitions(my_usd_plugin PRIVATE
           MFB_PACKAGE_NAME=myUsdPlugin
           MFB_ALT_PACKAGE_NAME=myUsdPlugin
           MFB_PACKAGE_MODULE=MyUsdPlugin
       )

2. Place ``PXR_NAMESPACE_USING_DIRECTIVE`` near the top of any
   translation unit that uses ``TF_REGISTRY_FUNCTION``, so that the
   unqualified ``Tf_RegistryInit`` inside the macro expansion resolves
   to the OpenUSD inline namespace:

   .. code-block:: cpp

       #include <pxr/pxr.h>
       #include <pxr/base/tf/type.h>
       #include <pxr/usd/ar/resolver.h>

       PXR_NAMESPACE_USING_DIRECTIVE

       class MyResolver : public ArResolver { /* ... */ };

       TF_REGISTRY_FUNCTION(TfType) {
           TfType::Define<MyResolver, TfType::Bases<ArResolver>>();
       }

Without either, the plugin will not compile.


Keeping Headers and Runtime In Sync
=====================================

OpenUSD encodes its release version in the ``pxrInternal_v0_*`` inline
namespace. A plugin compiled against one OpenUSD release cannot be loaded
into a process that links a different OpenUSD release — the mangled
symbol names will not match, and you will see undefined-symbol errors
inside ``Plug::Load()``.

The OpenUSD version shipped inside |isaac-sim_short| can change across
releases. The table below records known mappings; always confirm the
exact version by inspecting the ``usd-release`` entry inside the
``all-deps.packman.xml`` of the installer you are targeting.

.. list-table::
    :header-rows: 1
    :widths: 25 25 50

    * - |isaac-sim_short| version
      - OpenUSD version
      - Inline namespace (``pxrInternal_v0_*``)
    * - 5.1.0
      - 24.05
      - ``pxrInternal_v0_24_5__pxrReserved__``
    * - 6.0.0
      - 25.11
      - ``pxrInternal_v0_25_11__pxrReserved__``

.. caution::

    The packman approach in this page automatically pulls the matching
    OpenUSD headers for the installer you target, so you should not need
    to read the inline-namespace strings yourself. They are listed here
    only as a diagnostic aid: if you see an undefined symbol that
    contains ``pxrInternal_v0_24_5`` but your plugin was compiled against
    ``pxrInternal_v0_25_11``, the headers and runtime are out of sync and
    the link step is pointing at the wrong USD libraries. Confirm the
    exact namespace string for your installer with ``nm -D --defined-only
    extscache/omni.usd.libs-*/bin/libusd_tf.so | head`` before
    relying on this table.


Related
=========

* :ref:`isaac_sim_cli_extension_templates` — in-tree C++ Kit extension
  development against the |isaac-sim_short| source repository. Use this
  workflow when you can build inside the repo; use the page above when
  you can only build against the standalone installer.
* :ref:`isaac_sim_app_usd_tools` — GUI-side USD tooling shipped with
  |isaac-sim_short|.
