"""Confirm raspistill and raspivid (or libcamera equivalents) work on the Pi."""

import subprocess
import os
import sys


def run_cmd(cmd, description):
    print(f"[TEST] {description}")
    print(f"  Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            print(f"  PASS\n")
            return True
        else:
            print(f"  FAIL (exit code {result.returncode})")
            print(f"  stderr: {result.stderr.strip()}\n")
            return False
    except FileNotFoundError:
        print(f"  FAIL (command not found)\n")
        return False
    except subprocess.TimeoutExpired:
        print(f"  FAIL (timed out)\n")
        return False


def main():
    results = {}
    img_path = "/tmp/confirm_test.jpg"
    vid_path = "/tmp/confirm_test.h264"

    # Detect whether libcamera or legacy raspistill/raspivid tools are available.
    # Prefer libcamera - on newer Pi OS the legacy commands exist but don't work.
    libcam = subprocess.run(["which", "libcamera-still"], capture_output=True).returncode == 0
    legacy = subprocess.run(["which", "raspistill"], capture_output=True).returncode == 0

    if not legacy and not libcam:
        print("ERROR: Neither raspistill nor libcamera-still found on PATH.")
        sys.exit(1)

    if libcam:
        print("Detected: libcamera tools\n")
        results["libcamera-still"] = run_cmd(
            ["libcamera-still", "-o", img_path, "-t", "2000"],
            "Capture a still image with libcamera-still",
        )
        results["libcamera-vid"] = run_cmd(
            ["libcamera-vid", "-o", vid_path, "-t", "3000"],
            "Record a 3-second video with libcamera-vid",
        )
    else:
        print("Detected: legacy raspistill/raspivid\n")
        results["raspistill"] = run_cmd(
            ["raspistill", "-o", img_path, "-t", "2000"],
            "Capture a still image with raspistill",
        )
        results["raspivid"] = run_cmd(
            ["raspivid", "-o", vid_path, "-t", "3000"],
            "Record a 3-second video with raspivid",
        )

    # Verify output files exist and have content
    for path, label in [(img_path, "Image"), (vid_path, "Video")]:
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            size_kb = os.path.getsize(path) / 1024
            print(f"[OK] {label} saved: {path} ({size_kb:.1f} KB)")
        else:
            print(f"[MISSING] {label} not found or empty: {path}")

    # Summary
    print("\n--- Summary ---")
    all_pass = True
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_pass = False

    if all_pass:
        print("\nAll checks passed.")
    else:
        print("\nSome checks failed. See output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
