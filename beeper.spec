%global appimage_version 4.2.985

Name:           beeper
Version:        %{appimage_version}
Release:        1%{?dist}
Summary:        All your chats in one app
License:        Proprietary
URL:            https://www.beeper.com
Source0:        https://beeper-desktop.download.beeper.com/builds/Beeper-%{version}-x86_64.AppImage
Source1:        beeper-wrapper.sh
Source2:        beeper.desktop

BuildRequires:  squashfs-tools
ExclusiveArch:  x86_64
# Disable automatic dependency generation — Electron bundles its own libs
AutoReqProv:    no

# Electron-specific libs (libEGL, libffmpeg, libGLESv2, etc.) are bundled in /opt/beeper/
# and found via $ORIGIN rpath — no need to list them here.
# The AppImage's usr/lib/ (libnotify, libXss, libappindicator3, …) is dropped at install
# time; the system packages below provide those instead.
Requires:       gtk3
Requires:       nss
Requires:       at-spi2-atk
Requires:       libdrm
Requires:       mesa-libgbm
Requires:       alsa-lib
Requires:       cups-libs

%description
Beeper is a universal messaging app that brings together iMessage, WhatsApp,
Telegram, Signal, and many other chat networks into a single inbox.

This package is built from the official Beeper AppImage and is not affiliated
with or endorsed by Automattic, Inc.

%prep
chmod +x %{SOURCE0}
%{SOURCE0} --appimage-extract

%build
# Binary-only package, nothing to build.

%install
install -dm 755 %{buildroot}/opt/beeper
cp -a squashfs-root/. %{buildroot}/opt/beeper/
# Drop the entire AppImage usr/ tree — libs come from system Requires,
# icons are installed to /usr/share/icons/ separately below.
rm -rf %{buildroot}/opt/beeper/usr
# Disable the built-in auto-updater — updates are handled by COPR/dnf instead.
echo 'provider: none' > %{buildroot}/opt/beeper/resources/app-update.yml

install -Dm 755 %{SOURCE1} %{buildroot}%{_bindir}/beeper
install -Dm 644 %{SOURCE2} %{buildroot}%{_datadir}/applications/beeper.desktop

# Install icons extracted from the AppImage
find squashfs-root/usr/share/icons -type f \( -name '*.png' -o -name '*.svg' \) | while read -r icon; do
  dest="${icon#squashfs-root}"
  install -Dm 644 "$icon" "%{buildroot}${dest}"
done

%post
/usr/bin/update-desktop-database &>/dev/null || :
/usr/bin/gtk-update-icon-cache /usr/share/icons/hicolor &>/dev/null || :

%postun
/usr/bin/update-desktop-database &>/dev/null || :
/usr/bin/gtk-update-icon-cache /usr/share/icons/hicolor &>/dev/null || :

%files
/opt/beeper/
%{_bindir}/beeper
%{_datadir}/applications/beeper.desktop
%{_datadir}/icons/

%changelog
* Thu Jul 16 2026 Auto Update <support@midnightthoughts.space> - 4.2.985-1
- Update to 4.2.985

* Thu Jul 09 2026 Auto Update <support@midnightthoughts.space> - 4.2.972-1
- Update to 4.2.972

* Fri Jul 03 2026 Auto Update <support@midnightthoughts.space> - 4.2.957-1
- Update to 4.2.957

* Fri Jun 26 2026 Auto Update <support@midnightthoughts.space> - 4.2.948-1
- Update to 4.2.948

* Sat Jun 20 2026 Auto Update <support@midnightthoughts.space> - 4.2.945-1
- Update to 4.2.945

* Wed Jun 18 2025 Auto Update <support@midnightthoughts.space> - 4.2.936-1
- Update to 4.2.936

* Sat Jun 07 2025 Auto Update <support@midnightthoughts.space> - 4.2.892-1
- Initial package
