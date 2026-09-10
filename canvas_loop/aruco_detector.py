import cv2
import numpy as np

ARUCO_DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
DETECTOR_PARAMS = cv2.aruco.DetectorParameters()
ARUCO_DETECTOR = cv2.aruco.ArucoDetector(ARUCO_DICT, DETECTOR_PARAMS)


def detect_aruco_markers(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image

    corners, ids, _rejected = ARUCO_DETECTOR.detectMarkers(gray)

    result = {}

    if ids is None:
        return result

    for marker_corners, marker_id in zip(corners, ids.flatten()):
        pts = marker_corners.reshape(4, 2)
        center_x = float(pts[:, 0].mean())
        center_y = float(pts[:, 1].mean())
        result[int(marker_id)] = (center_x, center_y)

    return result


def get_canvas_corners(image):
    markers = detect_aruco_markers(image)

    required_ids = [0, 1, 2, 3]  # top_left, top_right, bottom_right, bottom_left

    if not all(mid in markers for mid in required_ids):
        return None

    return np.array([markers[mid] for mid in required_ids], dtype=np.float32)


def compute_canvas_homography(image, dst_w, dst_h):
    src_pts = get_canvas_corners(image)

    if src_pts is None:
        return None

    dst_pts = np.array(
        [
            [0, 0],
            [dst_w, 0],
            [dst_w, dst_h],
            [0, dst_h],
        ],
        dtype=np.float32,
    )

    H = cv2.getPerspectiveTransform(src_pts, dst_pts)

    return H
