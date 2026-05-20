import omni.syntheticdata

# Example values for an attached render product and a per-product wait count.
render_product_path = "/Render/RenderProduct_Replicator"
N = 1

# Deprecated: does not advance per-sensor tick counters under multi-tick rendering.
await omni.syntheticdata.sensors.next_render_simulation_async([render_product_path], N)
