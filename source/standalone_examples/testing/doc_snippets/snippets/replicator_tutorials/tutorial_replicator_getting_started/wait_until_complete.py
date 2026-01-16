while not BackendDispatch.is_done_writing():
    await omni.kit.app.get_app().next_update_async()
