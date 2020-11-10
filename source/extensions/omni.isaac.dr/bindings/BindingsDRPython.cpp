// Copyright (c) 2019-2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "omni/isaac/dr/DomainRandomizer.h"

#include <carb/BindingsPythonUtils.h>

#include <memory>
#include <string>
#include <vector>

CARB_BINDINGS("omni.isaac.dr.python")

namespace omni
{
namespace isaac
{
namespace dr
{

}
}
}

namespace
{

PYBIND11_MODULE(_dr, m)
{
    using namespace carb;
    using namespace omni::isaac::dr;

    m.doc() = R"pbdoc(
        This extension provides an interface to a Domain Randomization(DR) prim defined in a stage.
        
        Example:
            To use this interface you must first call the acquire interface function.
            You can create a cube in the editor (``Create->Shapes->Cube``) and then use the DR commands to create a DR color component.
            Then use the interface to call API to switch to manual mode.
            
            ::

                import omni
                import omni.isaac.dr as dr
                dr_interface = dr._dr.acquire_dr_interface()
                # Create DR color component
                result, prim = omni.kit.commands.execute(
                    "CreateColorComponentCommand",
                    prim_paths=["/World/Cube"],
                    first_color_range=(0.0, 0.0, 0.0),
                    second_color_range=(1.0, 1.0, 1.0),
                    roughness_range=(0.0, 1.0),
                    metallic_range=(0.0, 1.0),
                    duration=0.3,
                    include_children=False,
                )
                # Switch to manual mode
                dr_interface.toggle_manual_mode()
            
            Next, use the interface to call API to randomize the scene once.

            ::

                # Randomize the scene once
                dr_interface.randomize_once()

            Finally, you can switch back to non-manual mode by calling the ``toggle_manual_mode()`` again.
            By pressing play in the editor, you will see the color of the cube change every 0.3 seconds.

            ::

                # Switch to manual mode
                dr_interface.toggle_manual_mode()
                # Python equivalent of pressing play in editor
                editor = omni.kit.editor.get_editor_interface()
                if not editor.is_playing():
                    editor.play()

        
        Refer to the sample documentation for more examples and usage
                )pbdoc";

    defineInterfaceClass<DomainRandomizer>(m, "DomainRandomizer", "acquire_dr_interface", "release_dr_interface")
        .def("randomize_once", wrapInterfaceFunction(&DomainRandomizer::randomizeOnce), R"pbdoc(
                 Randomizes the scene once. This is mainly executed while in manual mode.
             )pbdoc")
        .def("toggle_manual_mode", wrapInterfaceFunction(&DomainRandomizer::toggleManualMode), R"pbdoc(
                 Toggles mode between manual and non-manual. In manual mode, user can control when scene randomization occur whereas in non-manual mode scene randomization is controlled via the duration parameter in various DR components.
             )pbdoc");
}
}
