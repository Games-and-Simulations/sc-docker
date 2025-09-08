#!/usr/bin/env bash
set -eux

# Ensure locally built images are loaded into the engine (not just cache)
export DOCKER_BUILDKIT=${DOCKER_BUILDKIT:-0}

# Always run from this script's directory so relative -f paths work
SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$SCRIPT_DIR"

# Engine selection: prefer rootful Docker, then rootless Podman, then rootful Podman.
# Respect SCBW_CONTAINER_RUNTIME as a manual override (socket URL/path or friendly label).
select_engine() {
  local podman_user_sock="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/podman/podman.sock"
  local podman_root_sock="/run/podman/podman.sock"
  local docker_sock="/var/run/docker.sock"

  # Map friendly labels to sockets
  _label_to_url() {
    case "$1" in
      podman-user|SCBW_RUNTIME_PODMAN_USER)
        echo "unix://$podman_user_sock" ;;
      podman-root|SCBW_RUNTIME_PODMAN_ROOT)
        echo "unix://$podman_root_sock" ;;
      docker-root|SCBW_RUNTIME_DOCKER_ROOT)
        echo "unix://$docker_sock" ;;
      *)
        echo "" ;;
    esac
  }

  # Normalize a value to a URL (accept unix://, tcp://, or filesystem path)
  _normalize_url() {
    local v="$1"
    if [[ "$v" =~ ^(unix|tcp):// ]]; then
      echo "$v"
    elif [[ "$v" == /* ]]; then
      echo "unix://$v"
    else
      echo ""
    fi
  }

  # Test connectivity to an engine URL
  _test_engine() {
    DOCKER_HOST="$1" docker info >/dev/null 2>&1
  }

  # 1) Manual override via SCBW_CONTAINER_RUNTIME
  if [[ -n "${SCBW_CONTAINER_RUNTIME:-}" ]]; then
    local candidate="$SCBW_CONTAINER_RUNTIME"
    local url=""
    # If it's a known label or env-var name
    url=$(_label_to_url "$candidate")
    if [[ -z "$url" ]]; then
      # If it's a URL or filesystem path
      url=$(_normalize_url "$candidate")
    fi

    if [[ -n "$url" ]] && _test_engine "$url"; then
      export DOCKER_HOST="$url"
      echo "INFO: Using engine from SCBW_CONTAINER_RUNTIME: $DOCKER_HOST" >&2
      return 0
    else
      echo "ERROR: SCBW_CONTAINER_RUNTIME set to '$SCBW_CONTAINER_RUNTIME' but not reachable." >&2
      echo "       Provide a valid label (docker-root|podman-user|podman-root), socket path, or URL (unix:///...)." >&2
      return 1
    fi
  fi

  # 2) Auto mode: podman-user -> podman-root -> docker-root
  if [[ -S "$podman_user_sock" ]] && _test_engine "unix://$podman_user_sock"; then
    export DOCKER_HOST="unix://$podman_user_sock"
    echo "INFO: Using rootless Podman at $DOCKER_HOST for builds." >&2
    return 0
  fi
  if [[ -S "$podman_root_sock" ]] && _test_engine "unix://$podman_root_sock"; then
    export DOCKER_HOST="unix://$podman_root_sock"
    echo "INFO: Using rootful Podman at $DOCKER_HOST for builds." >&2
    return 0
  fi
  if [[ -S "$docker_sock" ]] && _test_engine "unix://$docker_sock"; then
    export DOCKER_HOST="unix://$docker_sock"
    echo "INFO: Using rootful Docker at $DOCKER_HOST for image builds." >&2
    return 0
  fi

  echo "ERROR: No reachable container engine socket found for builds." >&2
  echo "Checked: $docker_sock, $podman_user_sock, $podman_root_sock" >&2
  return 1
}

select_engine

# Compute an effective UID for images (avoid 0 when running under sudo)
EFFECTIVE_UID=$(id -u)
if [ "$EFFECTIVE_UID" = "0" ] && [ -n "${SUDO_UID:-}" ]; then
  EFFECTIVE_UID="$SUDO_UID"
fi

BUILD_ARGS="--build-arg BOT_UID=${BOT_UID:-2001} --build-arg STARCRAFT_UID=${STARCRAFT_UID:-$EFFECTIVE_UID} --load"

# If building against rootful Docker, pass --network=host to avoid DNS issues during apt
NETWORK_OPT=""
if [ "${DOCKER_HOST:-}" = "unix:///var/run/docker.sock" ]; then
  NETWORK_OPT="--network=host"
  echo "INFO: Using host network for docker build to improve DNS/connectivity." >&2
fi

# Default to classic docker build to ensure local image chaining (FROM starcraft:*) works
BUILD_CMD=(docker build)
# If user explicitly requests buildx, honor it
if [ "${USE_BUILDX:-}" = "1" ] && docker buildx version >/dev/null 2>&1; then
  # Inspect current buildx driver to guide the user
  CURRENT_BUILDX_DRIVER=$(docker buildx inspect 2>/dev/null | awk -F': ' '/^Driver:/ {print $2; exit}')
  echo "INFO: USE_BUILDX=1 detected. buildx driver: ${CURRENT_BUILDX_DRIVER:-unknown}" >&2
  if [ "${CURRENT_BUILDX_DRIVER}" != "docker" ]; then
    cat >&2 <<'EO_BUILDX_WARN'
WARNING: Your buildx builder is not using the 'docker' driver (likely 'docker-container').
         With the container driver, builds run in an isolated environment and local
         images (e.g., 'starcraft:wine') are NOT visible as FROM bases. You may see
         errors like:
           "pull access denied, repository does not exist or may require authorization"

Fix options:
  1) Recommended: use the classic builder (local images are visible):
       unset USE_BUILDX
       ./docker/build_images.sh

  2) Or create/switch to a buildx builder that uses the docker driver:
       docker buildx create --use --driver docker --name scbw-docker
       # then re-run:
       USE_BUILDX=1 ./docker/build_images.sh
EO_BUILDX_WARN
  fi
  BUILD_CMD=(docker buildx build)
else
  # Remove --load from BUILD_ARGS if present to avoid unknown flag errors with classic builder
  BUILD_ARGS="${BUILD_ARGS/ --load/}"
  if [ "${USE_BUILDX:-}" = "1" ]; then
    echo "INFO: USE_BUILDX=1 requested but docker buildx not found; falling back to classic docker build." >&2
  fi
fi

"${BUILD_CMD[@]}" ${NETWORK_OPT} ${BUILD_ARGS} -f dockerfiles/wine.dockerfile  -t starcraft:wine   .
"${BUILD_CMD[@]}" ${NETWORK_OPT} ${BUILD_ARGS} -f dockerfiles/bwapi.dockerfile -t starcraft:bwapi  .
"${BUILD_CMD[@]}" ${NETWORK_OPT} ${BUILD_ARGS} -f dockerfiles/play.dockerfile  -t starcraft:play   .
"${BUILD_CMD[@]}" ${NETWORK_OPT} ${BUILD_ARGS} -f dockerfiles/java.dockerfile  -t starcraft:java   .

pushd ../scbw/local_docker
[ ! -f starcraft.zip ] && curl -SL 'http://files.theabyss.ru/sc/starcraft.zip' -o starcraft.zip
"${BUILD_CMD[@]}" ${NETWORK_OPT} ${BUILD_ARGS} -f game.dockerfile  -t "starcraft:game" .
popd

"${BUILD_CMD[@]}" ${NETWORK_OPT} ${BUILD_ARGS} -f dockerfiles/dbg.dockerfile  -t starcraft:dbg   .
