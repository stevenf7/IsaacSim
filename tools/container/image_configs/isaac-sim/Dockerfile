# NVBug SWIPAT for packages: https://nvbugswb.nvidia.com/NvBugs5/SWBug.aspx?bugid=4081238
FROM gitlab-master.nvidia.com:5005/omniverse/containers/apps/ov-base/ov-base-ubuntu-22:2023.10.0

# Switch to root user
USER root

# # Fix permission for shadercache generation
# RUN chown -R ubuntu /opt/nvidia

# Copy package
RUN mkdir -p /isaac-sim
WORKDIR /isaac-sim
COPY _inputs/isaac-sim /isaac-sim/
COPY data/license.sh /isaac-sim/
COPY data/privacy.sh /isaac-sim/
RUN mkdir -p /isaac-sim/oss/source
COPY oss/source/isaac-sim /isaac-sim/oss/source
COPY oss/license/isaac-sim /isaac-sim/oss/license

# Reset apt sources.list
RUN mv /etc/apt/sources.list.canonical /etc/apt/sources.list

# RUN chown -R ubuntu /isaac-sim

# # Switch back to non-root user
# USER ubuntu

# ISIM-968 - libglib2.0-0
RUN apt-get update && \
	apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        && rm -rf /var/lib/apt/lists/*

# WORKDIR /home/ubuntu/
RUN mkdir -p /root/.nvidia-omniverse/config
COPY data/ov_config /root/.nvidia-omniverse/config

# # Switch to root user
# USER root

# Open ports for live streaming
EXPOSE 47995-48012/udp \
       47995-48012/tcp \
       49000-49007/udp \
       49000-49007/tcp \
       49100/tcp \
       8011/tcp \
       8012/tcp \
       8211/tcp \
       8899/tcp \
       8891/tcp

RUN rm /root/.pip/pip.conf

# RUN chown -R ubuntu /home/ubuntu/

ENV NVIDIA_VISIBLE_DEVICES=all NVIDIA_DRIVER_CAPABILITIES=all

# # Switch back to non-root user
# USER ubuntu

ENV OMNI_SERVER http://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/4.0
ENV OMNI_USER admin
ENV OMNI_PASS admin
ENV MIN_DRIVER_VERSION 525.60.11
# OMNI_ENV_PRIVACY_CONSENT
# OMNI_ENV_PRIVACY_USERID

# # Remove duplicate files and make them symlinks - ISIM-1059 - rdfind
# RUN rdfind -makesymlinks true /isaac-sim

WORKDIR /isaac-sim

# Add symlink
RUN ln -s exts/omni.isaac.examples/omni/isaac/examples extension_examples

# Create aliases
RUN echo '#! /bin/sh' > runapp.sh && \
    echo '/isaac-sim/license.sh && /isaac-sim/privacy.sh && /isaac-sim/isaac-sim.sh \\' >> runapp.sh && \
    echo '  --/persistent/isaac/asset_root/default="$OMNI_SERVER" \\' >> runapp.sh && \
    echo '  --merge-config="/isaac-sim/config/open_endpoint.toml" --allow-root "$@" ' >> runapp.sh && \
    chmod u+x runapp.sh

RUN echo '#! /bin/sh' > runheadless.native.sh && \
    echo '/isaac-sim/license.sh && /isaac-sim/privacy.sh && /isaac-sim/isaac-sim.headless.native.sh \\' >> runheadless.native.sh && \
    echo '  --/persistent/isaac/asset_root/default="$OMNI_SERVER" \\' >> runheadless.native.sh && \
    echo '  --merge-config="/isaac-sim/config/open_endpoint.toml" --allow-root "$@" ' >> runheadless.native.sh && \
    chmod u+x runheadless.native.sh

RUN echo '#! /bin/sh' > runheadless.webrtc.sh && \
    echo '/isaac-sim/license.sh && /isaac-sim/privacy.sh && /isaac-sim/isaac-sim.headless.webrtc.sh \\' >> runheadless.webrtc.sh && \
    echo '  --/persistent/isaac/asset_root/default="$OMNI_SERVER" \\' >> runheadless.webrtc.sh && \
    echo '  --merge-config="/isaac-sim/config/open_endpoint.toml" --allow-root "$@" ' >> runheadless.webrtc.sh && \
    chmod u+x runheadless.webrtc.sh

# Update .bashrc
RUN echo 'alias runapp=/isaac-sim/runapp.sh' >> ~/.bashrc && \
    echo 'alias runheadless.native=/isaac-sim/runheadless.native.sh' >> ~/.bashrc && \
    echo 'alias runheadless.webrtc=/isaac-sim/runheadless.webrtc.sh' >> ~/.bashrc

# Default entrypoint to launch headless with streaming
ENTRYPOINT /isaac-sim/runheadless.native.sh
