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
            min_hand_detection_confidence=0.3,
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

            index_mid_high = hand_landmarks[7]
            index_mid = hand_landmarks[6]
            index_bot = hand_landmarks[5]

            x_tip = int(index_tip.x * width)
            y_tip = int(index_tip.y * height)

            x_mid_high = int(index_mid_high.x * width)
            y_mid_high = int(index_mid_high.y * height)

            x_mid = int(index_mid.x * width)
            y_mid = int(index_mid.y * height)

            x_bot = int(index_bot.x * width)
            y_bot = int(index_bot.y * height)

            points.append((x_tip, y_tip))
            points.append((x_mid_high, y_mid_high))
            points.append((x_mid, y_mid))
            points.append((x_bot, y_bot))

        return points

    def close(self):
        self.landmarker.close()
