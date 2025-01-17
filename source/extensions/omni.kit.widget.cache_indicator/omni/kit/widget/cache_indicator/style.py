from .icons import Icons


class Styles:
    CACHE_STATE_ITEM_STYLE = None
    LIVE_STATE_ITEM_STYLE = None

    @staticmethod
    def on_startup():
        # It needs to delay initialization of style as icons need to be initialized firstly.
        Styles.CACHE_STATE_ITEM_STYLE = {
            # TODO currently hidding this next line... because is crashing the extension... need to check later
            # "Image::doc": {"image_url": Icons.get("docs"), "color": 0xB04B4BFF},
            "Label::offline": {"color": 0xB04B4BFF},
            "Rectangle::offline": {"border_radius": 2.0},
            "Rectangle::offline": {"background_color": 0xFF808080},
            "Rectangle::offline:hovered": {"background_color": 0xFF9E9E9E},
        }
