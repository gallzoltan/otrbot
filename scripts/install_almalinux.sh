#!/usr/bin/env bash
# OTR Bot telepítő AlmaLinux 8/9-re (grafikus felület nélküli szerverre).
#
# Használat a projekt mappájából, normál felhasználóként (a rendszercsomagokhoz sudo kell):
#   bash scripts/install_almalinux.sh
#
# Környezeti változók:
#   GECKODRIVER_VERSION=0.36.0   adott geckodriver verzió (alapból a legújabb)
#   WITH_DEV=1                   a pytest is települjön
#   SKIP_SMOKE_TEST=1            a végén ne indítsa el próbaként a headless Firefoxot
#
# Többször is futtatható: ami már megvan, azt nem rontja el, a meglévő src/.env-et nem írja felül.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GECKODRIVER_FALLBACK="0.36.0"

info() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33mFigyelem: %s\033[0m\n' "$*" >&2; }
die()  { printf '\033[1;31mHiba: %s\033[0m\n' "$*" >&2; exit 1; }

if [[ $EUID -eq 0 ]]; then
  SUDO=""
  warn "rootként fut; az uv és a Python környezet a root felhasználóhoz kerül. Javasolt inkább a futtató felhasználóval indítani."
else
  command -v sudo >/dev/null || die "a sudo nincs telepítve, futtasd rootként a csomagtelepítést"
  SUDO="sudo"
fi

# --- 0. Rendszer ellenőrzése -------------------------------------------------
. /etc/os-release
case "${ID:-} ${ID_LIKE:-}" in
  *almalinux*|*rhel*|*rocky*|*centos*|*fedora*) ;;
  *) warn "ez nem AlmaLinux/RHEL-szerű rendszer (${PRETTY_NAME:-ismeretlen}), a dnf lépések hibázhatnak." ;;
esac
info "Rendszer: ${PRETTY_NAME:-ismeretlen}, projekt: $PROJECT_DIR"
[[ -f "$PROJECT_DIR/pyproject.toml" ]] || die "nem találom a pyproject.toml-t a $PROJECT_DIR mappában"

# --- 1. Rendszercsomagok ----------------------------------------------------
info "Rendszercsomagok telepítése (Firefox ESR, betűkészletek, segédprogramok)"
PACKAGES=(firefox tar gzip dejavu-sans-fonts dejavu-serif-fonts dejavu-sans-mono-fonts tmux sqlite)
# AlmaLinux 9 ships curl-minimal, which conflicts with the full curl package
command -v curl >/dev/null || PACKAGES+=(curl)
$SUDO dnf install -y "${PACKAGES[@]}"
firefox --version || die "a Firefox nem indul"

# --- 2. geckodriver ---------------------------------------------------------
case "$(uname -m)" in
  x86_64)  GD_ARCH="linux64" ;;
  aarch64) GD_ARCH="linux-aarch64" ;;
  *) die "nem támogatott processzor: $(uname -m)" ;;
esac

GD_VERSION="${GECKODRIVER_VERSION:-}"
if [[ -z "$GD_VERSION" ]]; then
  GD_VERSION="$(curl -fsSL https://api.github.com/repos/mozilla/geckodriver/releases/latest 2>/dev/null \
    | sed -n 's/.*"tag_name": *"v\([^"]*\)".*/\1/p' | head -n1 || true)"
  [[ -n "$GD_VERSION" ]] || { warn "nem sikerült lekérdezni a legújabb geckodrivert, a $GECKODRIVER_FALLBACK verzió települ"; GD_VERSION="$GECKODRIVER_FALLBACK"; }
fi

if command -v geckodriver >/dev/null && geckodriver --version | head -n1 | grep -q " $GD_VERSION"; then
  info "geckodriver $GD_VERSION már telepítve"
else
  info "geckodriver $GD_VERSION telepítése a /usr/local/bin mappába"
  TMP_DIR="$(mktemp -d)"
  trap 'rm -rf "$TMP_DIR"' EXIT
  curl -fL --retry 3 -o "$TMP_DIR/gd.tar.gz" \
    "https://github.com/mozilla/geckodriver/releases/download/v$GD_VERSION/geckodriver-v$GD_VERSION-$GD_ARCH.tar.gz"
  tar -xzf "$TMP_DIR/gd.tar.gz" -C "$TMP_DIR"
  $SUDO install -m 0755 "$TMP_DIR/geckodriver" /usr/local/bin/geckodriver
fi
/usr/local/bin/geckodriver --version | head -n1

# --- 3. uv és Python környezet ---------------------------------------------
export PATH="$HOME/.local/bin:$PATH"
if command -v uv >/dev/null; then
  info "uv már telepítve: $(uv --version)"
else
  info "uv telepítése a $HOME/.local/bin mappába"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  command -v uv >/dev/null || die "az uv telepítése nem sikerült"
fi

info "Python környezet és függőségek (uv sync; ha kell, letölti a Python 3.12-t)"
cd "$PROJECT_DIR"
if [[ "${WITH_DEV:-0}" == "1" ]]; then
  uv sync
else
  uv sync --no-dev
fi
uv run python --version

# --- 4. Beállítások ---------------------------------------------------------
ENV_FILE="$PROJECT_DIR/src/.env"
if [[ -f "$ENV_FILE" ]]; then
  info "A src/.env már létezik, nem írom felül"
else
  info "src/.env létrehozása a mintából (SYSTEM=linux, ENV=dev)"
  sed -e "s/^SYSTEM=.*/SYSTEM=linux/" -e "s/^ENV=.*/ENV=dev/" \
    "$PROJECT_DIR/src/.env.example" > "$ENV_FILE"
fi
chmod 600 "$ENV_FILE"
mkdir -p "$PROJECT_DIR/logs" "$PROJECT_DIR/data"

# --- 5. Próba: headless Firefox ---------------------------------------------
if [[ "${SKIP_SMOKE_TEST:-0}" != "1" ]]; then
  info "Próba: headless Firefox indítása"
  timeout 120 uv run python - <<'PY'
from otrbot.services.webdriver_service import WebDriver
w = WebDriver(headless=True)
try:
    w.driver.get("about:blank")
    print("Firefox OK, ablak:", w.driver.get_window_size())
finally:
    w.close()
PY
fi

cat <<EOF

Kész. Következő lépések:
  1. Töltsd ki a belépési adatokat:  nano $ENV_FILE
     (ENV=dev az EDU, ENV=prod az éles rendszer)
  2. Másold a betöltő Excelt a data/ mappába.
  3. Próbafutás tmux alatt:
       tmux new -s otr
       cd $PROJECT_DIR
       uv run python src/main.py -s "Benyújtás" -f data/<fajl>.xlsx -sp KTM -b 1 -e 5 --headless
     (kilépés a tmux-ból: Ctrl+B, majd D; visszatérés: tmux attach -t otr)
  4. Eredmény: sqlite3 data/<fajl>.journal.sqlite "select * from eredmeny"
EOF
