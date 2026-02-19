import omni.ext
from isaacsim.asset.transformer import RuleRegistry

from .rules import AnotherRule, MyCustomRule


class MyExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        registry = RuleRegistry()
        registry.register(MyCustomRule)
        registry.register(AnotherRule)

    def on_shutdown(self):
        pass
