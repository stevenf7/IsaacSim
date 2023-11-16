# omni.isaac.gym.benchmark

## Usage

To enable this extension, go to the Extension Manager menu and enable omni.isaac.gym.benchmark extension.

## How to Read the Perflab Reports

### Test Name and Segments

Test Name indicates the name of the test. Most tests are run with multiple parameters, so the name of the test identifies the test and the parameters used. The task name is embedded into the name of the tests.

#### Extension Tests:
Extension tests contain `_extension` in the test name. These tests are divided into two categories:
- `no_render` tests are run without viewport enabled
- `render` tests are run with viewport enabled

Each extension test covers one task and contains four measurements:
- `scene_loading`: includes environment creation and simulation startup time.
- `train_benchmark`: measures per-frame metrics for the first 10 iterations of RL training (including simulation).
- `sim_start`: measures the time it takes for the timeline to start (including physics simulation) without RL
- `sim_benchmark`: measures per-frame metrics for 20 steps without RL (including simulation)

#### Standalone Tests:
Standalone tests contain `_standalone` in the test name. These tests are divided into multiple categories, where the
parameters of the tests are embedded into the name of the tests.
- `headless` tests are run without the app window in headless mode
- `render` tests are run with the app window
- Names contain parameters `{task_name}_{pipeline}_{sim_device}`. `task_name` is the name of the task. `pipeline` is the 
tensor API pipeline that is being run (CPU or GPU). `sim_device` is the device in which physics simulation runs on. 
Valid combinations of pipeline and sim device are: `GPU pipeline + GPU sim`, `CPU pipeline + GPU sim`, `CPU pipeline + CPU sim`.

Each standlone test covers one task and measures the overall training time for 10 iterations: `train_benchmark`. 
This measurement includes kit instance launch time, overall startup time, scene creation time, training time, and shutdown time.

### Hardware

- Indicates whether the GPU or Render Thread data is shown
  - Render Thread refers to the CPU, which is primarily used to measure the total time to do an app update (presumably, one frame)
  - GPU data is measuring only the time taken to render that frame on the GPU
  - The difference of these two times is any CPU overhead that was not overlapped by the GPU
- The GPU data is typically the most important, as it is more likely to be the bottleneck when simulating robots, sensors, and/or other render products
