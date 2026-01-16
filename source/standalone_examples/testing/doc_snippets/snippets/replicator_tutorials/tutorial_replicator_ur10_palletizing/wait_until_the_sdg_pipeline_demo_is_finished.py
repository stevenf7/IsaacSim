DEFAULT_NUM_CAPTURES = 4
DEFAULT_BIN_FLIP_FRAMES = 2
DEFAULT_PALLET_FRAMES = 2


async def run_example_async(num_captures, bin_flip_frames, pallet_frames):
    from isaacsim.examples.interactive.ur10_palletizing.ur10_palletizing import BinStacking

    # ..
    bin_staking_sample = BinStacking()
    await bin_staking_sample.load_world_async()
    await bin_staking_sample.on_event_async()
    # ..
    sdg_demo = PalletizingSDGDemo()
    sdg_demo.start(num_captures, bin_flip_frames, pallet_frames)


asyncio.ensure_future(
    run_example_async(
        num_captures=DEFAULT_NUM_CAPTURES, bin_flip_frames=DEFAULT_BIN_FLIP_FRAMES, pallet_frames=DEFAULT_PALLET_FRAMES
    )
)
