import threading
from pathlib import Path

import cv2
import numpy as np
import zmq
from aruco_detector import compute_canvas_homography
from IndexDetector import IndexDetector

latest_coord = ()
finger_on_table = False
is_calibrated = False

_HERE = Path(__file__).parent

fs = cv2.FileStorage(str(_HERE / "calibration.yml"), cv2.FILE_STORAGE_READ)
H1 = fs.getNode("H1").mat()
H2 = fs.getNode("H2").mat()
fs.release()

w, h = 640, 480  # resolution of the kinect
CANVAS_W, CANVAS_H = 1280, 720  # pygame canvas size

DEPTH_MIN, DEPTH_MAX = 0, 2047

# Tolérance en unités brutes Kinect.
DEPTH_THRESHOLD = 30


def scale_matrix(src_w, src_h, dst_w, dst_h):
    return np.array(
        [[dst_w / src_w, 0, 0], [0, dst_h / src_h, 0], [0, 0, 1]], dtype=np.float32
    )


def kinect_to_canvas(point, H):
    pt = np.array([[point]], dtype=np.float32)
    out = cv2.perspectiveTransform(pt, H)
    return tuple(out[0, 0])


def depth_to_display(depth_frame):
    clipped = np.clip(depth_frame, DEPTH_MIN, DEPTH_MAX)
    normalized = ((clipped - DEPTH_MIN) / (DEPTH_MAX - DEPTH_MIN) * 255).astype(
        np.uint8
    )
    return cv2.applyColorMap(normalized, cv2.COLORMAP_JET)


def sample_depth_at(depth_frame, x, y, radius=2):
    fh, fw = depth_frame.shape
    x0, x1 = max(0, x - radius), min(fw, x + radius + 1)
    y0, y1 = max(0, y - radius), min(fh, y + radius + 1)

    patch = depth_frame[y0:y1, x0:x1].astype(np.int32)
    valid = patch[(patch > 0) & (patch < 2047)]

    return int(np.median(valid)) if valid.size > 0 else None


def is_finger_on_table(
    finger_pos, depth_frame, table_reference_depth_map, threshold=DEPTH_THRESHOLD
):
    if depth_frame is None or table_reference_depth_map is None:
        return False

    x, y = int(round(finger_pos[0])), int(round(finger_pos[1]))

    if not (0 <= x < depth_frame.shape[1] and 0 <= y < depth_frame.shape[0]):
        return False

    actual_depth = sample_depth_at(depth_frame, x, y)
    if actual_depth is None:
        return False

    expected_depth = sample_depth_at(table_reference_depth_map, x, y)
    if expected_depth is None:
        return False

    return abs(actual_depth - expected_depth) < threshold


class SharedState:
    def __init__(self):
        self.lock = threading.Lock()
        self.rgb_frame = None
        self.depth_frame = None
        self.stop = False


def rgb_worker(state: SharedState):
    global latest_coord, finger_on_table, is_calibrated

    context = zmq.Context.instance()
    subscriber = context.socket(zmq.SUB)
    subscriber.setsockopt(zmq.CONFLATE, 1)
    subscriber.connect("ipc:///tmp/camera_rgb.ipc")
    subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

    detector = IndexDetector(str(_HERE / "hand_landmarker.task"))

    H = None
    table_reference_depth_map = None

    while not state.stop:
        jpeg_data = subscriber.recv()
        frame = cv2.imdecode(np.frombuffer(jpeg_data, dtype=np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            continue

        frame_h, frame_w = frame.shape[:2]

        if not is_calibrated:
            raw_H = compute_canvas_homography(frame, frame_w, frame_h)
            if raw_H is not None:
                S = scale_matrix(frame_w, frame_h, CANVAS_W, CANVAS_H)
                H = S @ raw_H
                with state.lock:
                    depth_snapshot = state.depth_frame

                if depth_snapshot is not None:
                    table_reference_depth_map = depth_snapshot.copy()
                    is_calibrated = True
                    print("Calibration successful")
            with state.lock:
                state.rgb_frame = frame
            continue
        points = detector.get_index_coordinates(frame)

        if points:
            for pt in points:
                cv2.circle(frame, (int(pt[0]), int(pt[1])), 6, (0, 255, 0), -1)

            raw_point = points[1]
            canvas_point = kinect_to_canvas(raw_point, H)
            latest_coord = (float(canvas_point[0]), float(canvas_point[1]))

            with state.lock:
                depth_snapshot = state.depth_frame

            finger_on_table = is_finger_on_table(
                raw_point, depth_snapshot, table_reference_depth_map
            )
        else:
            finger_on_table = False

        with state.lock:
            state.rgb_frame = frame

    subscriber.close()


def depth_worker(state: SharedState):
    context = zmq.Context.instance()
    subscriber = context.socket(zmq.SUB)
    subscriber.setsockopt(zmq.CONFLATE, 1)
    subscriber.connect("ipc:///tmp/camera_depth.ipc")
    subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

    while not state.stop:
        depth_data = subscriber.recv()
        decoded = cv2.imdecode(
            np.frombuffer(depth_data, dtype=np.uint8), cv2.IMREAD_UNCHANGED
        )
        if decoded is None:
            continue
        with state.lock:
            state.depth_frame = decoded

    subscriber.close()


def receive_image():
    state = SharedState()

    rgb_thread = threading.Thread(target=rgb_worker, args=(state,), daemon=True)
    depth_thread = threading.Thread(target=depth_worker, args=(state,), daemon=True)
    rgb_thread.start()
    depth_thread.start()

    while True:
        with state.lock:
            rgb_frame = state.rgb_frame
            depth_frame = state.depth_frame

        if rgb_frame is not None:
            cv2.imshow("Camera", rgb_frame)

        if depth_frame is not None:
            cv2.imshow("Depth", depth_to_display(depth_frame))

        if cv2.waitKey(1) & 0xFF == 27:
            break

    state.stop = True
    cv2.destroyAllWindows()
