import omni.kit.app


def get_current_stage():
    return omni.usd.get_context().get_stage()
