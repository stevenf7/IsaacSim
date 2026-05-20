import isaacsim.core.experimental.utils.semantics as semantics_utils
import omni.usd


def remove_prefix(name, prefix):
    if name.startswith(prefix):
        return name[len(prefix) :]
    return name


def remove_numerical_suffix(name):
    suffix = name.split("_")[-1]
    if suffix.isnumeric():
        return name[: -len(suffix) - 1]
    return name


def remove_underscores(name):
    return name.replace("_", "")


stage = omni.usd.get_context().get_stage()
for prim in stage.Traverse():
    if prim.GetTypeName() == "Mesh":
        label = str(prim.GetPrimPath()).split("/")[-1]
        label = remove_prefix(label, "SM_")
        label = remove_numerical_suffix(label)
        label = remove_underscores(label)
        semantics_utils.add_labels(prim, labels=[label], taxonomy="class")
