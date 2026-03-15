import cv2
import numpy as np
import math
import matplotlib.pyplot as plt

def compare_snapshots(I1_bgr, I2_bgr, row: int, pivot_point_xy, show_plot: bool = False):

    # Check for pivot point
    if pivot_point_xy is None:
        raise ValueError("No pivotpoint set")

    cx, cy = pivot_point_xy

    # 1) Get grayscale normalized frames
    I1 = cv2.cvtColor(I1_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    I2 = cv2.cvtColor(I2_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0

    h = I1.shape[0]
    row = int(np.clip(row, 0, h - 1))

    # 2) Loading scanline profile
    data1 = I1[row, :]
    data2 = I2[row, :]

    # 3) Maximum on the scanlines, calculate maximum shift
    max1 = int(np.argmax(data1))
    max2 = int(np.argmax(data2))
    shift_px = max2 - max1

    # 4) Pivot geometry
    # Calculate scanline to pivot point distance
    dy = float(cy) - float(row)

    if dy <= 0:
        # Scanline is on or below pivot point, doesn't make sense
        raise ValueError(
            f"Scanline= {row} isn't above pivot point= {cy}."
        )

    # Maximum positions relative to pivot point
    dx1 = float(max1) - float(cx)
    dx2 = float(max2) - float(cx)

    # Calculate angles
    theta1_rad = math.atan2(dx1, dy)
    theta2_rad = math.atan2(dx2, dy)
    dtheta_rad = theta2_rad - theta1_rad

    # Angle wrapping (convert -pi;pi to 0;2pi)
    dtheta_rad = (dtheta_rad + math.pi) % (2 * math.pi) - math.pi

    # Convert to degrees
    theta1_deg = math.degrees(theta1_rad)
    theta2_deg = math.degrees(theta2_rad)
    dtheta_deg = math.degrees(dtheta_rad)

    # 5) volitelný plot (debug)
    if show_plot:
        plt.figure(figsize=(10, 5))
        plt.plot(data1, label="snapshot A", alpha=0.8)
        plt.plot(data2, label="snapshot B", alpha=0.8)
        plt.axvline(max1, linestyle="--", alpha=0.6)
        plt.axvline(max2, linestyle="--", alpha=0.6)
        plt.title(
            f"row={row} | max1={max1} max2={max2} | shift={shift_px}px | "
            f"theta1={theta1_deg:.2f}° theta2={theta2_deg:.2f}° | dtheta={dtheta_deg:.2f}°"
        )
        plt.xlabel("x [px]")
        plt.ylabel("intensity (0..1)")
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.show()

    return {
        "row": row,
        "max1": max1,
        "max2": max2,
        "shift_px": shift_px,
        "pivot_point_xy": (cx, cy),
        "dy": dy,
        "theta1_rad": theta1_rad,
        "theta2_rad": theta2_rad,
        "theta1_deg": theta1_deg,
        "theta2_deg": theta2_deg,
        "dtheta_rad": dtheta_rad,
        "dtheta_deg": dtheta_deg,
    }