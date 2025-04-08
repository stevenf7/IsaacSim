# Asset Thumbnails Renderer

This script is used to generate thumbnails for assets in the Omniverse platform.

## Usage

To run the script, use the following command:

```bash
python render_asset_thumbnails.py < asset_root > [--pretend] [--headless]
```

### Arguments

- `asset_root`: The root path of the Omniverse assets.
- `--pretend`: If specified, the script will not perform any actions but will show what would be done.
- `--headless`: If specified, the script will run without the UI.

### Generate Doc Asset

- Go to the asset *.thumb* folder, open the <filename>.thumb.usd file, adjust camera angle and zoom
- Set camera resolution to desired valueu (1920*1080 for docs)
- Change render to RTX path trace
- Go to Edit, Capture Screenshot or press F10 to generate screen shot
- Go to Documents/Kit/shared/screenshots for the screenshot
