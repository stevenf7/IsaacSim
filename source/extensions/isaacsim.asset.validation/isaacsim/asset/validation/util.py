from typing import Any, List, Optional, Sequence, Set, TypeVar, Union

import omni.usd
from pxr import Sdf, Usd, UsdGeom, UsdUtils


def is_relationship_prepended(relationship):
    """Check if a relationship is prepended in the layer stack.

    Examines the property stack of the relationship to determine if it uses
    prepended items rather than explicit items in the target path list.

    Args:
        relationship (Usd.Relationship): The USD relationship to check.

    Returns:
        bool: True if the relationship is prepended, False if it uses explicit items.
    """
    rel_stack = relationship.GetPropertyStack()
    for spec in rel_stack:
        if spec.targetPathList.isExplicit:
            # It's a non-editable list
            return False
    return True


def make_relationship_prepended(relationship):
    """Convert a relationship to use prepended items in the layer stack.

    Modifies the relationship's property specs to use prepended items instead of
    explicit items, which allows for composition with stronger layers.

    Args:
        relationship (Usd.Relationship): The USD relationship to convert.

    Returns:
        bool: True if the operation was successful.
    """

    rel_stack = relationship.GetPropertyStack()
    for spec in rel_stack:
        if spec.targetPathList.isExplicit:
            items = [i for i in spec.targetPathList.explicitItems]
            spec.targetPathList.prependedItems = items
            spec.targetPathList.explicitItems = []
    return True
