#!/usr/bin/env bash
set -euo pipefail
BRIDGE_IMAGE="${BRIDGE_IMAGE:-ros:humble-ros-base}"
CONTAINER_NAME="${CONTAINER_NAME:-ros2_carriage}"
HOST_WS_ROOT="${HOST_WS_ROOT:-$HOME/carriage_ros2_project/ros2_ws}"
BRIDGE_PORT="${BRIDGE_PORT:-/dev/ttyAMA0}"
BRIDGE_BAUD="${BRIDGE_BAUD:-115200}"
ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-42}"
CYCLONEDDS_URI="${CYCLONEDDS_URI:-file://$HOST_WS_ROOT/config/cyclonedds_rpi.xml}"
echo "=== Запуск carriage_bridge в Docker ==="
echo "Образ         : ${BRIDGE_IMAGE}"
echo "Контейнер     : ${CONTAINER_NAME}"
echo "Workspace     : ${HOST_WS_ROOT}"
echo "UART порт     : ${BRIDGE_PORT}"
echo "UART скорость : ${BRIDGE_BAUD}"
echo "ROS_DOMAIN_ID : ${ROS_DOMAIN_ID}"
echo "CYCLONEDDS_URI: ${CYCLONEDDS_URI}"
echo "======================================="
if [ ! -d "${HOST_WS_ROOT}" ]; then
  echo "ERROR: Не найден workspace по пути ${HOST_WS_ROOT}" >&2
  exit 1
fi
exec docker run -it --rm \
  --name "${CONTAINER_NAME}" \
  --net=host \
  --device "${BRIDGE_PORT}" \
  -e ROS_DOMAIN_ID="${ROS_DOMAIN_ID}" \
  -e CYCLONEDDS_URI="${CYCLONEDDS_URI}" \
  -v "${HOST_WS_ROOT}":/ros2_ws \
  "${BRIDGE_IMAGE}" \
  bash -lc " \
    set +u; \
    source /opt/ros/humble/setup.bash; \
    source /ros2_ws/install/setup.bash; \
    ros2 launch carriage_bridge carriage_launch.py \
      port:=${BRIDGE_PORT} \
      baudrate:=${BRIDGE_BAUD} \
  "
