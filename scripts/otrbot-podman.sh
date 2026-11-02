#!/usr/bin/env bash
# OTR Bot futtatása podman konténerben (AlmaLinux szerverre, grafikus felület nélkül).
#
# Előfeltétel a gazdagépen: sudo dnf install -y podman
#
# Használat a projekt mappájából, normál felhasználóként (rootless podman):
#   scripts/otrbot-podman.sh build                 # image építése (kódváltozás után újra)
#   scripts/otrbot-podman.sh test                  # próba: headless Firefox a konténerben
#   scripts/otrbot-podman.sh run -s "Benyújtás" -f data/minta.xlsx -sp KTM -b 1 -e 5
#   scripts/otrbot-podman.sh shell                 # bash a konténerben, hibakereséshez
#
# A run a main.py kapcsolóit kapja, a --headless-t magától hozzáteszi.
# Az Excel útvonala a konténeren belüli: data/<fájl>.xlsx (a gazdagépen: $OTRBOT_DATA_DIR/<fájl>.xlsx).
#
# Csatolások a gazdagépről:
#   $OTRBOT_DATA_DIR (alap: <projekt>/data) -> /app/data   Excel + napló (.journal.sqlite)
#   $OTRBOT_LOGS_DIR (alap: <projekt>/logs) -> /app/logs   logok, logs/fail képernyőképek
#   $OTRBOT_ENV_FILE (alap: <projekt>/src/.env) -> /app/src/.env (csak olvasható)
# A belépési adatok nem kerülnek bele az image-be.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${OTRBOT_IMAGE:-localhost/otrbot:latest}"
DATA_DIR="${OTRBOT_DATA_DIR:-$PROJECT_DIR/data}"
LOGS_DIR="${OTRBOT_LOGS_DIR:-$PROJECT_DIR/logs}"
ENV_FILE="${OTRBOT_ENV_FILE:-$PROJECT_DIR/src/.env}"

die() { printf 'Hiba: %s\n' "$*" >&2; exit 1; }

command -v podman >/dev/null || die "a podman nincs telepítve (sudo dnf install -y podman)"

usage() {
  sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

# Common podman run options: rootless podman maps container root to the calling user,
# so files written to data/ and logs/ belong to that user on the host.
# :Z relabels the mounts for SELinux (enforcing on AlmaLinux by default).
run_opts() {
  [[ -f "$ENV_FILE" ]] || die "nincs $ENV_FILE (másold a src/.env.example-ből és töltsd ki)"
  mkdir -p "$DATA_DIR" "$LOGS_DIR"
  RUN_OPTS=(--rm --init --shm-size=2g
    -v "$DATA_DIR:/app/data:Z"
    -v "$LOGS_DIR:/app/logs:Z"
    -v "$ENV_FILE:/app/src/.env:ro,Z")
  # Interactive terminal only when there is one (not under nohup/cron)
  if [[ -t 0 && -t 1 ]]; then RUN_OPTS+=(-it); fi
}

image_exists() {
  podman image exists "$IMAGE" || die "nincs $IMAGE image, előbb: $0 build"
}

cmd="${1:-}"
[[ $# -gt 0 ]] && shift

case "$cmd" in
  build)
    exec podman build -t "$IMAGE" -f "$PROJECT_DIR/Containerfile" "$@" "$PROJECT_DIR"
    ;;
  run)
    [[ $# -gt 0 ]] || usage 1
    image_exists
    run_opts
    exec podman run "${RUN_OPTS[@]}" "$IMAGE" "$@" --headless
    ;;
  test)
    image_exists
    exec podman run --rm --init --shm-size=2g --entrypoint python "$IMAGE" -c '
from otrbot.services.webdriver_service import WebDriver
w = WebDriver(headless=True)
try:
    w.driver.get("about:blank")
    print("Firefox OK, ablak:", w.driver.get_window_size())
finally:
    w.close()'
    ;;
  shell)
    image_exists
    run_opts
    exec podman run "${RUN_OPTS[@]}" -it --entrypoint bash "$IMAGE"
    ;;
  -h|--help|help|"")
    usage 0
    ;;
  *)
    printf 'Ismeretlen parancs: %s\n\n' "$cmd" >&2
    usage 1
    ;;
esac
