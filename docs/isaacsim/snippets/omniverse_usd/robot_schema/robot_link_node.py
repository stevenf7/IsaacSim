class RobotLinkNode:
    prim  # The USD prim for this link
    name  # Prim name (or None)
    path  # Prim path (or None)
    parent  # Parent RobotLinkNode (None for root)
    children  # List of child RobotLinkNodes
