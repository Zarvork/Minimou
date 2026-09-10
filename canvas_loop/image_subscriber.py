import cv2
import numpy as np
import zmq
from aruco_detector import compute_canvas_homography
from IndexDetector import IndexDetector

latest_coord = ()

CANVAS_W, CANVAS_H = 1280, 720  # pygame canvas size


def scale_matrix(src_w, src_h, dst_w, dst_h):
    return np.array(
        [[dst_w / src_w, 0, 0], [0, dst_h / src_h, 0], [0, 0, 1]], dtype=np.float32
    )


def kinect_to_canvas(point, H):
    pt = np.array([[point]], dtype=np.float32)
    out = cv2.perspectiveTransform(pt, H)
    return tuple(out[0, 0])


def receive_image():
    global latest_coord

    is_calibrated = False
    H = None

    context = zmq.Context()

    subscriber = context.socket(zmq.SUB)
    subscriber.setsockopt(zmq.CONFLATE, 1)
    subscriber.connect("ipc:///tmp/camera.ipc")

    subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

    detector = IndexDetector("hand_landmarker.task")

    while True:
        jpeg_data = subscriber.recv()

        frame = cv2.imdecode(np.frombuffer(jpeg_data, dtype=np.uint8), cv2.IMREAD_COLOR)

        if frame is None:
            continue

        h, w = frame.shape[:2]

        if not is_calibrated:
            raw_H = compute_canvas_homography(frame, w, h)
            if raw_H is not None:
                S = scale_matrix(w, h, CANVAS_W, CANVAS_H)
                H = S @ raw_H
                is_calibrated = True
                print("Calibration sucessfull")
            else:
                cv2.imshow("Camera", frame)
                if cv2.waitKey(1) & 0xFF == 27:
                    break
                continue

        points = detector.get_index_coordinates(frame)

        # print(points)

        if points != []:
            # Draw points
            for pt in points:
                cv2.circle(frame, (int(pt[0]), int(pt[1])), 6, (0, 255, 0), -1)

            # Projection matrix

            raw_point = points[0]
            canvas_point = kinect_to_canvas(raw_point, H)
            latest_coord = (float(canvas_point[0]), float(canvas_point[1]))

        cv2.imshow("Camera", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    subscriber.close()
    context.term()
    cv2.destroyAllWindows()
