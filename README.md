# GestureCanvas

A real-time, hand-tracking drawing app — no mouse, no stylus, just your fingers in front of a webcam.

Built with **OpenCV** + **MediaPipe**, GestureCanvas turns hand gestures into a full-featured digital canvas: draw, erase, move, zoom (with two hands!), undo, and toggle visual effects like glow trails and rainbow strokes — all live over your camera feed.

![Python](https://img.shields.io/badge/python-3.11-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.9-orange)

<!-- Optional: drop a demo GIF or screenshot here once you have one -->
<!-- ![demo](assets/demo.gif) -->

---

## ✨ Features

- **Gesture-based drawing** — index finger up to draw, no clicking required
- **Multi-tool system** — Draw / Erase / Move, switchable via the side panel
- **Two-hand pinch-to-zoom** — bring both index fingers together/apart to zoom the canvas in and out
- **Undo with a hold gesture** — hold thumb-only pose to trigger undo (with a radial progress indicator)
- **Clear canvas** — open palm (5 fingers) to wipe everything
- **Live FX toggles**
  - 🌟 **Glow** — soft bloom on your strokes
  - 🪞 **Mirror** — symmetric drawing across the vertical axis
  - ⚡ **Velocity** — brush size reacts to how fast you move
  - 🌈 **Rainbow** — auto-cycling stroke color
- **HSV color spectrum picker** + 16-color quick palette
- **Particle trail effects** while drawing
- **Save your canvas** as a PNG anytime

## 🎮 Controls

| Gesture | Action |
|---|---|
| ☝️ 1 finger (index) | Draw / Erase / Move (depending on active tool) |
| ✌️ 2 fingers (index + middle) | Stop / hover panel |
| 🖐️ 5 fingers (open palm) | Clear canvas |
| 👍 Thumb only, held | Undo |
| 🤏 Two hands, pinch distance | Zoom canvas in/out |
| Hover panel item ~0.3s | Select tool / color / toggle |

**Keyboard**
| Key | Action |
|---|---|
| `S` | Save canvas as PNG |
| `Q` | Quit |

## 🛠️ Tech Stack

- Python 3.11
- [OpenCV](https://opencv.org/) — video capture, rendering, image ops
- [MediaPipe](https://developers.google.com/mediapipe) — hand landmark tracking
- NumPy

## 📦 Installation

```bash
git clone https://github.com/<your-username>/GestureCanvas.git
cd GestureCanvas

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
python main.py
```

Requires a working webcam. Tested on Python 3.11.9 (MediaPipe does not yet support 3.14).

## 📁 Project Structure

```
GestureCanvas/
├── main.py           # App loop, gesture logic, camera capture
├── hand_tracker.py   # MediaPipe hand detection wrapper
├── canvas.py          # Drawing canvas, UI panel, effects, state
└── requirements.txt
```

## 🚧 Known Limitations / Roadmap

- Single-camera only, no multi-camera selection yet
- No layer system (single flat canvas)
- Save format limited to PNG
- Planned: brush presets, export session as video, custom gesture mapping

## 📄 License

MIT — feel free to fork and remix.

---

Made by [@gwenflfr](https://github.com/gwenflfr) as part of an ongoing series of creative-tech / computer vision experiments.
