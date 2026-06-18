#!/usr/bin/env bash
set -euo pipefail

SPEC="$(dirname "$0")/beeper.spec"
SOURCES_DIR="$HOME/rpmbuild/SOURCES"
MOCK_CONFIG="fedora-44-x86_64"

usage() {
  echo "Usage: $0 [--build] [--rebuild]"
  echo "  --build    Also build the RPM in mock after updating"
  echo "  --rebuild  Skip version check and rebuild the current spec version"
  exit 1
}

DO_BUILD=0
DO_REBUILD=0
for arg in "$@"; do
  case "$arg" in
    --build)   DO_BUILD=1 ;;
    --rebuild) DO_REBUILD=1 ;;
    *) usage ;;
  esac
done

# Detect upstream version via redirect URL
REDIRECT=$(curl -sI 'https://api.beeper.com/desktop/download/linux/x64/stable/com.automattic.beeper.desktop' \
  | grep -i '^location:' | tr -d '\r' | awk '{print $2}')
NEW_VERSION=$(basename "$REDIRECT" | grep -oP '\d+\.\d+\.\d+')
CURRENT_VERSION=$(grep -oP '(?<=%global appimage_version )\S+' "$SPEC")

echo "Upstream: $NEW_VERSION"
echo "Current:  $CURRENT_VERSION"

if [[ "$NEW_VERSION" == "$CURRENT_VERSION" && "$DO_REBUILD" -eq 0 ]]; then
  echo "Already up to date. Use --rebuild to force a rebuild."
  exit 0
fi

if [[ "$NEW_VERSION" != "$CURRENT_VERSION" ]]; then
  echo "Updating spec to $NEW_VERSION..."
  sed -i "s/^%global appimage_version.*/%global appimage_version $NEW_VERSION/" "$SPEC"

  # Prepend changelog entry (LC_TIME=C forces English day/month abbreviations)
  DATE=$(LC_TIME=C date '+%a %b %d %Y')
  sed -i "/^%changelog/a * $DATE Auto Update <support@midnightthoughts.space> - $NEW_VERSION-1\n- Update to $NEW_VERSION\n" "$SPEC"
fi

# Sync sources
cp "$(dirname "$0")/beeper-wrapper.sh" "$(dirname "$0")/beeper.desktop" "$SOURCES_DIR/"
cp "$SPEC" "$HOME/rpmbuild/SPECS/"

# Download AppImage if not already cached
echo "Downloading Beeper ${NEW_VERSION} AppImage (if not cached)..."
spectool -g -R "$HOME/rpmbuild/SPECS/beeper.spec"

# Build SRPM
echo "Building source RPM..."
SRPM=$(rpmbuild -bs "$HOME/rpmbuild/SPECS/beeper.spec" | grep -oP '(?<=Erstellt: |Wrote: )\S+')
echo "SRPM: $SRPM"

if [[ "$DO_BUILD" -eq 1 ]]; then
  echo "Building RPM in mock ($MOCK_CONFIG)..."
  sudo mock -r "$MOCK_CONFIG" "$SRPM"
  echo "RPM ready in /var/lib/mock/$MOCK_CONFIG/result/"
fi

echo "Done."
