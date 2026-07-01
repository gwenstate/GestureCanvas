import cv2
import mediapipe as mp

class HandTracker:
    def __init__(self, max_hands=2, detection_confidence=0.8, tracking_confidence=0.8):
        self.mp_hands = mp.solutions.hands
        self.mp_draw  = mp.solutions.drawing_utils
        self.mp_style = mp.solutions.drawing_styles

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence
        )

        self.FINGER_TIPS = [4, 8, 12, 16, 20]

    def find_hands(self, frame, draw=True):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(rgb)

        if self.results.multi_hand_landmarks and draw:
            for hand_lm in self.results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    frame,
                    hand_lm,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_style.get_default_hand_landmarks_style(),
                    self.mp_style.get_default_hand_connections_style()
                )
        return frame

    def get_positions(self, frame, hand_index=0):
        positions = []
        if self.results.multi_hand_landmarks:
            if hand_index < len(self.results.multi_hand_landmarks):
                hand = self.results.multi_hand_landmarks[hand_index]
                h, w, _ = frame.shape
                for idx, lm in enumerate(hand.landmark):
                    positions.append((idx, int(lm.x * w), int(lm.y * h)))
        return positions

    def count_fingers_up(self, positions):
        if len(positions) < 21:
            return [False] * 5
        fingers = []
        fingers.append(positions[4][1] < positions[3][1])
        for tip_id in [8, 12, 16, 20]:
            fingers.append(positions[tip_id][2] < positions[tip_id - 2][2])
        return fingers

    def get_hand_label(self, hand_index=0):
        if self.results.multi_handedness:
            if hand_index < len(self.results.multi_handedness):
                return self.results.multi_handedness[hand_index].classification[0].label
        return None