#!/usr/bin/env bash

set -Eeuo pipefail

ROOT="/opt/canvas-loop"

cleanup() {
    if [[ -n "${KINECT_PID:-}" ]]; then
        kill "$KINECT_PID" 2>/dev/null || true
        wait "$KINECT_PID" 2>/dev/null || true
    fi
}

trap cleanup EXIT INT TERM

echo "USB devices:"
if command -v lsusb >/dev/null 2>&1; then
    lsusb
else
    echo "lsusb unavailable; continuing."
fi

echo "Starting Kinect publisher..."
"$ROOT/kinect/build/test-cv" &
KINECT_PID=$!

sleep 2

echo "Starting canvas loop..."
cd "$ROOT/canvas_loop"
exec uv run --project . python main.py
