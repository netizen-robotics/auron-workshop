#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/jazzy/setup.bash
export DISPLAY=:99
lab_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

processes=()
web_root=
cleanup() {
    if (("${#processes[@]}")); then
        kill "${processes[@]}" 2>/dev/null || true
        wait "${processes[@]}" 2>/dev/null || true
    fi
    if [[ -n "$web_root" ]]; then rm -rf -- "$web_root"; fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

if [[ -S /tmp/.X11-unix/X99 ]]; then
    printf 'Display :99 is already in use. Stop the earlier simulator first.\n' >&2
    exit 1
fi

web_root="$(mktemp -d)"
ln -s /usr/share/novnc/* "$lab_dir"/web/* "$web_root"

Xvfb "$DISPLAY" -screen 0 500x500x24 -nolisten tcp &
processes+=("$!")
for attempt in {1..50}; do
    [[ -S /tmp/.X11-unix/X99 ]] && break
    sleep 0.1
done
[[ -S /tmp/.X11-unix/X99 ]] || { printf 'The simulator display did not start.\n' >&2; exit 1; }

# noVNC and websockify: https://github.com/novnc/noVNC
# noVNC streams the shared simulator display. ROS messages use the separate bridge below.
x11vnc -display "$DISPLAY" -localhost -rfbport 5900 -nopw -forever -shared -quiet &
processes+=("$!")
websockify --web "$web_root" 6080 127.0.0.1:5900 &
processes+=("$!")
ros2 run turtlesim turtlesim_node &
processes+=("$!")
ros2 launch rosbridge_server rosbridge_websocket_launch.xml address:=0.0.0.0 port:=9090 &
processes+=("$!")

printf 'Open http://localhost:6080/ on your laptop. Rosbridge is on port 9090.\n'
wait -n "${processes[@]}"
