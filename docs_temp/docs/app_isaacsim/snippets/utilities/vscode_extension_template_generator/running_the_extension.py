import my.custom.extension

interface = my.custom.extension.acquire_extension_interface()
my.custom.extension.set_default_status("custom status")
interface.register_object(10)
my.custom.extension.release_extension_interface()
