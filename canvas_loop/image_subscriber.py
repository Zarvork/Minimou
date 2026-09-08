import cv2
import numpy as np
import zmq
from IndexDetector import IndexDetector

latest_coord = (0, 0)


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
            latest_coord = points[0]

        cv2.imshow("Camera", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    subscriber.close()
    context.term()
    cv2.destroyAllWindows()
