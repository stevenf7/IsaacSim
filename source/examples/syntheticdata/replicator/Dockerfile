FROM nvcr.io/omniverse/isaac-cesspool/isaac-sim:latest-develop

# Install some software
RUN dpkg --add-architecture i386 && \
        apt-get update && apt-get install -y --no-install-recommends \
        apt-utils \
        vim \
        netcat

# Copy files
COPY . /isaac-sim/python_samples/syntheticdata/replicator
COPY docker/run.sh /isaac-sim
COPY docker/loop_kill_replicator.sh /isaac-sim
COPY docker/loop_run_replicator.sh /isaac-sim

# Install Python requirements
RUN ./python.sh -m pip install pyyaml
RUN ./python.sh -m pip install opencv-python
