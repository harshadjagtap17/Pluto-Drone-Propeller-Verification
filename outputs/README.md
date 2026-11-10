# Sample Outputs

This folder contains visual outputs extracted from the supplied `Pluto_Drone_Verification.ipynb` notebook and the supplied project image assets. These are actual notebook outputs, not synthetic example results.

## Structure

```text
outputs/
├── sample_verification/
│   ├── input_drone_top_view.png
│   ├── region_based_detection/
│   │   └── annotated_propeller_regions.png
│   └── yolo_reference_detections/
│       ├── reference_detection_01.jpg
│       └── reference_detection_02.jpg
├── propeller_crops/
│   ├── detected_propeller_D1.jpg
│   ├── detected_propeller_D2.jpg
│   ├── detected_propeller_D3.jpg
│   └── detected_propeller_D4.jpg
└── image_processing/
    ├── grayscale.png
    ├── gaussian_blur.png
    ├── canny_edges.png
    └── contour_detection.png
```

## Notes

- `input_drone_top_view.png` is the Pluto drone top-view reference photograph supplied with the project.
- `annotated_propeller_regions.png` visualizes the four propeller regions defined in the notebook's region-based detection stage. It should not be described as a YOLO prediction.
- `reference_detection_01.jpg` and `reference_detection_02.jpg` are annotated YOLO prediction visualizations displayed by the notebook for two reference images. They are kept in a separate folder because they are not the same image as `input_drone_top_view.png`.
- `detected_propeller_D1.jpg` through `D4` are the four propeller crop previews shown by the notebook's detection/cropping stage. The D-labels are retained as shown; no motor-position mapping is implied here.
- The image-processing files show intermediate grayscale, Gaussian blur, Canny edge, and contour-detection stages from the notebook.

These visuals demonstrate project stages; they are not a manufacturer-certified safety inspection or proof of flight readiness.
