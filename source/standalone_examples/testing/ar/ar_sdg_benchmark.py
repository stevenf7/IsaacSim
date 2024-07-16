# Copyright 2024 Amazon.com, Inc. or its affiliates. All Rights Reserved.

import argparse
import logging
import os

# from omni.isaac.kit import SimulationApp
from isaacsim import SimulationApp

# Add logging formatter
logging.basicConfig(
    format="%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def define_arguments() -> None:
    """Defines the command line arguments."""
    # TODO [VSPL-4582] - Add debugging/testing (optionally create new layers, etc)

    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", type=str, help="Scene to load")
    parser.add_argument("--num_datasets", type=int, default=3, help="Number of datasets to record")
    parser.add_argument("--num_frames", type=int, default=10, help="Number of images to render per dataset")
    parser.add_argument("--num_subframes", type=int, default=-1, help="Number of subframes to use per render")
    parser.add_argument("--num_steps", type=int, default=15, help="Number of physics steps between rendered outputs")
    parser.add_argument(
        "--output_path",
        type=str,
        default=os.getcwd() + "/output",
        help="Location where data will be output",
    )
    parser.add_argument(
        "--renderer",
        type=str,
        choices=["PathTracing", "RayTracedLighting"],
        default="PathTracing",
        help="Renderer to use, PathTracing by default",
    )
    parser.add_argument(
        "--windowed",
        help="Whether to run the application in foreground. If not provided the application will run headlessly",
        action="store_true",
    )
    parser.add_argument(
        "--debug",
        help="Whether to set logger level to debug. If not provided, logger will run with level info",
        action="store_true",
    )
    parser.add_argument(
        "--fabric",
        type=str,
        choices=["NoFabric", "WriteToStage", "WriteToLayer"],
        default="NoFabric",
        help="Fabric test options, NoFabric by default",
    )
    parser.add_argument(
        "--test",
        help="Whether to run the application in test mode. If not provided the application will run in normal mode",
        action="store_true",
    )
    parser.add_argument(
        "--backend-type",
        default="OsmoKPIFile",
        choices=["LocalLogMetrics", "JSONFileMetrics", "OsmoKPIFile"],
        help="Benchmarking backend, defaults",
    )

    return parser


if __name__ == "__main__":
    """Main entry point for the synthetic data generations."""

    # Create argument parser
    parser = define_arguments()
    args, _ = parser.parse_known_args()

    renderer = args.renderer
    headless = False if args.windowed else True
    scene = args.scene
    output_path = args.output_path
    if not os.path.isabs(output_path):
        output_path = os.path.join(os.getcwd(), output_path)
    num_datasets = int(args.num_datasets)
    num_frames = int(args.num_frames)
    num_subframes = int(args.num_subframes)
    num_steps = int(args.num_steps)
    debug = args.debug
    fabric = args.fabric
    test_mode = args.test

    # Default rendering parameters
    config = {
        "renderer": renderer,
        "headless": headless,
        "samples_per_pixel_frame": 16,
    }

    # Logging parameters.
    logger.info("Starting Simulation App with the following params")
    logger.info(f"Scene: {scene}")
    logger.info(f"Output Path: {output_path}")
    logger.info(f"Num Datasets: {num_datasets}")
    logger.info(f"Num Frames: {num_frames}")
    logger.info(f"Num Subframes: {num_subframes}")
    logger.info(f"Num Steps: {num_steps}")
    logger.info(f"Renderer: {renderer}")
    logger.info(f"Headless: {headless}")

    # Start simulation app
    kit = SimulationApp(launch_config=config)

    from omni.isaac.core.utils.extensions import enable_extension

    enable_extension("omni.isaac.benchmark.services")
    from omni.isaac.benchmark.services import BaseIsaacBenchmark

    # Create the benchmark
    benchmark = BaseIsaacBenchmark(
        benchmark_name="ar_sdg_benchmark",
        workflow_metadata={
            "metadata": [
                {"name": "num_datasets", "data": num_datasets},
                {"name": "num_frames", "data": num_frames},
                {"name": "num_subframes", "data": num_subframes},
                {"name": "num_steps", "data": num_steps},
            ]
        },
        backend_type=args.backend_type,
    )

    # start synthetic data generation
    from orchestrator import Orchestrator

    # step 1: Setup
    benchmark.set_phase("loading", start_recording_frametime=False, start_recording_runtime=True)
    orchestrator = Orchestrator(scene, kit, num_frames, num_subframes, num_steps, output_path, fabric, debug)
    # Run for a few frames to ensure everything is loaded
    for _ in range(10):
        kit.update()
    benchmark.store_measurements()

    # step 2: Loop over the datasets
    benchmark.set_phase("benchmark")
    for idx in range(1, num_datasets + 1):
        variation_output_path: str = os.path.join(output_path, str(idx).zfill(5))
        # step 3: Randomize
        orchestrator.create_variation(variation_output_path)
        # step 4: Advance Simulation and Render
        orchestrator.run(variation_output_path)
    benchmark.store_measurements()

    # close and exit
    kit.close()
