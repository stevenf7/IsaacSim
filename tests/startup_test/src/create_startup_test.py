import json
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List

import dssim_py
from nv_benchflow.client import Benchmark, script
from nv_benchflow.config import BenchmarkConfig, EnvConfig
from ovat_outputs import FileOutput, Outputs, TestOutput


@dataclass
class ImageTest:
    """Holds information about a test case"""

    name: str
    output_filename: str
    stage_path: str
    golden_filename: str = ""
    camera_path: str = ""
    wait_after_load: float = 5
    image_width: int = 1280
    image_height: int = 720
    threshold: float = 0.01
    hdr: bool = False
    viewport_gizmos: bool = False
    num_assets_loaded: int = 1
    enabled_renderers: str = "rtx"
    stats_file: str = ""
    timeout: int = 200


# Test cases to be executed in this OVAT test
TEST_LIST = (
    ImageTest(
        name="Astronaut",
        golden_filename="astronaut_golden.png",
        output_filename="astronaut.png",
        stage_path=f"omniverse://ov-sandbox/NVIDIA/Samples/Astronaut/Astro_USD.usd",
        camera_path="/Root/Camera",
        wait_after_load=15,
    ),
)
SCREENSHOT_SCRIPT = Path(__file__).parent / "kit-screenshot" / "screenshot.py"


def prepare_app():
    """Finds the service, sets it up and warms shaders"""
    create_runner = Benchmark.services.find_service("CreateRunner", "1.0")
    create_runner.prepare()
    create_runner.set_env("OMNI_USER", "test")
    # Warm up shaders
    create_runner.run_kit(args=f'--exec "{SCREENSHOT_SCRIPT} --quit"', timeout=240)
    return create_runner


def run_image_tests(create_runner) -> Outputs:
    # All images and stats reports go to a temp dir
    output_dir = Path(tempfile.mkdtemp())
    # For each test we will add two outputs to the Outputs collection
    outputs = Outputs()

    for test in TEST_LIST:
        Benchmark.log_info(f"Running test: {test.name}")

        # get a handle to each TestOutput we measure
        _render_test = outputs.add(TestOutput(name=f"{test.name} Render Test"))
        _exit_test = outputs.add(TestOutput(name=f"{test.name} Exit Test"))

        # the generated image
        _golden_file = None
        if test.golden_filename:
            _golden_file = Path(__file__).parent / "golden" / test.golden_filename
        _outfile = output_dir / test.output_filename

        # build args list for script
        screenshot_args = f"-s {test.stage_path} -o {_outfile} --res_x {test.image_width} --res_y {test.image_height}"

        if test.camera_path:
            screenshot_args = f"{screenshot_args} -c {test.camera_path}"
        if test.viewport_gizmos:
            screenshot_args = f"{screenshot_args} --viewport_gizmos"
        if test.hdr:
            screenshot_args = f"{screenshot_args} --hdr"

        screenshot_args = f"{screenshot_args} --num_assets_loaded {test.num_assets_loaded}"
        screenshot_args = f"{screenshot_args} --wait_after_load {test.wait_after_load}"

        # store the stats
        stats_file = output_dir / f"{_outfile.stem}.json"
        screenshot_args = f"{screenshot_args} --stats_file {stats_file}"

        screenshot_args = f"{screenshot_args} --stats_file {stats_file}"
        args = f'--exec "{SCREENSHOT_SCRIPT} {screenshot_args}"'
        if test.enabled_renderers:
            args = f"{args} --/renderer/enabled={test.enabled_renderers}"

        # Run the render test
        with _render_test.timer:
            # careful, stdout and stderr can be bytes!
            return_code, stdout, stderr, timed_out = create_runner.run_kit(args=args, timeout=test.timeout)
        Benchmark.log_info(f"Kit ran {test.name} in {_render_test.timer.duration}s")

        # Check for a clean exit
        if timed_out:
            _exit_test.set_failed(
                f"Kit timed out, that means it hung during the render test. Return code: {return_code}"
            )
            Benchmark.log_warn(
                f"Kit timed out. Got return code {return_code} (instead of 0), {test.name} exit test failed."
            )
        elif return_code != 0:
            _exit_test.set_failed(f"Kit crashed on exit. Return code: {return_code}")
            Benchmark.log_warn(f"Kit crashed on exit. Return code: {return_code}, {test.name} exit test failed.")

        # Store Kit's logfile for each image
        kit_log = create_runner.get_log_path()
        if kit_log and kit_log.exists():
            log_file = output_dir / f"{_outfile.stem}_kit.log"
            shutil.move(str(kit_log), log_file)
            outputs.add(FileOutput(log_file))

        # Store the console output because errors still show up there!
        console_file: Path = output_dir / f"{_outfile.stem}_kit_terminal.log"
        console_file.write_text(f"**STDOUT**\n{stdout}\n**STDERR**\n{stderr}")
        outputs.add(FileOutput(console_file))

        # Now check the render output
        if not _outfile.exists():
            _render_test.set_failed("Kit did not render an image at all")
            Benchmark.log_warn(f"Kit did not render an image at all, {test.name} render test failed.")
            continue
        else:
            _render_test.add_image_metadata("Generated Image", str(_outfile))

        if _golden_file:
            _render_test.add_image_metadata("Reference Image", str(_golden_file))
            _diff_img = output_dir / f"{_outfile.stem}_diff{_outfile.suffix}"

            # dssim_py throws an error if the images differ in size
            try:
                ssim = dssim_py.compare(str(_golden_file), str(_outfile), diff_output=str(_diff_img))
                Benchmark.log_info(f"{test.name} SSIM score: {ssim}")

                _render_test.add_number_metadata("SSIM Value", ssim)
                _render_test.add_image_metadata("Differences", _diff_img)

                # magic numbers for the win! we'll fix this with OVAT Metrics
                if ssim > test.threshold:
                    _render_test.set_failed_comparison("SSIM too high", test.threshold, ssim)
                # did the test pass and do we have a stats file?
                elif test.stats_file:
                    # capture the stats
                    try:
                        stats = json.loads(stats_file.read_text())
                        load_time = stats["load_time"]
                        Benchmark.log_info(f"{test.name} Load Time: {load_time}")
                        _render_test.add_number_metadata("Load Time", load_time)
                    except Exception as e:
                        Benchmark.log_warn(f"Stats decoding failed: {e}")
                        pass

            except ValueError as e:
                Benchmark.log_error(f"Kit generated an image with an invalid size. {test.name} render test failed.")
                Benchmark.log_error(str(e))
                _render_test.set_failed("Generated image size is invalid", details=str(e))

    return outputs


@script(
    "PYScript Create Render Test", "0.1", script_type=BenchmarkConfig.Type.Execution, os_type=EnvConfig.OSType.Windows
)
class CreateRenderTest:
    def run(self):
        """Run is the main entrypoint for Execution scripts"""
        Benchmark.log_info("Started Create Render Tests")

        kit_runner = prepare_app()

        # Run all the image benchmarks
        outputs = run_image_tests(kit_runner)

        # Finally push all the outputs to GTL
        outputs.submit()


if __name__ == "__main__":
    Benchmark.run()
