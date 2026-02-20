# Inject a experience config
sys.argv.insert(1, f'{os.environ["EXP_PATH"]}/isaacsim.exp.base.python.kit')

# Add paths to extensions
sys.argv.append(f"--ext-folder")
sys.argv.append(f'{os.path.abspath(os.environ["ISAAC_PATH"])}/exts')

# Run headless
sys.argv.append("--no-window")
