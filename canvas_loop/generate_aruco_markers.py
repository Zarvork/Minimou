import cv2
import numpy as np

ARUCO_DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
MARKER_SIZE_PX = 200

CORNER_IDS = {
    "top_left": 0,
    "top_right": 1,
    "bottom_right": 2,
    "bottom_left": 3,
}


def generate_markers(output_dir="."):
    for name, marker_id in CORNER_IDS.items():
        marker_img = cv2.aruco.generateImageMarker(
            ARUCO_DICT, marker_id, MARKER_SIZE_PX
        )
        path = f"{output_dir}/aruco_{marker_id}_{name}.png"
        cv2.imwrite(path, marker_img)
        print(f"Marker {marker_id} ({name}) -> {path}")


if __name__ == "__main__":
    generate_markers()
