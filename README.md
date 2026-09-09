# Gesture-Based Media Controller Using Computer Vision

Control a video player (YouTube, VLC, any player that responds to keyboard shortcuts) with
hand gestures from a plain webcam — no extra hardware, no training data, no cloud calls.

Built as Project No. 10 for **Computer Vision and Image Processing (AHP 3), PES University,
Jan–May 2026.**

---

## Demo

| Gesture | Mode | Action |
|---|---|---|
| Thumb + index pinch | any | Play / Pause (`space`) |
| Index finger only, move up / down | `VOLUME` | Volume up / down (`up` / `down`) |
| Index + middle finger, move left / right | `SEEK` | Rewind / Forward (`left` / `right`) |
| Open palm / anything else | `IDLE` | No action |

A colour-coded HUD shows the current mode live in the camera window — green for `IDLE`,
yellow for `VOLUME`, cyan for `SEEK` — so you always know what the system thinks you're doing.

> Add screenshots to `assets/` and reference them here, e.g. `![Volume mode](assets/volume_mode.png)`

---

## How it works

```
Camera ──► MediaPipe Hands ──► 21 landmarks ──► EMA smoothing ──► finger-state vector
                                                                        │
                                                    5-frame stability buffer (hysteresis)
                                                                        │
                                                        confirmed mode ─┴─► debounced pyautogui keypress
```

1. **Initialization** — open the webcam, load MediaPipe's pre-trained hand detection model.
2. **Frame capture & detection** — mirror the frame, convert BGR→RGB, run hand detection.
3. **Gesture recognition** — extract landmarks, smooth the index fingertip with an
   exponential moving average (α = 0.3), derive which fingers are extended.
4. **Mode confirmation** — a mode only switches after 5 consecutive frames agree, which is
   what kills the "Midas Touch" problem (accidental triggers from transitional hand poses).
5. **Action mapping** — pinch distance triggers play/pause; vertical motion in `VOLUME`
   mode and horizontal motion in `SEEK` mode trigger the corresponding keypresses, each
   with its own debounce timer.
6. **Output** — HUD overlay drawn on the frame; `Esc` exits cleanly.

### Key parameters

| Constant | Value | What it controls |
|---|---|---|
| `SMOOTHING_FACTOR` | 0.3 | EMA weight on the raw fingertip position |
| `STABILITY_FRAMES` | 5 | Frames a mode must hold before it is confirmed |
| `MOVE_THRESHOLD` | 30 px | Vertical travel needed for a volume step |
| `SEEK_THRESHOLD` | 35 px | Horizontal travel needed for a seek step |
| `DEBOUNCE_VOLUME` | 0.15 s | Minimum gap between volume keypresses |
| `DEBOUNCE_SEEK` | 0.3 s | Minimum gap between seek keypresses |

---

## Results

- 5-frame stability buffer mitigates the "Midas Touch" problem; estimated SUS ≈ 75+,
  above the 71.7 benchmark reported in [1].
- EMA smoothing (α = 0.3) converts jittery raw landmark coordinates into fluid motion.
- Colour-coded HUD gives real-time visual confirmation instead of console logs.
- 85–90% classification success rate across varying lighting conditions.

---

## Getting started

### Requirements

- Python 3.10 – 3.12
- A working webcam
- Camera permission for your terminal / IDE (macOS: System Settings → Privacy & Security → Camera;
  also grant Accessibility permission so `pyautogui` can send keystrokes)

### Install

```bash
git clone https://github.com/<your-username>/gesture-media-controller.git
cd gesture-media-controller

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### Run

```bash
python src/gesture_control.py
```

Open a video in another window, click it once so it has keyboard focus, then bring your
hand into frame. Press `Esc` in the camera window to quit.

> **Note:** the script sends real keystrokes to whichever window is focused. Keep the video
> player focused, not your code editor.

---

## Repository layout

```
gesture-media-controller/
├── src/
│   └── gesture_control.py     # main application
├── docs/
│   └── Batch_10_GestureBased_Media_Controller.pdf
├── assets/                    # screenshots / demo GIF
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Limitations & future work

- Performance degrades in poor lighting (a known limitation across the literature).
- Single-hand only; no multi-hand or two-handed gestures.
- Keypress-based control means the target player must have keyboard focus.
- Next: expand the gesture library, add environmental light compensation, and add a
  per-application key mapping config instead of hard-coded keys.

---

## Team

| Name | SRN |
|---|---|
| Medha Venkatesh | PES1UG23EC174 |
| Khushi Nesari | PES1UG23EC147 |
| Anish Ganesh | PES1UG23EC044 |

**Faculty:** Dr. Aswini N, Assoc. Prof., ECE, PES University

---

## References

[1] L. Melo, T. Nascimento, J. Felix, L. Cardoso and F. Soares, "Gesture-Based Interaction
with Video Players Using MediaPipe: A Case Study," *2025 IEEE Canadian Conference on
Electrical and Computer Engineering (CCECE)*, Canada, 2025.

[2] B. Dinesh, C. V. Naveeth Reddy and N. Senthamilarasi, "Computer Vision-Based Hand
Recognition and Gesture Control for Dino Games," *2025 International Conference on Emerging
Smart Computing and Informatics (ESCI)*, Pune, India, 2025.

---

## License

MIT — see [LICENSE](LICENSE).
