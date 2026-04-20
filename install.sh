#!/usr/bin/env bash
set -euo pipefail

# --- config ---
REPO="rammohan-b/ClaudeUsageTrackEr"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/bin}"
BINARY_NAME="claude-tracker"
# --------------

die() { echo "ERROR: $*" >&2; exit 1; }

detect_platform() {
    local os arch
    os="$(uname -s)"
    arch="$(uname -m)"

    case "$os" in
        Linux)
            case "$arch" in
                x86_64) echo "linux-x86_64" ;;
                *) die "Unsupported Linux architecture: $arch" ;;
            esac
            ;;
        Darwin)
            case "$arch" in
                arm64)  echo "macos-arm64"  ;;
                x86_64) echo "macos-x86_64" ;;
                *) die "Unsupported macOS architecture: $arch" ;;
            esac
            ;;
        *)
            die "Unsupported OS: $os (Linux, macOS, and WSL2 are supported)"
            ;;
    esac
}

fetch_latest_version() {
    local url="https://api.github.com/repos/${REPO}/releases/latest"
    if command -v curl &>/dev/null; then
        curl -fsSL "$url" | grep '"tag_name"' | sed 's/.*"tag_name": *"\(.*\)".*/\1/'
    elif command -v wget &>/dev/null; then
        wget -qO- "$url" | grep '"tag_name"' | sed 's/.*"tag_name": *"\(.*\)".*/\1/'
    else
        die "curl or wget is required"
    fi
}

download() {
    local url="$1" dest="$2"
    echo "  Downloading from $url"
    if command -v curl &>/dev/null; then
        curl -fsSL --progress-bar -o "$dest" "$url"
    else
        wget -q --show-progress -O "$dest" "$url"
    fi
}

main() {
    echo "==> Installing claude-tracker"

    local platform version asset_url tmp

    platform="$(detect_platform)"
    echo "  Platform: $platform"

    version="$(fetch_latest_version)"
    [ -n "$version" ] || die "Could not determine latest release version"
    echo "  Version:  $version"

    asset_url="https://github.com/${REPO}/releases/download/${version}/${BINARY_NAME}-${platform}"

    tmp="$(mktemp)"
    download "$asset_url" "$tmp"
    chmod +x "$tmp"

    mkdir -p "$INSTALL_DIR"
    mv "$tmp" "${INSTALL_DIR}/${BINARY_NAME}"

    echo "  Installed to ${INSTALL_DIR}/${BINARY_NAME}"

    # Warn if INSTALL_DIR is not on PATH
    if ! echo "$PATH" | tr ':' '\n' | grep -qxF "$INSTALL_DIR"; then
        echo
        echo "  NOTICE: ${INSTALL_DIR} is not on your PATH."
        echo "  Add this to your shell profile (~/.bashrc or ~/.zshrc):"
        echo "    export PATH=\"${INSTALL_DIR}:\$PATH\""
    fi

    echo
    echo "==> Done. Run: claude-tracker serve"
    echo "    Dashboard will be available at http://localhost:5555"
}

main "$@"
