import cv2
import numpy as np
import time
from collections import deque
from picamera2 import Picamera2


def get_arrow_direction(mask):
    """
    Detect arrow direction from a binary mask using contour analysis and
    convexity defects (identify_corners.py technique).

    The arrow's unique structural signature is the "armpit" notch where the
    wide arrowhead meets the narrower shaft.  convexityDefects finds this notch
    reliably.  The tip is then the convex-hull point farthest from the notch,
    and the vector from the contour centroid to the tip gives the direction.

    Returns (direction_str, tip_xy, centroid_xy, notch_xy) or Nones on failure.
    """
    _, thresh = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
    cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None, None, None, None

    cnt = max(cnts, key=cv2.contourArea)
    if cv2.contourArea(cnt) < 500:
        return None, None, None, None

    hull_idx = cv2.convexHull(cnt, returnPoints=False)
    defects  = cv2.convexityDefects(cnt, hull_idx)
    if defects is None:
        return None, None, None, None

    # Deepest defect = the notch (armpit between shaft and arrowhead)
    deepest  = max(defects[:, 0], key=lambda d: d[3])
    notch_pt = cnt[deepest[2]][0]

    # Tip = hull point farthest from the notch
    hull_pts = cv2.convexHull(cnt)  # shape (M, 1, 2) — actual coordinates
    tip = max(hull_pts,
              key=lambda p: np.linalg.norm(np.array(p[0]) - notch_pt.astype(float)))[0]

    # Centroid via image moments
    M  = cv2.moments(cnt)
    cx = int(M['m10'] / M['m00'])
    cy = int(M['m01'] / M['m00'])

    vec   = tip.astype(float) - np.array([cx, cy], dtype=float)
    angle = np.degrees(np.arctan2(vec[1], vec[0]))

    if   -45  <= angle <  45:  direction = "Right"
    elif  45  <= angle < 135:  direction = "Down"
    elif angle >= 135 or angle < -135: direction = "Left"
    else:                      direction = "Up"

    return direction, tip, np.array([cx, cy]), notch_pt


def main(duration_seconds: int = 30, fps: int = 30, width: int = 640, height: int = 480):
    """
    Record a video for `duration_seconds`, detect arrow direction each frame
    using green masking + morphological clean-up + contour/defect analysis,
    overlay direction on the frame, and record per-frame timing metrics.
    Output files: output.avi, frame_times.txt
    """
    picam2 = Picamera2()
    config = picam2.create_video_configuration(main={"size": (width, height), "format": "RGB888"})
    picam2.configure(config)
    picam2.start()

    # Allow sensor to adjust (from still.py / homework03/video.py)
    time.sleep(2)

    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    out = cv2.VideoWriter("output.avi", fourcc, fps, (width, height))

    # Green HSV bounds (from convert_reference.py)
    lower_green = np.array([70, 90, 150], dtype=np.uint8)
    upper_green = np.array([80, 255, 255], dtype=np.uint8)

    # Morphological kernel for mask clean-up (from blurr.py technique)
    morph_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))

    # Rolling buffer for temporal smoothing — avoids single-frame flickers
    direction_buffer = deque(maxlen=5)

    # Performance / metrics (from homework03/video.py)
    start_time = time.time()
    frame_counter = 0
    deltas_sum = 0.0
    min_delta = float("inf")
    max_delta = 0.0
    times_out = None

    try:
        times_out = open("frame_times.txt", "w")
        while True:
            frame_start = time.perf_counter()

            frame = picam2.capture_array()

            # Flip vertically (from homework03/video.py)
            frame = cv2.flip(frame, 0)

            # --- Green mask (convert_reference.py technique) ---
            # picamera2 RGB888 delivers RGB data; use COLOR_RGB2HSV (not BGR2HSV)
            hsv  = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
            mask = cv2.inRange(hsv, lower_green, upper_green)

            # --- Morphological clean-up (blurr.py technique) ---
            # CLOSE fills holes inside the arrow; OPEN removes noise speckles
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, morph_kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  morph_kernel)

            # --- Contour-based arrow direction (identify_corners.py technique) ---
            direction, tip, centroid, notch_pt = get_arrow_direction(mask)

            # --- Temporal smoothing: report the mode over the last 5 frames ---
            direction_buffer.append(direction or "Unknown")
            stable_direction = max(set(direction_buffer), key=direction_buffer.count)

            # --- Annotate frame ---
            if direction is not None:
                cv2.circle(frame, tuple(notch_pt), 6, (255,   0,   0), -1)  # blue  = notch
                cv2.circle(frame, tuple(tip),       8, (  0,   0, 255), -1)  # red   = tip
                cv2.circle(frame, tuple(centroid),  5, (  0, 255, 255), -1)  # yellow = centroid
                cv2.arrowedLine(frame, tuple(centroid), tuple(tip), (0, 255, 0), 2, tipLength=0.3)
                cv2.putText(
                    frame, f"Direction: {stable_direction}",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2,
                )
            else:
                cv2.putText(
                    frame, f"Direction: {stable_direction}",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2,
                )

            # Elapsed time overlay (from homework03/video.py)
            elapsed = int(time.time() - start_time)
            cv2.putText(
                frame, f"Time: {elapsed}s",
                (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2,
            )

            # Frame delta overlay (from homework03/video.py) — computed before write
            frame_delta = time.perf_counter() - frame_start
            cv2.putText(
                frame, f"Delta: {frame_delta:.3f}s",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2,
            )

            out.write(frame)

            # Update running stats
            deltas_sum += frame_delta
            min_delta = min(min_delta, frame_delta)
            max_delta = max(max_delta, frame_delta)

            # Write per-frame metrics (frame index, delta, direction)
            if times_out is not None:
                times_out.write(f"{frame_counter},{frame_delta:.6f},{stable_direction}\n")
                times_out.flush()

            print(f"Frame {frame_counter}: {frame_delta:.6f}s  Direction: {stable_direction}")
            frame_counter += 1

            if time.time() - start_time >= duration_seconds:
                break

    finally:
        if times_out is not None:
            avg = deltas_sum / frame_counter if frame_counter > 0 else 0.0
            times_out.write(
                f"# frames={frame_counter}, avg={avg:.6f}, min={min_delta:.6f}, max={max_delta:.6f}\n"
            )
            times_out.close()
        out.release()
        picam2.stop()


if __name__ == "__main__":
    main()
