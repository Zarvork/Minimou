#!/usr/bin/env bash

set -Eeuo pipefail

if ! sudo chmod o+rw $(for dev in /sys/bus/usb/devices/*/; do
    vendor=$(cat "$dev/idVendor" 2>/dev/null)
    if [[ "$vendor" == "045e" ]]; then
        busnum=$(cat "$dev/busnum" 2>/dev/null)
        devnum=$(cat "$dev/devnum" 2>/dev/null)
        printf "/dev/bus/usb/%03d/%03d " "$busnum" "$devnum"
    fi
done) 2>/dev/null; then
    echo "ERROR: Kinect non détecté ou non branché."
    exit 1
fi

exec docker compose up "$@"
