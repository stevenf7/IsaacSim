FROM gitlab-master.nvidia.com:5005/omniverse/containers/apps/ov-packman/ov-packman:latest as kit-build

### ==== Generated section (begin) ====

# Main package
RUN /opt/nvidia/packman/packman install kit-sdk-launcher 106.0+release.15014.11e40b49.tc.linux-x86_64.release

### ==== Generated section (end) ====

FROM gitlab-master.nvidia.com:5005/omniverse/containers/apps/ov-base/ov-base-ubuntu-22:latest

### ==== Generated section (begin) ====

# Main package
COPY --from=kit-build --chown=ubuntu:ubuntu /var/tmp/packman/chk/kit-sdk-launcher/106.0+release.15014.11e40b49.tc.linux-x86_64.release/ /opt/nvidia/omniverse/kit-sdk-launcher

### ==== Generated section (end) ====

COPY data/startup.sh /startup.sh
COPY data/startup_nogpu.sh /startup_nogpu.sh

# Open ports for live streaming
EXPOSE 47995-48012/udp \
       47995-48012/tcp \
       49000-49007/udp \
       49000-49007/tcp \
       8011/tcp \
       8111/tcp \
       49100/tcp

ENTRYPOINT ["/startup.sh"]