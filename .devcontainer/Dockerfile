FROM ros:jazzy-ros-base

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git novnc python3-venv \
        ros-jazzy-navigation2 ros-jazzy-nav2-bringup ros-jazzy-nav2-simple-commander \
        ros-jazzy-rosbridge-suite ros-jazzy-slam-toolbox ros-jazzy-turtlesim \
        websockify x11vnc xvfb \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv --system-site-packages /opt/auron-venv \
    && if ! id ubuntu >/dev/null 2>&1; then useradd -m -u 1000 -s /bin/bash ubuntu; fi \
    && printf '\nsource /opt/ros/jazzy/setup.bash\n' >> /etc/bash.bashrc

ENV PATH="/opt/auron-venv/bin:${PATH}" \
    ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST \
    PYTHONDONTWRITEBYTECODE=1
