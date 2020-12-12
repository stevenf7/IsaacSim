This folder contains OVAT tests, not unit tests

# createrunner

This folder contains code from:
https://gitlab-master.nvidia.com/ovat/services/kit-runner-service/-/tree/OM-21520/src 
https://gitlab-master.nvidia.com/ovat/libraries/kit-runner/-/tree/OM-21520/kit_runner

which I have copied and pasted here to improve development velocity... (currently developing libraries and services involves the use of pip, poetry, benchmark upload, git (for the TC side, and committing all of the code) and for me at least, there are too many moving parts.

Once we have a stable platform, the code should go back into the OVAT project, other than any create specific parts which can stay in this repo



# startup_test

This contains startup test for create... and the infrastructure required to glue it, the create runnerservice above, and any other services or "components"  used in your test




# To run locally (on Windows)
The test script and createrunner service  can be tested locally using the .\run_test.bat(.sh) script.
This will set up a local gcn daemon, read the gcn.yml file, splice in any overrides from the ovat_test.toml file (to create a gcn_local.yml) and submit that job to the local gcn daemon to execute. Some example overides are below

```
"Absolute EXE Path" = ["ResolvePath", "../../_build/windows-x86_64/release/omni.create.bat"]
"Absolute EXE Path" = ["ResolvePath", "C:/Users/eoinm/.ovat/GCN/Work/Temp/task_api_17_11_2020/ovat-kit.ith5amm4/create/_build/windows-x86_64/release/omni.create.bat"]
+"name of the experience" = "create"
+"Realtime stdout and stderr" = true
```

# To run in production (on Windows)
If you have made any changes to the two components here, you must upload them to GCN like this:

```
(venvwin) PS C:\myfolder>benchmark_upload.exe .\createrunnerservice.py --version-tag=dev --gtl-user eoinm --debug
(venvwin) PS C:\myfolder>benchmark_upload.exe .\create_startup_test.py --version-tag=dev --gtl-user eoinm --debug

The entire folder and it's subfolders will be uploaded. The requirements.txt files will be read and those dependencies added somewhere in GTL to the build

You must take the version number that you get back from GTL, and add it to the task_architect.yml file that your submission script uses (and make sure the version-tag matches also). You can also use the Build ID (TODO: add example)

# Linux
Linux is not quite there, see https://nvidia.slack.com/archives/CLWD9DXLK/p1605838389060000?thread_ts=1605050956.446900&cid=CLWD9DXLK

# References
+ see https://confluence.nvidia.com/display/~eoinm/Developing+for+OVAT for some unstructured tips
+ see https://confluence.nvidia.com/display/~eoinm/Using+OVAT+with+Kit+-+FAQ for some more info, links to the real docs etc


# Tips

You can take the input to a test as logged to the shell and run it locally... (you may need to cange some of the paths e.g)

from
```
C:\Users\eoinm\.ovat\GCN\Work\Temp\task_api_4w_vhc21\ovat-kit.qzkkn3lq\create\_build\windows-x86_64\release\omni.create.bat --exec "C:\Users\eoinm\.ovat\GCN\Work\Data\scratchpad\cli-20d3a76576d0877f5dad674a24b77a8c523509ecb16eabde56a54c5eeeb7fef3\kit-screenshot\screenshot.py -s omniverse://sandbox.ov.nvidia.com:3009/Projects/Dev/Kitchen_set/Kitchen_set.usd -o C:\Users\eoinm\.ovat\GCN\Work\Temp\task_api_4w_vhc21\tmpr001ssqa\create_kitchen_set.png --res_x 1280 --res_y 720 -c /Root/Camera --num_assets_loaded 1 --wait_after_load 15 --stats_file C:\Users\eoinm\.ovat\GCN\Work\Temp\task_api_4w_vhc21\tmpr001ssqa\create_kitchen_set.json --stats_file C:\Users\eoinm\.ovat\GCN\Work\Temp\task_api_4w_vhc21\tmpr001ssqa\create_kitchen_set.json --capture_app" --/renderer/enabled=rtx --carb/log/sources/carb.fastcache.plugin/level=Warning
```

to
```
C:\eoin\code\omniverse\ov-create\_build\windows-x86_64\release\omni.create.bat --exec " C:\eoin\code\omniverse\ov-create\tests\startup_test\src\kit-screenshot\screenshot.py -s omniverse://sandbox.ov.nvidia.com:3009/Projects/Dev/Kitchen_set/Kitchen_set.usd -o C:\temp\create_kitchen_set.png --res_x 1280 --res_y 720 -c /Root/Camera --num_assets_loaded 1 --wait_after_load 15 --stats_file C:\temp\create_kitchen_set.json --stats_file C:\temp\create_kitchen_set.json --capture_app" --/renderer/enabled=rtx --carb/log/sources/carb.fastcache.plugin/level=Warning
```