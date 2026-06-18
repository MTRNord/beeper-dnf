# beeper-rpm

Automatically packages the [Beeper](https://www.beeper.com) AppImage as an RPM and publishes it to Fedora COPR.

Beeper is proprietary software. This repository does **not** redistribute the Beeper binary — the spec file downloads it from Beeper's official CDN at build time.

---

## Install from COPR

```sh
dnf copr enable mtrnord/beeper
dnf install beeper
```

---

## Local build

### Prerequisites

```sh
# Fedora / RHEL
sudo dnf install rpm-build rpmdevtools squashfs-tools
```

### One-time setup

```sh
rpmdev-setuptree   # creates ~/rpmbuild/{SOURCES,SPECS,BUILD,...}
```

### Download the AppImage source

The spec's `Source0` is a remote URL, so you need to fetch it manually before building locally:

```sh
VERSION=$(grep -oP '(?<=%global appimage_version )\S+' beeper.spec)
curl -L \
  "https://beeper-desktop.download.beeper.com/builds/Beeper-${VERSION}-x86_64.AppImage" \
  -o ~/rpmbuild/SOURCES/Beeper-${VERSION}-x86_64.AppImage
```

Copy the other sources too:

```sh
cp beeper-wrapper.sh beeper.desktop ~/rpmbuild/SOURCES/
cp beeper.spec ~/rpmbuild/SPECS/
```

### Build the RPM

```sh
# Build a source RPM only (fast, validates the spec)
rpmbuild -bs ~/rpmbuild/SPECS/beeper.spec

# Build the full binary RPM
rpmbuild -bb ~/rpmbuild/SPECS/beeper.spec
```

The resulting RPM lands in `~/rpmbuild/RPMS/x86_64/`.

### Build in a clean chroot with mock (recommended)

`mock` replicates what COPR does and catches missing `BuildRequires`:

```sh
sudo dnf install mock
sudo usermod -aG mock $USER   # log out and back in after this

# Build the source RPM first
rpmbuild -bs ~/rpmbuild/SPECS/beeper.spec

# Then build in a Fedora 44 chroot
mock -r fedora-44-x86_64 ~/rpmbuild/SRPMS/beeper-*.src.rpm
```

The RPM ends up in `/var/lib/mock/fedora-44-x86_64/result/`.

### Install and test

```sh
sudo rpm -ivh ~/rpmbuild/RPMS/x86_64/beeper-*.rpm
# or with mock output:
sudo rpm -ivh /var/lib/mock/fedora-42-x86_64/result/beeper-*.rpm

beeper
```

---

## How auto-updates work

A GitHub Actions workflow (`.github/workflows/check-update.yml`) runs daily:

1. Follows the Beeper download redirect to detect the current version.
2. If the version differs from what's in `beeper.spec`, it updates the `%global appimage_version` line and commits.
3. COPR detects the new commit and triggers a rebuild automatically.

---

## Troubleshooting

**AppImage fails to self-extract in mock chroot**

If `%{SOURCE0} --appimage-extract` fails (e.g., due to missing kernel namespace support), extract the SquashFS manually:

```sh
# Find the SquashFS offset inside the AppImage ELF
OFFSET=$(cat -v Beeper-*.AppImage | grep -boa 'hsqs' | head -1 | cut -d: -f1)
unsquashfs -o "$OFFSET" -d squashfs-root Beeper-*.AppImage
```

Replace the `%prep` block in the spec with the commands above.

**Beeper crashes on launch**

The wrapper calls `AppRun` which auto-detects sandbox support via `unshare -Ur`. If it still crashes, force-enable the SUID sandbox instead:

```sh
sudo chmod 4755 /opt/beeper/chrome-sandbox
```
