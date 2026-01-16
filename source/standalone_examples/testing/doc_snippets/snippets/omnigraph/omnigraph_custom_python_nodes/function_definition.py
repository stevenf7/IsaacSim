class OgnNodeName:
    @staticmethod
    def compute(db):
        db.outputs.out = bool(db.inputs.value_input > 0.0)
        return True
