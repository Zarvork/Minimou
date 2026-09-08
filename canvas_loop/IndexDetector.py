import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class IndexDetector:
    def __init__(self, model_path="hand_landmarker.task"):
        base_options = python.BaseOptions(model_asset_path=model_path)

        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_hands=1,
            min_hand_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        self.landmarker = vision.HandLandmarker.create_from_options(options)

    def get_index_coordinates(self, image):
        if image is None or image.size == 0:
            return []

        height, width = image.shape[:2]

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)

        result = self.landmarker.detect(mp_image)

        points = []

        for hand_landmarks in result.hand_landmarks:
            index_tip = hand_landmarks[8]

            x = int(index_tip.x * width)
            y = int(index_tip.y * height)

            points.append((x, y))

        return points

    def close(self):
        self.landmarker.close()
