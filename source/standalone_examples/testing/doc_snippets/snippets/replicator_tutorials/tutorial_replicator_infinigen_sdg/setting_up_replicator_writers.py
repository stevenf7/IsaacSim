# Only create the writers if there are render products to attach to
writers = []
if render_products:
    for writer_config in writers_config:
        writer = infinigen_utils.setup_writer(writer_config)
        if writer:
            writer.attach(render_products)
            writers.append(writer)
            print(f"[SDG] {writer_config['type']}'s out dir: {writer_config.get('kwargs', {}).get('output_dir', '')}")
