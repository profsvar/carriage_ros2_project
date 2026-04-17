#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$SCRIPT_DIR}"
DOCKERFILE_PATH="${DOCKERFILE_PATH:-$PROJECT_ROOT/Dockerfile.carriage_bridge}"
BRIDGE_IMAGE="${BRIDGE_IMAGE:-carriage-bridge:humble-rpi}"
CONTAINER_NAME="${CONTAINER_NAME:-ros2_carriage}"
HOST_WS_ROOT="${HOST_WS_ROOT:-$HOME/carriage_ros2_project/ros2_ws}"
BRIDGE_PORT="${BRIDGE_PORT:-}"
BRIDGE_BAUD="${BRIDGE_BAUD:-115200}"
ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-42}"
CYCLONEDDS_URI="${CYCLONEDDS_URI:-file://$HOST_WS_ROOT/config/cyclonedds_rpi.xml}"

if [ -z "${BRIDGE_PORT}" ]; then
  for candidate in /dev/serial0 /dev/ttyAMA0 /dev/ttyS0; do
    if [ -e "${candidate}" ]; then
      BRIDGE_PORT="${candidate}"
      break
    fi
  done
fi

if [ -z "${BRIDGE_PORT}" ] || [ ! -e "${BRIDGE_PORT}" ]; then
  echo "ERROR: UART-порт не найден. Укажите BRIDGE_PORT явно." >&2
  echo "Подсказка: ls -l /dev/serial* /dev/ttyAMA* /dev/ttyS* 2>/dev/null" >&2
  exit 1
fi

if [ ! -f "${DOCKERFILE_PATH}" ]; then
  echo "ERROR: Не найден Dockerfile по пути ${DOCKERFILE_PATH}" >&2
  exit 1
fi

if ! docker image inspect "${BRIDGE_IMAGE}" >/dev/null 2>&1; then
  echo "Docker-образ ${BRIDGE_IMAGE} не найден локально. Выполняю одноразовую сборку..."
  docker build -t "${BRIDGE_IMAGE}" -f "${DOCKERFILE_PATH}" "${PROJECT_ROOT}"
fi

if [ ! -d "${HOST_WS_ROOT}" ]; then
  echo "ERROR: Не найден workspace по пути ${HOST_WS_ROOT}" >&2
  exit 1
fi

if [ ! -f "${HOST_WS_ROOT}/install/setup.bash" ]; then
  echo "Не найден ${HOST_WS_ROOT}/install/setup.bash. Выполняю одноразовую сборку ROS2 workspace..."
  docker run -it --rm \
    --net=host \
    -v "${HOST_WS_ROOT}":/ros2_ws \
    "${BRIDGE_IMAGE}" \
    bash -lc " \
      set -e; \
      source /opt/ros/humble/setup.bash; \
      cd /ros2_ws; \
      colcon build --base-paths src \
    "
fi

echo "=== Запуск carriage_bridge в Docker ==="
echo "Образ         : ${BRIDGE_IMAGE}"
echo "Контейнер     : ${CONTAINER_NAME}"
echo "Workspace     : ${HOST_WS_ROOT}"
echo "UART порт     : ${BRIDGE_PORT}"
echo "UART скорость : ${BRIDGE_BAUD}"
echo "ROS_DOMAIN_ID : ${ROS_DOMAIN_ID}"
echo "CYCLONEDDS_URI: ${CYCLONEDDS_URI}"
echo "======================================="
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
