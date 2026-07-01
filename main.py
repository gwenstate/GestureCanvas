import cv2
import math
from collections import deque
from hand_tracker import HandTracker
from canvas import Canvas

def dist(p1, p2):
    return math.hypot(p1[0]-p2[0], p1[1]-p2[1])

def get_tip(pos, tip=8, dip=6, extend=10):
    dx = pos[tip][1] - pos[dip][1]
    dy = pos[tip][2] - pos[dip][2]
    ln = math.hypot(dx, dy)
    if ln == 0:
        return pos[tip][1], pos[tip][2]
    return (pos[tip][1] + int(dx/ln*extend),
            pos[tip][2] + int(dy/ln*extend))

PALM_CONN = [(0,1),(0,5),(0,9),(0,13),(0,17),(5,9),(9,13),(13,17)]
FINGERS   = [
    [(1,2),(2,3),(3,4)],
    [(5,6),(6,7),(7,8)],
    [(9,10),(10,11),(11,12)],
    [(13,14),(14,15),(15,16)],
    [(17,18),(18,19),(19,20)],
]
TIPS = [4, 8, 12, 16, 20]

def draw_skeleton(frame, positions):
    if not positions:
        return
    pts = {p[0]: (p[1], p[2]) for p in positions}
    all_conn = PALM_CONN + [c for f in FINGERS for c in f]
    for (a, b) in all_conn:
        if a in pts and b in pts:
            cv2.line(frame, pts[a], pts[b], (40,40,40), 3, cv2.LINE_AA)
    for (a, b) in all_conn:
        if a in pts and b in pts:
            cv2.line(frame, pts[a], pts[b], (210,210,210), 1, cv2.LINE_AA)
    for p in positions:
        idx, x, y = p[0], p[1], p[2]
        if idx == 0:
            cv2.circle(frame,(x,y),5,(40,40,40),cv2.FILLED)
            cv2.circle(frame,(x,y),3,(200,200,200),cv2.FILLED)
        elif idx in TIPS:
            cv2.circle(frame,(x,y),5,(40,40,40),cv2.FILLED)
            cv2.circle(frame,(x,y),3,(255,255,255),cv2.FILLED)
        elif idx in [1,5,9,13,17]:
            cv2.circle(frame,(x,y),4,(40,40,40),cv2.FILLED)
            cv2.circle(frame,(x,y),2,(170,170,170),cv2.FILLED)
        else:
            cv2.circle(frame,(x,y),3,(40,40,40),cv2.FILLED)
            cv2.circle(frame,(x,y),2,(120,120,120),cv2.FILLED)

def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    tracker = HandTracker(max_hands=2)
    canvas  = Canvas(width=1280, height=720)

    buf               = deque(maxlen=4)
    prev_move_x       = prev_move_y = None
    prev_pinch        = None
    prev_finger_state = None
    undo_hold         = 0
    UNDO_THRESHOLD    = 18

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        tracker.find_hands(frame, draw=False)

        pos0 = tracker.get_positions(frame, 0)
        pos1 = tracker.get_positions(frame, 1)

        draw_skeleton(frame, pos0)
        draw_skeleton(frame, pos1)

        ix = iy = None

        # two hands ngezoom
        if pos0 and pos1:
            x0, y0 = get_tip(pos0)
            x1, y1 = get_tip(pos1)
            d = dist((x0,y0),(x1,y1))

            if prev_pinch is not None:
                delta = d - prev_pinch
                if abs(delta) > 2:
                    canvas.zoom_canvas(1 + delta*0.007)
            prev_pinch = d

            mid = ((x0+x1)//2,(y0+y1)//2)
            cv2.line(frame,(x0,y0),(x1,y1),(50,50,50),1)
            cv2.circle(frame, mid, 5, (200,200,200), cv2.FILLED)
            cv2.putText(frame, f"{canvas.scale:.1f}x",
                        (mid[0]+10, mid[1]-8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200,200,200), 1)

            canvas.stop_drawing()
            buf.clear()
            prev_move_x = prev_move_y = None
            prev_finger_state = None
            ix, iy = x0, y0

        # one hand 
        elif pos0:
            prev_pinch = None
            fingers    = tracker.count_fingers_up(pos0)
            raw_x, raw_y = get_tip(pos0)

            buf.append((raw_x, raw_y))
            ix = int(sum(p[0] for p in buf)/len(buf))
            iy = int(sum(p[1] for p in buf)/len(buf))

            cur_state = (fingers[1], fingers[2], fingers[0], all(fingers))
            if cur_state != prev_finger_state:
                canvas.stop_drawing()
                prev_move_x = prev_move_y = None
                buf.clear()
                ix, iy = raw_x, raw_y
            prev_finger_state = cur_state

            # Jempol only = UNDO
            if fingers[0] and not any(fingers[1:]):
                undo_hold += 1
                pct = min(undo_hold/UNDO_THRESHOLD, 1.0)
                cv2.putText(frame,"UNDO",(ix-24,iy-32),
                            cv2.FONT_HERSHEY_SIMPLEX,0.65,(100,180,255),2)
                cv2.ellipse(frame,(ix,iy),(28,28),-90,0,
                            int(360*pct),(100,180,255),3)
                if undo_hold >= UNDO_THRESHOLD:
                    canvas.undo(); undo_hold=0
            else:
                undo_hold = 0

            # 1 jari
            if fingers[1] and not fingers[2]:
                on_panel = canvas.check_palette_hover(ix, iy)
                if not on_panel:
                    if canvas.mode == "draw":
                        canvas.draw(ix, iy)
                    elif canvas.mode == "erase":
                        canvas.erase(ix, iy)
                    elif canvas.mode == "move":
                        if prev_move_x is not None:
                            canvas.move_canvas(ix-prev_move_x, iy-prev_move_y)
                        prev_move_x, prev_move_y = ix, iy

            # 2 jari = stop
            elif fingers[1] and fingers[2]:
                canvas.check_palette_hover(ix, iy)
                canvas.stop_drawing()
                prev_move_x = prev_move_y = None

            # 5 jari = clear
            elif all(fingers):
                canvas.clear()
                canvas.stop_drawing()
                buf.clear()

            else:
                canvas.stop_drawing()
                prev_move_x = prev_move_y = None

        else:
            prev_pinch        = None
            prev_finger_state = None
            undo_hold         = 0
            buf.clear()
            canvas.stop_drawing()

        # RENDER 
        blended = canvas.blend_with_camera(frame)
        blended = canvas.draw_panel(blended)
        canvas.update_particles(blended)
        if ix is not None:
            canvas.draw_cursor(blended, ix, iy)

        cv2.imshow("GestureCanvas", blended)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            canvas._save()

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()