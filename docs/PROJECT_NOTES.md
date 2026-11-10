# Project notes

- The final notebook workflow uses the supplied YOLO checkpoint to detect propeller regions.
- The reference engine maps detected centres to four image-relative motor positions.
- The current reference configuration is `ASSUMED`, not confirmed.
- Propeller A/B classification is represented in the reference configuration and reporting interfaces, but automatic type classification is not connected to the final inference pipeline.
- The command-line script is a cleaned, reproducible entry point based on the final notebook workflow.
