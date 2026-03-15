# stimulus.py

import time
import csv
from pathlib import Path
import cv2

from compare import compare_snapshots


class Stimulus:
    def __init__(
        self,
        post_frames=12,
        pause_ms=20,
        trigger_fn=None,
        flush_grabs=2,
        save_enabled=True,
        save_root="captures",
    ):
        self.post_frames = post_frames
        self.pause_ms = pause_ms
        self.trigger_fn = trigger_fn
        self.flush_grabs = flush_grabs

        self.save_enabled = save_enabled
        self.save_root = Path(save_root)

    # Create a new unique folder for each stimulation captures/stim_0001, stim_0002, ...
    def _create_new_run_folder(self):
        self.save_root.mkdir(parents=True, exist_ok=True)

        max_index = 0
        for folder in self.save_root.glob("stim_*"):
            if folder.is_dir():
                try:
                    idx = int(folder.name.split("_")[1])
                    max_index = max(max_index, idx)
                except:
                    pass

        new_index = max_index + 1
        run_folder = self.save_root / f"stim_{new_index:04d}"
        run_folder.mkdir()
        return run_folder


    # Main stimulation sequence
    def run(self, cap, ui, frame_now=None):

        # Check that pivot and scanline are defined
        if ui.pivot_point is None:
            print("[STIM] No pivot point selected.")
            return None

        if ui.scanline_y is None:
            print("[STIM] No scanline selected.")
            return None

 
        # 1) Get rest frame (frame just before stimulation)
        if frame_now is None:
            ok, frame_now = cap.read()
            if not ok:
                print("[STIM] Could not read rest frame.")
                return None

        rest_full = frame_now.copy()
        rest = ui.crop(rest_full)

        # Convert pivot + scanline into ROI coordinates
        pivot_roi, row_roi = ui.full_to_roi_coords(
            ui.pivot_point,
            int(ui.scanline_y)
        )
        row_roi = int(row_roi)

        # Create folder for this stimulation
        run_folder = None
        if self.save_enabled:
            run_folder = self._create_new_run_folder()
            cv2.imwrite(str(run_folder / f"rest__{run_folder.name}.png"), rest)

        # 2) Send stimulation
        if self.trigger_fn is not None:
            try:
                self.trigger_fn()
            except Exception as e:
                print(f"[STIM] Trigger failed: {e}")
        else:
            print("[STIM] No trigger function defined.")

        # Flush camera buffer to sync timing
        for _ in range(self.flush_grabs):
            cap.grab()

        # 3) Capture post-stimulation frames
        best_result = None
        best_frame_index = None
        csv_rows = []

        for i in range(self.post_frames):

            ok, frame = cap.read()
            if not ok:
                continue

            post = ui.crop(frame)

            result = None
            error_msg = ""

            try:
                result = compare_snapshots(
                    rest,
                    post,
                    row=row_roi,
                    pivot_point_xy=pivot_roi,
                    show_plot=False,
                )
            except Exception as e:
                error_msg = str(e)

            # Save post frame with dTheta in filename
            if self.save_enabled and run_folder is not None:
                if result is not None:
                    dtheta = result["dtheta_deg"]
                    tag = f"{dtheta:+.2f}".replace("+", "plus").replace("-", "minus")
                    filename = f"post_{i:03d}__dtheta={tag}deg.png"
                else:
                    filename = f"post_{i:03d}__ERROR.png"

                cv2.imwrite(str(run_folder / filename), post)

            # Store results for CSV
            if result is not None:
                csv_rows.append({
                    "frame_i": i,
                    "dtheta_deg": result.get("dtheta_deg", ""),
                    "theta1_deg": result.get("theta1_deg", ""),
                    "theta2_deg": result.get("theta2_deg", ""),
                    "shift_px": result.get("shift_px", ""),
                    "row": result.get("row", row_roi),
                    "error": "",
                })

                # Track maximum absolute dTheta
                if best_result is None or abs(result["dtheta_deg"]) > abs(best_result["dtheta_deg"]):
                    best_result = result
                    best_frame_index = i
            else:
                csv_rows.append({
                    "frame_i": i,
                    "dtheta_deg": "",
                    "theta1_deg": "",
                    "theta2_deg": "",
                    "shift_px": "",
                    "row": row_roi,
                    "error": error_msg,
                })

            if self.pause_ms > 0:
                time.sleep(self.pause_ms / 1000.0)

        # 4) Save CSV summary
        if self.save_enabled and run_folder is not None:
            csv_path = run_folder / "results.csv"
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
                writer.writeheader()
                writer.writerows(csv_rows)

        # 5) Print final result
        if best_result is None:
            print("[STIM] No valid comparison result.")
            return None

        print("---- STIM RESULT ----")
        print(f"Folder: {run_folder}")
        print(f"Best frame index: {best_frame_index}")
        print(f"dTheta: {best_result['dtheta_deg']:.2f} deg")
        print("---------------------")

        return best_frame_index, best_result