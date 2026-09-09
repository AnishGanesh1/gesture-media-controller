import cv2
import mediapipe as mp
import pyautogui
import time
import math

pyautogui.FAILSAFE = False

cap = cv2.VideoCapture(0)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# --- CONFIGURATION ---
PINCH_THRESHOLD = 35
MOVE_THRESHOLD = 30 # Vertical for Volume
SEEK_THRESHOLD = 35 # Horizontal for Seek
STABILITY_FRAMES = 5 # Number of frames for a gesture to be "confirmed"
SMOOTHING_FACTOR = 0.3
DEBOUNCE_PLAY_PAUSE = 1.0
DEBOUNCE_VOLUME = 0.15
DEBOUNCE_SEEK = 0.3

# --- STATE VARIABLES ---
current_smoothed_x, current_smoothed_y = 0, 0
prev_x, prev_y = 0, 0
last_action_times = {
    'play_pause': 0,
    'volume': 0,
    'seek': 0
}
gesture_history = []
confirmed_mode = "IDLE"

def distance(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

def get_finger_extended(lm_list):
    """Returns a list of booleans representing if [Thumb, Index, Middle, Ring, Pinky] are extended."""
    if not lm_list: return [False] * 5
    
    fingers = []
    # Thumb: Simple tip vs joint comparison
    fingers.append(lm_list[4][1] < lm_list[2][1]) 
    
    # 4 Fingers: Check if tip is above the joint (lower y value)
    for tip_id in [8, 12, 16, 20]:
        fingers.append(lm_list[tip_id][2] < lm_list[tip_id - 2][2])
        
    return fingers

while True:
    success, frame = cap.read()
    if not success:
        print("Camera frame not received. Exiting...")
        break
    
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    if result.multi_hand_landmarks:
        for handLms in result.multi_hand_landmarks:
            lm_list = []
            for id, lm in enumerate(handLms.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                lm_list.append((id, cx, cy))

            if lm_list:
                # 1. Coordinate Smoothing (EMA) for Index Finger Tip
                raw_x, raw_y = lm_list[8][1], lm_list[8][2]
                
                # Initialize state on first detection
                if current_smoothed_x == 0 and current_smoothed_y == 0:
                    current_smoothed_x, current_smoothed_y = raw_x, raw_y
                    prev_x, prev_y = raw_x, raw_y

                current_smoothed_x = (SMOOTHING_FACTOR * raw_x) + ((1 - SMOOTHING_FACTOR) * current_smoothed_x)
                current_smoothed_y = (SMOOTHING_FACTOR * raw_y) + ((1 - SMOOTHING_FACTOR) * current_smoothed_y)

                # 2. Robust Mode Selection with Hysteresis
                fingers = get_finger_extended(lm_list)
                
                raw_mode = "IDLE"
                if fingers[1] and not fingers[2] and not fingers[3] and not fingers[4]:
                    raw_mode = "VOLUME"
                elif fingers[1] and fingers[2] and not fingers[3] and not fingers[4]:
                    raw_mode = "SEEK"
                
                # Buffer the raw detections
                gesture_history.append(raw_mode)
                if len(gesture_history) > STABILITY_FRAMES:
                    gesture_history.pop(0)
                
                # Only switch mode if the last N frames agree
                if len(gesture_history) == STABILITY_FRAMES:
                    if all(m == gesture_history[0] for m in gesture_history):
                        confirmed_mode = gesture_history[0]

                # Visual feedback for mode
                color_map = {"IDLE": (0, 255, 0), "VOLUME": (0, 255, 255), "SEEK": (255, 255, 0)}
                circle_color = color_map.get(confirmed_mode, (0, 255, 0))
                
                cv2.circle(frame, (int(current_smoothed_x), int(current_smoothed_y)), 12, circle_color, cv2.FILLED)
                cv2.putText(frame, f"MODE: {confirmed_mode}", (20, 40), cv2.FONT_HERSHEY_DUPLEX, 0.8, circle_color, 2)

                # PLAY / PAUSE - Pinch gesture (Always active, but less sensitive to mode)
                thumb_tip = lm_list[4][1:]
                index_tip = lm_list[8][1:]
                dist = distance(thumb_tip, index_tip)
                
                now = time.time()
                if dist < 30 and now - last_action_times['play_pause'] > 1.2:
                    pyautogui.press('space')
                    cv2.putText(frame, "ACTION: PLAY/PAUSE", (20, 80), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 255), 3)
                    last_action_times['play_pause'] = now

                # 3. EXECUTE ACTIONS
                if confirmed_mode == "VOLUME":
                    # Vertical sensitivity
                    if current_smoothed_y < prev_y - MOVE_THRESHOLD:
                        if now - last_action_times['volume'] > DEBOUNCE_VOLUME:
                            pyautogui.press('up')
                            last_action_times['volume'] = now
                    elif current_smoothed_y > prev_y + MOVE_THRESHOLD:
                        if now - last_action_times['volume'] > DEBOUNCE_VOLUME:
                            pyautogui.press('down')
                            last_action_times['volume'] = now
                            
                elif confirmed_mode == "SEEK":
                    # Horizontal sensitivity
                    if current_smoothed_x > prev_x + SEEK_THRESHOLD: 
                        if now - last_action_times['seek'] > DEBOUNCE_SEEK:
                            pyautogui.press('right')
                            last_action_times['seek'] = now
                    elif current_smoothed_x < prev_x - SEEK_THRESHOLD:
                        if now - last_action_times['seek'] > DEBOUNCE_SEEK:
                            pyautogui.press('left')
                            last_action_times['seek'] = now

                # Always update previous positions for comparison
                prev_x, prev_y = current_smoothed_x, current_smoothed_y

            mp_draw.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS)

    cv2.imshow("Gesture Control", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()