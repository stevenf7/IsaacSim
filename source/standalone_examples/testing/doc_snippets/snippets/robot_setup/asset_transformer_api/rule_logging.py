def process_rule(self) -> str | None:
    self.log_operation("SchemaRoutingRule start destination=payloads/physics.usda")
    self.log_operation("Schema patterns: Physics*, Physx*")

    # ... processing ...

    self.log_operation("Moved 5 schema(s) from /World/Robot: PhysicsRigidBodyAPI, PhysicsMassAPI, ...")
    self.log_operation("Processed 12 prim(s), moved 24 schema instance(s)")
    self.log_operation("SchemaRoutingRule completed")
