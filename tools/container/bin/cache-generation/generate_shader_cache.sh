#!/usr/bin/env bash

set -e
set -u

# Check for libGLX_nvidia.so.0 (needed for Vulkan):
ldconfig -p | grep libGLX_nvidia.so.0 || NOTFOUND=1
if [[ -v NOTFOUND ]]; then
    cat << EOF > /dev/stderr

Fatal Error: Cannot find libGLX_nvidia.so.0...

Ensure running with NVIDIA runtime (using "--gpus all" or "--runtime nvidia").

EOF
    exit 1
fi


# Detect NVIDIA Vulkan API version, and create ICD:
#    /opt/nvidia/omniverse/vkapiversion/bin/vkapiversion \
export VK_ICD_FILENAMES=/tmp/nvidia_icd.json
export LD_LIBRARY_PATH="/opt/nvidia/omniverse/kit-sdk-launcher/plugins/carb_gfx"
LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/nvidia/omniverse/kit-sdk-launcher/plugins/gpu.foundation"
LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/nvidia/omniverse/kit-sdk-launcher/extscore/omni.gpu_foundation/bin/deps"
### >>>
LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/nvidia/omniverse/kit-sdk-launcher/extscore/omni.assets.plugins/bin"
LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/nvidia/omniverse/kit-sdk-launcher/extscore/omni.assets.plugins/bin/deps"
LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/nvidia/omniverse/kit-sdk-launcher/extscore/omni.client/bin"
LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/nvidia/omniverse/kit-sdk-launcher/extscore/omni.client/bin/deps"
LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/nvidia/omniverse/kit-sdk-launcher/exts/omni.gpu_foundation/bin"
LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/nvidia/omniverse/kit-sdk-launcher/exts/omni.gpu_foundation/bin/deps"
LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/nvidia/omniverse/kit-sdk-launcher/exts/omni.gpucompute.plugins/bin"
LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/nvidia/omniverse/kit-sdk-launcher/exts/omni.gpucompute.plugins/bin/deps"
LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/nvidia/omniverse/kit-sdk-launcher/exts/omni.hydra.iray/bin"
LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/nvidia/omniverse/kit-sdk-launcher/exts/omni.hydra.iray/bin/deps"
LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/nvidia/omniverse/kit-sdk-launcher/exts/omni.hydra.rtx/bin/"
LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/nvidia/omniverse/kit-sdk-launcher/exts/omni.hydra.rtx/bin/deps"
LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/nvidia/omniverse/kit-sdk-launcher/exts/omni.kit.renderer.imgui/bin"
LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/nvidia/omniverse/kit-sdk-launcher/exts/omni.kit.renderer.imgui/bin/deps"
LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/nvidia/omniverse/kit-sdk-launcher/exts/omni.mdl.neuraylib/bin" # No /deps
LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/nvidia/omniverse/kit-sdk-launcher/exts/omni.stats/bin"
LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/nvidia/omniverse/kit-sdk-launcher/exts/omni.stats/bin/deps"
LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/nvidia/omniverse/kit-sdk-launcher/exts/omni.usd.libs/bin"
LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/nvidia/omniverse/kit-sdk-launcher/exts/omni.usd.libs/bin/deps"
LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/nvidia/omniverse/kit-sdk-launcher/exts/omni.volume/bin"
LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/nvidia/omniverse/kit-sdk-launcher/exts/omni.volume/bin/deps"
# LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/opt/nvidia/omniverse/vkapiversion/bin/vkapiversion"
### <<<
LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:${VK_ICD_FILENAMES}"


echo "========================================================================"
echo "Getting driver & GPU information..."
echo "========================================================================"

# Extract driver version from `nvidia-smi`:
DRIVER_VERSION=`nvidia-smi --query-gpu=driver_version --format=csv,noheader --id=0`
# Remove spaces from the GPU name, as `nvidia-smi` returns a human-friendly GPU
# name such as "NVIDIA A40", which is unsuitable for a Packman package name:
GPU_NAME=`nvidia-smi --query-gpu=gpu_name --format=csv,noheader --id=0 | sed -r 's/[ ]+/-/g'`
# Extract the Kit SDK version obtained by parsing the output of `./kit --help`:
KIT_SDK_VERSION=`/opt/nvidia/omniverse/kit-sdk-launcher/kit --help | sed -n -e 's/Kit Version: //p' | sed 's/+/./g' `
# Build the Packman package version name to be used for the packages generated
# from the artifacts resulting from the warmup procedure:
echo "Kit SDK version:          '${KIT_SDK_VERSION}'"
echo "Application name:         '${APP_PACKMAN_PACKAGE_NAME}"
echo "Application version:      '${APP_PACKMAN_PACKAGE_VERSION}'"
echo "GPU name:                 '${GPU_NAME}'"
echo "Driver version:           '${DRIVER_VERSION}'"

# TODO: Additional application and shader caches to consider when using
# Omniverse Create include the following:
#    * Warp caches?
#    * Physics caches?
#    * Additional material/USD caches?
#    * Cooked mesh cache?
#    * etc.


echo "========================================================================"
echo "Checking for existing packman packages..."
echo "========================================================================"

check_if_packman_package_exists () {
    PACKMAN_PACKAGE_NAME=$1
    PACKMAN_PACKAGE_VERSION=$2

    echo "Checking if there is an existing packman package that already exists:"
    echo "------------------------------------------------------------------------"
    echo "PACKMAN_PACKAGE_NAME=${PACKMAN_PACKAGE_NAME}"
    echo "PACKMAN_PACKAGE_VERSION=${PACKMAN_PACKAGE_VERSION}"
    echo "------------------------------------------------------------------------"

    # Using `packman resolve NAME VERSION` since `packman list <PREFIX>` is VERY slow.
    result=$(/opt/nvidia/packman/packman resolve $PACKMAN_PACKAGE_NAME $PACKMAN_PACKAGE_VERSION)
    if [ -z $result ]; then
        echo "This package does not exist."
    else
        # To do: Add ability to force
        echo "An existing package name/version already exists:"
        echo $result
        echo "Nothing to do."
        save_package_details_to_dotenv_artifact "${PACKMAN_PACKAGE_NAME}" "${PACKMAN_PACKAGE_VERSION}"
        echo "Exiting."
        exit 0
    fi
}

save_package_details_to_dotenv_artifact () {
    PACKMAN_PACKAGE_NAME=$1
    PACKMAN_PACKAGE_VERSION=$2
    # Save the resulting package information to a file so we can expose a dotenv artifact in CI...
    echo "========================================================================"
    echo "Saving packman package name/version to file: $GENERATED_CACHE_PACKAGE_DOTENV_FILE"
    echo "------------------------------------------------------------------------"
    echo "KIT_APP_DRIVER_SHADER_CACHE_PACKAGE_NAME=${PACKMAN_PACKAGE_NAME}" | tee -a $GENERATED_CACHE_PACKAGE_DOTENV_FILE
    echo "KIT_APP_DRIVER_SHADER_CACHE_PACKAGE_VERSION=${PACKMAN_PACKAGE_VERSION}" | tee -a $GENERATED_CACHE_PACKAGE_DOTENV_FILE
    echo "========================================================================"
}

# Check
PACKMAN_PACKAGE_NAME="kit-app-driver-shader-cache"
PACKMAN_PACKAGE_VERSION="${KIT_SDK_VERSION}.${GPU_NAME}.${DRIVER_VERSION}"
check_if_packman_package_exists "${PACKMAN_PACKAGE_NAME}" "${PACKMAN_PACKAGE_VERSION}"


echo "========================================================================"
echo "Running: generate_shader_cache.kit" $@
echo "========================================================================"

export APP_SHADER_CACHE_PATH="/opt/nvidia/omniverse/shader-caches/app-shader-cache"
export DRIVER_APP_SHADER_CACHE_PATH="/opt/nvidia/omniverse/shader-caches/driver-app-shader-cache"
mkdir -p "${APP_SHADER_CACHE_PATH}"
mkdir -p "${DRIVER_APP_SHADER_CACHE_PATH}"

# Minimalistic warmup for the container.
#
# Other cache settings of potential interest:
#    --rtx/shaderDb/shaderCachePath=...
#    --rtx/shaderDb/appShaderCachePath=...
#    --rtx/shaderDb/driverShaderCachePath=...
#    --rtx/shaderDb/driverAppShaderCachePath=...
/opt/nvidia/omniverse/${APP_PACKMAN_PACKAGE_NAME}/kit/kit \
    /opt/nvidia/omniverse/${APP_PACKMAN_PACKAGE_NAME}/apps/generate_shader_cache.kit \
    --/rtx/shaderDb/cachePermutationIndex=0 \
    --/rtx/shaderDb/appShaderCachePath="${APP_SHADER_CACHE_PATH}" \
    --/rtx/shaderDb/driverAppShaderCachePath="${DRIVER_APP_SHADER_CACHE_PATH}" \
    --/renderer/shadercache/driverDiskCache/enabled=true \
    --/app/asyncRendering=false \
    --/rtx/materialDb/syncLoads=true \
    --/omni.kit.plugin/syncUsdLoads=true \
    --/rtx/hydra/materialSyncLoads=true \
    --/rtx/materialflattener/enabled=true \
    --/renderer/multiGpu/autoEnable=false \
    --/renderer/activeGpu=0 \
    --/app/hydraEngine/skipStatusBarIdle=true \
    --/rtx/flow/enabled=true \
    --allow-root \
    --no-audio \
    --no-window \
    $@ || true

# We unfortunately expect a segfault (`|| true`)...
# We will wait a couple of seconds before proceeding.
sleep 5

echo "========================================================================"
echo "Generating Packman packages..."
echo "========================================================================"

RESULTS_LOCATION="/results"
PACKAGE_FORMAT="zip"
mkdir -p "${RESULTS_LOCATION}"

# The following steps call `./packman pack` and `./packman push` explicitly
# instead of the `./packman publish` convenience method in order to:
#    * Explicitly set the archive container format to ZIP (avoiding the
#      requirement of installing 7zip on the Docker container where the shader
#      cache will ultimately be downloaded).
#    * Specify the output folder to "/results", making it possible to retrieve
#      the Packman packages on NGC for inspection.

generate_cache_packman_package () {
    SHADER_CACHE_PACKAGE_NAME=$1
    SHADER_CACHE_VERSION=$2
    SHADER_CACHE_LOCATION=$3

    if [ -d "${SHADER_CACHE_LOCATION}" ]; then
        SHADER_CACHE_PACKMAN_PACKAGE_NAME="${SHADER_CACHE_PACKAGE_NAME}@${SHADER_CACHE_VERSION}"
        echo "Packaging '${SHADER_CACHE_PACKMAN_PACKAGE_NAME}'..."
        /opt/nvidia/packman/packman pack \
            --name "${SHADER_CACHE_PACKMAN_PACKAGE_NAME}" \
            --container "${PACKAGE_FORMAT}" \
            --output-folder "${RESULTS_LOCATION}" \
            "${SHADER_CACHE_LOCATION}"
        echo "Pushing '${SHADER_CACHE_PACKMAN_PACKAGE_NAME}' to remote..."
        /opt/nvidia/packman/packman push \
            --force \
            "${RESULTS_LOCATION}/${SHADER_CACHE_PACKMAN_PACKAGE_NAME}.${PACKAGE_FORMAT}" || true
    else
        echo "Could not find '${SHADER_CACHE_LOCATION}', skipping packaging."
    fi
}

# Generate the kit app driver shader cache packman package...
echo "Generating driver kit application driver shader cache..."
PACKMAN_PACKAGE_NAME="kit-app-driver-shader-cache"
PACKMAN_PACKAGE_VERSION="${KIT_SDK_VERSION}.${GPU_NAME}.${DRIVER_VERSION}"
generate_cache_packman_package "${PACKMAN_PACKAGE_NAME}" "${PACKMAN_PACKAGE_VERSION}" "${DRIVER_APP_SHADER_CACHE_PATH}"
save_package_details_to_dotenv_artifact "${PACKMAN_PACKAGE_NAME}" "${PACKMAN_PACKAGE_VERSION}"
echo "Done generating kit application driver shader cache."

# We will skip this for now, to iterate on at a later date...
# echo "Generating application shader cache..."
# generate_cache_packman_package "${APP_PACKMAN_PACKAGE_NAME}-shader-cache" "${APP_PACKMAN_PACKAGE_VERSION}" "${APP_SHADER_CACHE_PATH}"
# echo "Done generating application shader."

exit 0
