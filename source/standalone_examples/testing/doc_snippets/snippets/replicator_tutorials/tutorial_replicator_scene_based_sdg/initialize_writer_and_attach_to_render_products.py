def setup_writer(config: dict) -> rep.Writer | None:
    """Setup and initialize writer with optional backend support."""

    def normalize_output_dir(params):
        if "output_dir" in params and not os.path.isabs(params["output_dir"]):
            params["output_dir"] = os.path.join(os.getcwd(), params["output_dir"])

    writer_type = config.get("writer", "BasicWriter")
    if writer_type not in rep.WriterRegistry.get_writers():
        print(f"[SDG] Writer type '{writer_type}' not found in registry.")
        return None

    writer = rep.WriterRegistry.get(writer_type)
    writer_kwargs = dict(config.get("writer_config", {}))
    normalize_output_dir(writer_kwargs)

    backend_type = config.get("backend_type")
    backend = None
    if backend_type:
        try:
            backend = rep.backends.get(backend_type)
        except Exception as e:
            print(f"[SDG] Backend '{backend_type}' not found: {e}")
            return None

        backend_params = dict(config.get("backend_params", {}))
        normalize_output_dir(backend_params)

        try:
            print(f"[SDG] Backend: {backend_type} | Params: {backend_params}")
            backend.initialize(**backend_params)
        except TypeError as e:
            print(f"[SDG] Invalid backend params: {e}")
            return None

    if "output_dir" in writer_kwargs:
        print(f"[SDG] Output: {writer_kwargs['output_dir']}")

    backend_info = f" + {backend_type}" if backend else ""
    print(f"[SDG] Writer: {writer_type}{backend_info} | Config: {writer_kwargs}")

    try:
        if backend:
            writer.initialize(backend=backend, **writer_kwargs)
        else:
            writer.initialize(**writer_kwargs)
    except TypeError as e:
        print(f"[SDG] Invalid writer params: {e}")
        return None

    return writer
