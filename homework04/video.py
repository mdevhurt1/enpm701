import cv2
import numpy as np
import time
from collections import deque
from picamera2 import Picamera2


def get_arrow_direction(mask):
    """
    Detect arrow direction from a binary mask using corner detection
    (goodFeaturesToTrack / Shi-Tomasi), matching the identify_corners.py technique.

    The mask's pixel centroid (center of mass of all white pixels) is used as the
    reference point.  The large rectangular shaft pushes this centroid toward the
    tail side, so the arrowhead tip is always the detected corner farthest from it.

    Returns (direction_str, tip_xy, centroid_xy, all_corners) or Nones on failure.
    """
    # Need white pixels to exist
    white_pixels = np.column_stack(np.where(mask > 127))  # (row, col)
    if len(white_pixels) < 100:
        return None, None, None, None

    # Mild blur spreads binary edges into gradients goodFeaturesToTrack can use
    blurred = cv2.GaussianBlur(mask, (5, 5), 0)

    corners = cv2.goodFeaturesToTrack(
        blurred,
        maxCorners=7,
        qualityLevel=0.01,
        minDistance=20,
    )
    if corners is None:
        return None, None, None, None

    corners = np.int0(corners)
    pts = corners.reshape(-1, 2).astype(float)

    # Pixel centroid - stable reference independent of how many corners were found
    mask_cx = float(white_pixels[:, 1].mean())  # col = x
    mask_cy = float(white_pixels[:, 0].mean())  # row = y
    mask_centroid = np.array([mask_cx, mask_cy])

    # Tip = corner farthest from the pixel centroid
    tip_idx = max(range(len(pts)), key=lambda i: np.linalg.norm(pts[i] - mask_centroid))
    tip = pts[tip_idx].astype(int)

    vec   = pts[tip_idx] - mask_centroid
    angle = np.degrees(np.arctan2(vec[1], vec[0]))

    if   -45  <= angle <  45:  direction = "Right"
    elif  45  <= angle < 135:  direction = "Down"
    elif angle >= 135 or angle < -135: direction = "Left"
    else:                      direction = "Up"

    return direction, tip, mask_centroid.astype(int), pts.astype(int)


def main(duration_seconds: int = 30, fps: int = 10, width: int = 640, height: int = 480):
    """
    Record a video for `duration_seconds`, detect arrow direction each frame
    using green masking + morphological clean-up + goodFeaturesToTrack corner
    detection, overlay direction on the frame, and record per-frame timing metrics.
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

    # Green HSV bounds (from convert_reference.py / colorpicker.py calibration)
    lower_green = np.array([50, 100, 71], dtype=np.uint8)
    upper_green = np.array([86, 253, 249], dtype=np.uint8)

    # Morphological kernel for mask clean-up (from blurr.py technique).
    # 3x3 here because the arrow is much smaller in 640x480 video than in the
    # high-res still; a 7x7 kernel would erode the small arrow away entirely.
    morph_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

    # Rolling buffer for temporal smoothing - avoids single-frame flickers
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

            # --- Corner-based arrow direction (identify_corners.py technique) ---
            direction, tip, centroid, all_corners = get_arrow_direction(mask)

            # --- Temporal smoothing: report the mode over the last 5 frames ---
            direction_buffer.append(direction or "Unknown")
            stable_direction = max(set(direction_buffer), key=direction_buffer.count)

            # --- Annotate frame ---
            if direction is not None:
                for pt in all_corners:
                    cv2.circle(frame, tuple(pt), 4, (0, 255, 255), -1)     # yellow = all corners
                cv2.circle(frame, tuple(tip),      8, (  0,   0, 255), -1)  # red    = tip
                cv2.circle(frame, tuple(centroid), 5, (255,   0,   0), -1)  # blue   = centroid
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

            # Pace the loop to the declared fps so the video plays back in real time.
            # If processing already took longer than one frame period, skip the sleep.
            frame_delta = time.perf_counter() - frame_start
            sleep_needed = (1.0 / fps) - frame_delta
            if sleep_needed > 0:
                time.sleep(sleep_needed)

            # Record total frame time (processing + sleep) for the delta overlay
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
