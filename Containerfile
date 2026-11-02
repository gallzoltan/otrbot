# OTR Bot container image (AlmaLinux 9, Firefox ESR, geckodriver, Python 3.12 via uv).
# Build and run with scripts/otrbot-podman.sh; see docs there.
FROM docker.io/library/almalinux:9

ARG GECKODRIVER_VERSION=0.37.1

# Firefox ESR + fonts for the failure screenshots. curl-minimal is already in the base image.
RUN dnf install -y firefox tar gzip dejavu-sans-fonts dejavu-serif-fonts dejavu-sans-mono-fonts \
 && dnf clean all \
 && rm -rf /var/cache/dnf

RUN case "$(uname -m)" in \
      x86_64)  arch=linux64 ;; \
      aarch64) arch=linux-aarch64 ;; \
      *) echo "unsupported arch $(uname -m)"; exit 1 ;; \
    esac \
 && curl -fsSL --retry 3 \
      "https://github.com/mozilla/geckodriver/releases/download/v${GECKODRIVER_VERSION}/geckodriver-v${GECKODRIVER_VERSION}-${arch}.tar.gz" \
    | tar -xz -C /usr/local/bin \
 && chmod 0755 /usr/local/bin/geckodriver \
 && geckodriver --version | head -n1

COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /usr/local/bin/uv

ENV UV_PYTHON_INSTALL_DIR=/opt/python \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1

WORKDIR /app

# Dependencies first, so a code change does not reinstall them
COPY pyproject.toml uv.lock README.md .python-version ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
RUN uv sync --frozen --no-dev \
 && rm -f src/.env

# load_dotenv() does not override variables that are already set, so SYSTEM stays linux
ENV PATH=/app/.venv/bin:$PATH \
    SYSTEM=linux \
    PYTHONUNBUFFERED=1 \
    TZ=Europe/Budapest

# Excel files and journals (data/) and logs (logs/) are mounted from the host
VOLUME ["/app/data", "/app/logs"]

ENTRYPOINT ["python", "src/main.py"]
