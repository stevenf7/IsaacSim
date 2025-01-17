import omni.client
import omni.kit.app
import omni.kit.test


class TestCacheIndicatorWidget(omni.kit.test.AsyncTestCase):
    async def test_menu_setup(self):
        import omni.kit.ui_test as ui_test

        menu_widget = ui_test.get_menubar()
        menu = menu_widget.find_menu("Cache State Widget")
        self.assertTrue(menu)
