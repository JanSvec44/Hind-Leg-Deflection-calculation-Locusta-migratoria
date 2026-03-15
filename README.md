# Locust Stimulation Response Analysis

Python tool for analyzing angular movement of a biological structure
after electrical stimulation.

The system captures frames from a camera, triggers stimulation using a
Keysight AWG, and computes angular displacement between pre‑ and
post‑stimulation frames using image analysis.


## Features

-   Live camera preview with overlay
-   Interactive selection of:
    -   pivot point
    -   region of interest (ROI)
    -   scanline used for comparison
-   Hardware stimulation trigger via Keysight AWG (PyVISA)
-   Automatic capture of post‑stimulus frames
-   Angle calculation from image shift
-   Automatic saving of images and experiment results
-   CSV export of all frame measurements


## How the algorithm works

1.  Capture a **rest frame** before stimulation.
2.  Send a trigger to the AWG.
3.  Capture multiple frames after stimulation.
4.  Compare each frame with the rest frame.

Processing steps:

1.  Convert frames to grayscale.
2.  Extract intensity profile along a chosen scanline.
3.  Detect the maximum intensity position.
4.  Measure the shift between frames.
5.  Convert the shift into angular displacement relative to the pivot
    point.

Angles are computed as:

theta = atan2(dx, dy)

Where:

-   `dx` = horizontal offset from pivot
-   `dy` = vertical distance from pivot to scanline

The final result is:

dtheta = theta2 - theta1


## Project structure

    .
    ├── main.py
    ├── live.py
    ├── stimulus.py
    ├── compare.py

### main.py

Controls the application:
- camera initialization 
- AWG communication 
- UI loop 
- stimulation triggering

### live.py

User interface:
- pivot point selection
- ROI selection 
- scanline control
- overlay rendering

### stimulus.py

Handles stimulation experiments:
- capture rest frame 
- send trigger 
- capture post‑stimulation frames 
- compute displacement 
- save images and results

### compare.py

Core image analysis: 
- extract scanline intensity 
- detect maxima 
- compute angular displacement


## Requirements

Python 3.9+

Install dependencies:

    pip install opencv-python numpy matplotlib pyvisa

You also need **Keysight VISA** installed for AWG
communication.


## Hardware

Required:

-   camera supported by OpenCV
-   Keysight arbitrary waveform generator
-   VISA interface (USB/LAN)

Example VISA address used in the code:

    USB0::0x2A8D::0x8D01::CN63220283::0::INSTR


## Controls

  Key          Action
  ------------ ---------------------
  - LMB          Set pivot point
  - RMB + drag   Select ROI
  - W / S        Move scanline
  - T            Show crop preview
  - G            Trigger stimulation
  - Q            Quit program


## Output

Each stimulation creates a folder:

    captures/
       stim_0001/
       stim_0002/

Example contents:

    rest__stim_0001.png
    post_000__dtheta=...
    post_001__dtheta=...
    results.csv


## Running the program

    python main.py

Workflow:

1.  Start the program.
2.  Set the pivot point.
3.  Draw the ROI.
4.  Adjust the scanline.
5.  Press **G** to trigger stimulation.
6.  Frames are captured and the angular displacement is calculated.


## Possible improvements

-   automatic pivot detection
-   automatic scanline detection
-   real‑time angle display

