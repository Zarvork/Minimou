import cv2
import numpy as np
import zmq
from IndexDetector import IndexDetector

latest_coord = ()

fs = cv2.FileStorage("calibration.yml", cv2.FILE_STORAGE_READ)
H1 = fs.getNode("H1").mat()
H2 = fs.getNode("H2").mat()
fs.release()

w, h = 640, 480  # resolution of the kinect
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

        points = detector.get_index_coordinates(frame)

        print(points)

        if points != []:
            # Draw points
            for pt in points:
                cv2.circle(frame, (int(pt[0]), int(pt[1])), 6, (0, 255, 0), -1)
            S = scale_matrix(w, h, CANVAS_W, CANVAS_H)
            # Projection matrix
            H = S @ H2 @ H1
            raw_point = points[0]
            canvas_point = kinect_to_canvas(raw_point, H)
            latest_coord = canvas_point

        cv2.imshow("Camera", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    subscriber.close()
    context.term()
    cv2.destroyAllWindows()
