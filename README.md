# pluto-propeller-verification
# Pluto Propeller Verification

A Gradio-based interface for a computer-vision system that checks Pluto drone propeller installation.

## Project architecture

- `app.py` — Gradio frontend.
- `backend/detection/` — YOLO object detection and image preprocessing (Member 1).
- `backend/reference/` — official Pluto reference configuration (Member 2).
- `backend/verification/` — configuration comparison and defect identification (Member 3).
- `backend/integration/pipeline.py` — connects the engines and returns the result to Gradio.
- `backend/reports/` — report formatting helpers.
- `models/` — trained inference model weights.
- `assets/reference_images/` — official reference images, if required.

## Local setup

Recommended Python version: 3.11.11.

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Open the local URL printed in the terminal.

## Render deployment

Use the existing Render Web Service connected to this repository.

- Build command: `pip install -r requirements.txt`
- Start command: `python app.py`

Render supplies the `PORT` environment variable; the app binds to it.

## Pipeline contract

The Gradio frontend calls:

```python
annotated_image, report = run_pipeline(image)
```

- `image`: RGB NumPy array supplied by Gradio.
- `annotated_image`: RGB NumPy array, or `None` if unavailable.
- `report`: Python dictionary.

Expected report shape:

```python
{
    "status": "PASS",  # or "INCORRECT INSTALLATION" / "UNABLE TO VERIFY"
    "summary": "Short explanation",
    "detections": {
        "motors": 4,
        "propellers": 4,
        "cw": 2,
        "ccw": 2
    },
    "errors": [
        {
            "motor": "M2",
            "error": "Incorrect propeller orientation",
            "expected": "CCW",
            "detected": "CW",
            "correction": "Install the correct propeller."
        }
    ],
    "corrections": []
}
```

The shape above is the integration target. Adapt the pipeline to the teammates' actual tested function signatures and outputs; do not rewrite their algorithms unnecessarily.

## Safety behavior

- The frontend defaults to `UNABLE TO VERIFY` until a backend result is returned.
- Only the verification engine should determine whether the installation passes.
- Missing, ambiguous or low-confidence detections must not be treated as PASS.
- The drone must remain disarmed with motors stopped during inspection.

## Model files

Do not commit large model weights or datasets blindly. Check GitHub file limits first. Use Git LFS or external model storage if the trained weights are too large. If using external storage, configure the model path through an environment variable or a documented download step.

## Current status

The frontend and integration placeholder can run independently. Detection, reference and verification modules are added when supplied by the team members.
