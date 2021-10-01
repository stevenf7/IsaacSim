from pxr import Semantics, Usd


def add_update_semantics(prim: Usd.Prim, semantic_label: str, type_label: str = "class", suffix="") -> None:
    """
    Apply a semantic label to a prim or update an existing label

    Args:
        prim (Usd.Prim): Usd Prim to add or update semantics on
        semantic_label (str): The label we want to apply
        type_label (str): The type of semantic information we are specifying (default = "class")
        suffix (str): Additional suffix used to specify multiple semantic attribute names. 
        By default the semantic attribute name is "Semantics", and to specify additional 
        attributes a suffix can be provided. Simple string concatenation is used :"Semantics" + suffix (default = "")
    """
    # Apply or aquire the existing SemanticAPI
    semantic_api = Semantics.SemanticsAPI.Get(prim, "Semantics" + suffix)
    if not semantic_api:
        semantic_api = Semantics.SemanticsAPI.Apply(prim, "Semantics" + suffix)
        semantic_api.CreateSemanticTypeAttr()
        semantic_api.CreateSemanticDataAttr()

    type_attr = semantic_api.GetSemanticTypeAttr()
    data_attr = semantic_api.GetSemanticDataAttr()

    # Set the type and data for the SemanticAPI
    if type_label is not None:
        type_attr.Set(type_label)
    if semantic_label is not None:
        data_attr.Set(semantic_label)
