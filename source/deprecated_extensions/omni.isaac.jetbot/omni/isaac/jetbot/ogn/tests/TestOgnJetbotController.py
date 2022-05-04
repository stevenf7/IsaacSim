import omni.kit.test
import omni.graph.core as og
import omni.graph.core.tests as ogts
import os
import carb


class TestOgn(ogts.test_case_class(use_schema_prims=True, allow_implicit_graph=False)):
    async def test_import(self):
        import omni.isaac.jetbot.ogn.OgnJetbotControllerDatabase

        self.assertTrue(hasattr(omni.isaac.jetbot.ogn.OgnJetbotControllerDatabase, "OgnJetbotControllerDatabase"))

    async def test_usda(self):
        test_file_name = "OgnJetbotControllerTemplate.usda"
        usd_path = os.path.join(os.path.dirname(__file__), "usd", test_file_name)
        if not os.path.exists(usd_path):
            self.assertTrue(False, f"{usd_path} not found for loading test")
        (result, error) = await ogts.load_test_file(usd_path)
        self.assertTrue(result, f"{error} on {usd_path}")
        test_node = og.Controller.node("/TestGraph/Template_omni_isaac_jetbot_JetbotController")
        self.assertTrue(test_node.is_valid())
        node_type_name = test_node.get_type_name()
        self.assertEqual(og.GraphRegistry().get_node_type_version(node_type_name), 1)
        self.assertTrue(test_node.get_attribute_exists("inputs:execIn"))

        self.assertTrue(test_node.get_attribute_exists("inputs:forwardVelocity"))

        input_attr = test_node.get_attribute("inputs:forwardVelocity")
        actual_input = og.Controller.get(input_attr)
        ogts.verify_values(
            0,
            actual_input,
            "omni.isaac.jetbot.JetbotController USD load test - inputs:forwardVelocity attribute value error",
        )
        self.assertTrue(test_node.get_attribute_exists("inputs:rotationVelocity"))

        input_attr = test_node.get_attribute("inputs:rotationVelocity")
        actual_input = og.Controller.get(input_attr)
        ogts.verify_values(
            0,
            actual_input,
            "omni.isaac.jetbot.JetbotController USD load test - inputs:rotationVelocity attribute value error",
        )
