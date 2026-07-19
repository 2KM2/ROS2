#!/usr/bin/env bash
set -euo pipefail

readonly TARGET_UBUNTU_CODENAME="noble"
readonly TARGET_ROS_DISTRO="jazzy"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
INSTALL_ROS=true
BUILD_STAGE=true

usage() {
  cat <<'EOF'
Usage: ./scripts/install_dependencies.sh [options]

Options:
  --skip-ros    Do not configure the ROS repository or install ROS Jazzy.
  --skip-stage  Do not build and install the bundled Stage simulator.
  -h, --help    Show this help message.
EOF
}

for argument in "$@"; do
  case "${argument}" in
    --skip-ros) INSTALL_ROS=false ;;
    --skip-stage) BUILD_STAGE=false ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: ${argument}" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ ! -r /etc/os-release ]]; then
  echo "Cannot detect the operating system." >&2
  exit 1
fi

# shellcheck disable=SC1091
source /etc/os-release
if [[ "${ID:-}" != "ubuntu" || "${VERSION_CODENAME:-}" != "${TARGET_UBUNTU_CODENAME}" ]]; then
  echo "This project requires Ubuntu 24.04 (${TARGET_UBUNTU_CODENAME})." >&2
  echo "Detected: ${PRETTY_NAME:-unknown}" >&2
  exit 1
fi

if (( EUID == 0 )); then
  SUDO=()
else
  command -v sudo >/dev/null || {
    echo "sudo is required when this script is not run as root." >&2
    exit 1
  }
  SUDO=(sudo)
fi

apt_install() {
  "${SUDO[@]}" env DEBIAN_FRONTEND=noninteractive apt-get install -y "$@"
}

TEMP_DIR="$(mktemp -d)"
trap 'rm -rf -- "${TEMP_DIR}"' EXIT

echo "[1/6] Installing base development tools..."
"${SUDO[@]}" apt-get update
apt_install \
  ca-certificates curl gnupg lsb-release locales software-properties-common \
  build-essential cmake git pkg-config

"${SUDO[@]}" locale-gen en_US en_US.UTF-8
"${SUDO[@]}" update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8

if [[ "${INSTALL_ROS}" == true ]]; then
  echo "[2/6] Configuring the ROS 2 apt repository..."
  "${SUDO[@]}" add-apt-repository -y universe

  curl -fsSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o "${TEMP_DIR}/ros.key"
  gpg --dearmor --yes --output "${TEMP_DIR}/ros-archive-keyring.gpg" \
    "${TEMP_DIR}/ros.key"
  "${SUDO[@]}" install -m 0644 "${TEMP_DIR}/ros-archive-keyring.gpg" \
    /usr/share/keyrings/ros-archive-keyring.gpg

  ARCHITECTURE="$(dpkg --print-architecture)"
  REPOSITORY_LINE="deb [arch=${ARCHITECTURE} signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu ${TARGET_UBUNTU_CODENAME} main"
  printf '%s\n' "${REPOSITORY_LINE}" | "${SUDO[@]}" tee \
    /etc/apt/sources.list.d/ros2.list >/dev/null

  "${SUDO[@]}" apt-get update
  echo "[3/6] Installing ROS 2 Jazzy..."
  apt_install \
    ros-jazzy-desktop \
    ros-dev-tools
else
  echo "[2/6] Skipping ROS repository configuration."
  echo "[3/6] Skipping ROS Jazzy installation."
fi

if [[ ! -r "/opt/ros/${TARGET_ROS_DISTRO}/setup.bash" ]]; then
  echo "ROS 2 ${TARGET_ROS_DISTRO} was not found in /opt/ros." >&2
  echo "Run this script without --skip-ros first." >&2
  exit 1
fi

echo "Installing workspace ROS tools and runtime dependencies..."
"${SUDO[@]}" apt-get update
apt_install \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-vcstool \
  ros-jazzy-ros-gz \
  ros-jazzy-slam-toolbox \
  ros-jazzy-cartographer-ros \
  ros-jazzy-navigation2 \
  ros-jazzy-nav2-bringup \
  ros-jazzy-teleop-twist-keyboard \
  ros-jazzy-tf2-tools

echo "[4/6] Installing Stage build dependencies..."
apt_install \
  libfltk1.3-dev libgl1-mesa-dev libglu1-mesa-dev \
  libjpeg-dev libpng-dev libltdl-dev

if [[ "${BUILD_STAGE}" == true ]]; then
  STAGE_SOURCE="${WORKSPACE_DIR}/src/sim_stage/Stage"
  if [[ ! -f "${STAGE_SOURCE}/CMakeLists.txt" ]]; then
    echo "Bundled Stage source was not found: ${STAGE_SOURCE}" >&2
    exit 1
  fi

  echo "[5/6] Building and installing the bundled Stage simulator..."
  STAGE_BUILD_DIR="${TEMP_DIR}/stage-build"
  cmake -S "${STAGE_SOURCE}" -B "${STAGE_BUILD_DIR}" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/usr/local
  cmake --build "${STAGE_BUILD_DIR}" --parallel "$(nproc)"
  "${SUDO[@]}" cmake --install "${STAGE_BUILD_DIR}"
  "${SUDO[@]}" ldconfig
else
  echo "[5/6] Skipping the bundled Stage build."
fi

echo "[6/6] Resolving dependencies declared by package.xml files..."
# shellcheck disable=SC1090
source "/opt/ros/${TARGET_ROS_DISTRO}/setup.bash"

if [[ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]]; then
  "${SUDO[@]}" rosdep init
fi
rosdep update

# Stage is provided by src/sim_stage/Stage and installed above, so rosdep must
# not try to resolve the legacy, case-sensitive package.xml key through apt.
rosdep install \
  --from-paths "${WORKSPACE_DIR}/src" \
  --ignore-src \
  --rosdistro "${TARGET_ROS_DISTRO}" \
  --skip-keys Stage \
  -r -y

echo
echo "Dependency installation completed."
echo "Build the workspace with:"
echo "  cd ${WORKSPACE_DIR}"
echo "  source /opt/ros/${TARGET_ROS_DISTRO}/setup.bash"
echo "  colcon build --symlink-install"
echo "  source install/setup.bash"
