import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


MODEL_PATH = "hand_landmarker.task"


# Create MediaPipe hand detector
base_options = python.BaseOptions(
    model_asset_path=MODEL_PATH
)

options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=2,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5
)

detector = vision.HandLandmarker.create_from_options(
    options
)


# Open camera
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("Camera open nahi ho raha!")
    detector.close()
    exit()


print("Camera started!")
print("Apna hand camera ke saamne lao.")
print("Q press karke exit karo.")


while True:

    success, frame = camera.read()

    if not success:
        print("Camera frame nahi mil raha.")
        break

    # Mirror camera
    frame = cv2.flip(frame, 1)

    # Convert BGR -> RGB
    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    # Convert image for MediaPipe
    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    # Detect hands
    result = detector.detect(mp_image)

    # Draw detected landmarks
    if result.hand_landmarks:

        for hand in result.hand_landmarks:

            h, w, _ = frame.shape

            # Draw points
            for landmark in hand:

                x = int(
                    landmark.x * w
                )

                y = int(
                    landmark.y * h
                )

                cv2.circle(
                    frame,
                    (x, y),
                    5,
                    (0, 255, 0),
                    -1
                )

            # Connect some important points
            connections = [
                (0, 1),
                (1, 2),
                (2, 3),
                (3, 4),

                (0, 5),
                (5, 6),
                (6, 7),
                (7, 8),

                (0, 9),
                (9, 10),
                (10, 11),
                (11, 12),

                (0, 13),
                (13, 14),
                (14, 15),
                (15, 16),

                (0, 17),
                (17, 18),
                (18, 19),
                (19, 20),

                (5, 9),
                (9, 13),
                (13, 17)
            ]

            for start, end in connections:

                x1 = int(
                    hand[start].x * w
                )

                y1 = int(
                    hand[start].y * h
                )

                x2 = int(
                    hand[end].x * w
                )

                y2 = int(
                    hand[end].y * h
                )

                cv2.line(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (255, 0, 0),
                    2
                )

    # Show information
    cv2.putText(
        frame,
        "Hand Tracking Test",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 255),
        2
    )

    cv2.putText(
        frame,
        "Press Q to Exit",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    # Display
    cv2.imshow(
        "Hand Game Camera",
        frame
    )

    # Exit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# Cleanup
camera.release()
cv2.destroyAllWindows()
detector.close()

print("Program closed.")