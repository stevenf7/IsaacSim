# Cleanup
await rep.orchestrator.wait_until_complete_async()
writer.detach()
for render_product in render_products:
    render_product.destroy()

print("[SDG] Complete")
