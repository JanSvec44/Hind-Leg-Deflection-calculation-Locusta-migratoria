import cv2
import pyvisa
from live import LiveUI
from compare import compare_snapshots
from stimulus import Stimulus


# Video parameters
CAMERA_INDEX = 0
FRAME_W = 1920  
FRAME_H = 1080
FPS = 30

AWG = None  # Keysight handler
KEYSIGHT_VISA_ADRESS = "USB0::0x2A8D::0x8D01::CN63220283::0::INSTR"


WINDOW = "Locust stimulation response analysis"
CROP_PREVIEW = "Crop Preview"

STIM_POST_FRAMES = 12
STIM_POST_FRAMES_INTER_DELAY = 20 # ms

def open_camera():
    # Opens camera
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError(f"Can't open the camera.")

    # Modifies video to parameters set above
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)
    cap.set(cv2.CAP_PROP_FPS, FPS)

    try:
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    except Exception:
        pass

    return cap

def init_awg(visa_address: str):
    # Keysight control
    rm = pyvisa.ResourceManager()
    inst = rm.open_resource(visa_address)
    inst.timeout = 5000

    try:
        print("[AWG]", inst.query("*IDN?").strip())
    except Exception:
        pass

    inst.write("TRIG:SOUR BUS")  
    inst.write("OUTP ON")        

    return inst

def send_stim():
    global AWG
    if AWG is None:
        print("[STIM] AWG not initialized")
        return
    AWG.write("*TRG")  # BUS trigger = software trigger
    print("[STIM] Sending trigger")

def main():
    global AWG
    AWG = init_awg(KEYSIGHT_VISA_ADRESS)

    cap = open_camera()

    ui = LiveUI() # Manages user input
    snapshots = []  # List of cropped frames

    stim = Stimulus(post_frames=STIM_POST_FRAMES, pause_ms=STIM_POST_FRAMES_INTER_DELAY, trigger_fn=send_stim, save_enabled=True, save_root="captures") # Stimulation handler

    # Window init
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(WINDOW, ui.mouse_callback)

    while True:
        # Throws away old frames, improves latency
        try:
            cap.grab()
        except Exception:
            pass

        # Read frame if possible
        ok, frame = cap.read()
        if not ok or frame is None:
            cv2.waitKey(5)
            continue

        # Initialize scanline in the middle of the frame height
        if ui.scanline_y is None:
            ui.scanline_y = frame.shape[0] // 2

        # Draw overlay
        vis = ui.draw_overlay(frame)
        cv2.imshow(WINDOW, vis)

        # Get key input
        key = cv2.waitKey(1) & 0xFF

        # Quit program Q
        if key in (ord("q"), ord("Q")):
            break

        # Move scanline up/down 2px W/S
        if key in (ord("w"), ord("W")):
            ui.scanline_y = max(0, int(ui.scanline_y) - 2)

        if key in (ord("s"), ord("S")):
            ui.scanline_y = min(frame.shape[0] - 1, int(ui.scanline_y) + 2)

        # Toggle crop preview T
        if key in (ord("t"), ord("T")):
            cv2.imshow(CROP_PREVIEW, ui.crop(frame))

        # Sends stimulation G
        if key in (ord("g"), ord("G")):
            stim.run(cap, ui)

    # Keysight release
    try:
        if AWG is not None:
            AWG.write("OUTP OFF")
            AWG.close()
    except Exception:
        pass
    
    # Feed release
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
