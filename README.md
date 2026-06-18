# beeper-rpm

Automatically packages the [Beeper](https://www.beeper.com) AppImage as an RPM and publishes it to a self-hosted DNF repository at `packages.mtrnord.blog`.

Beeper is proprietary software. This repository does **not** redistribute the Beeper binary — the spec file downloads it from Beeper's official CDN at build time.

---

## Install

```sh
sudo curl -o /etc/yum.repos.d/mtrnord.repo https://packages.mtrnord.blog/mtrnord.repo
sudo dnf install beeper
```

When prompted to import the GPG key, verify the fingerprint matches before accepting:

```
Fingerprint: FB7F 7B3E 1074 AA60 3F19  9BCE 175E 4D3C 6385 91B3
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

`mock` replicates what CI does and catches missing `BuildRequires`:

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
sudo rpm -ivh /var/lib/mock/fedora-44-x86_64/result/beeper-*.rpm

beeper
```

---

## How auto-updates work

Two GitHub Actions workflows handle updates end-to-end:

1. **`check-update.yml`** runs daily at 06:00 UTC:
   - Follows the Beeper download redirect to detect the current version.
   - If the version differs from `beeper.spec`, it updates `%global appimage_version` and commits.

2. **`publish.yml`** triggers on every push to `main` (i.e. after each version bump commit):
   - Builds the RPM inside a Fedora container.
   - GPG-signs the package.
   - Uploads the RPM and updated `repo.gpg` to `packages.mtrnord.blog`.
   - Runs `createrepo_c --update` to refresh the repo metadata.

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
