#!/bin/bash
# chrome-sandbox won't have the SUID bit set when installed via RPM, so --no-sandbox is required.
# --ozone-platform-hint=auto enables native Wayland under a Wayland compositor.
exec /opt/beeper/beepertexts --no-sandbox --ozone-platform-hint=auto "$@"
