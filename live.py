import cv2


class LiveUI:
    def __init__(self):
        # UI elements (x, y regarding full frame)
        self.pivot_point = None     # Pivot point
        self.roi = None        # Region of interest 
        self.scanline_y = None # Scanline for 2 frame comparison

        # Status for ROI
        self.dragging = False
        self.p1 = None
        self.p2 = None

    # Mouse input handling
    def mouse_callback(self, event, x, y, flags, param):
        # Left MB - set pivot point
        if event == cv2.EVENT_LBUTTONDOWN:
            self.pivot_point = (x, y)

        # Right MB - start of ROI
        if event == cv2.EVENT_RBUTTONDOWN:
            self.dragging = True
            self.p1 = (x, y)
            self.p2 = (x, y)

        # Dragging
        if event == cv2.EVENT_MOUSEMOVE and self.dragging:
            self.p2 = (x, y)

        # End of dragging - save ROI in 2 points p1, p2
        if event == cv2.EVENT_RBUTTONUP:
            self.dragging = False
            self.p2 = (x, y)
            self.roi = self._normalize_roi(self.p1, self.p2)

    # Sort p1 and p2, to handle drag left to right vs right to left
    @staticmethod
    def _normalize_roi(p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])
        return (x1, y1, x2, y2)

    # Cropping
    def crop(self, frame):
        # If ROI selected, crop the frame, otherwise do nothing
        if self.roi is None:
            return frame

        # Read ROI, check for out of frame bounds
        x1, y1, x2, y2 = self.roi
        x1 = max(0, x1); y1 = max(0, y1)
        x2 = min(frame.shape[1], x2)
        y2 = min(frame.shape[0], y2)

        # Check if rectangle, if not, do nothing
        if x2 <= x1 or y2 <= y1:
            return frame

        # Return cropped frame
        return frame[y1:y2, x1:x2]

    # Recalculate pivot point and scanline to ROI coordinates
    def full_to_roi_coords(self, pivot_point_full, scanline_y_full,):
        
        # if no ROI -> do nothing
        if self.roi is None:
            return pivot_point_full, scanline_y_full

        # Read ROI, return recalculated pivot point and scanline
        x1, y1, x2, y2 = self.roi
        cx, cy = pivot_point_full
        return (cx - x1, cy - y1), (scanline_y_full - y1)

    # Image output - draws frame, instructions, pivot point, ROI, scanline
    def draw_overlay(self, frame):

        out = frame.copy() # Helper frame

        # Instructions
        cv2.putText(
            out,
            "LMB=pivot point | RMB+drag=ROI | W/S scanline | R=snapshot | T=crop preview | Q=quit",
            (10, out.shape[0] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            2
        )

        # Draw pivot point 
        if self.pivot_point is not None:
            cv2.circle(out, self.pivot_point, 5, (0, 255, 255), -1)
            cv2.putText(out, f"Pivot point: {self.pivot_point}", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

        # ROI 
        roi_draw = None
        if self.dragging and self.p1 is not None and self.p2 is not None: # Live dragging
            roi_draw = self._normalize_roi(self.p1, self.p2)
        elif self.roi is not None: # Finished dragging 
            roi_draw = self.roi

        # Draw ROI
        if roi_draw is not None:
            x1, y1, x2, y2 = roi_draw
            cv2.rectangle(out, (x1, y1), (x2, y2), (255, 255, 0), 2)
            cv2.putText(out, "ROI", (x1, max(0, y1 - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

        # Draw scanline
        if self.scanline_y is not None:
            y = int(self.scanline_y)
            cv2.line(out, (0, y), (out.shape[1] - 1, y), (255, 0, 255), 2)
            cv2.putText(out, f"Scanline y={y}", (10, 55),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)

        return out
