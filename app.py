import html
import os

import gradio as gr
import numpy as np

from backend.integration.pipeline import run_pipeline


def _safe(value):
    return html.escape(str(value if value is not None else ""))


def _status_card(report):
    status = str(report.get("status", "UNABLE TO VERIFY")).upper()
    styles = {
        "PASS": ("#16834A", "#EAF7EF", "✓"),
        "INCORRECT INSTALLATION": ("#D92D20", "#FDECEC", "!"),
        "UNABLE TO VERIFY": ("#A66A00", "#FFF6E5", "?"),
    }
    color, background, symbol = styles.get(
        status, styles["UNABLE TO VERIFY"]
    )
    summary = _safe(report.get(
        "summary",
        "The installation could not be verified."
    ))
    return f"""
    <div class="status-card" style="background:{background};
         border-left:4px solid {color};">
      <div class="status-symbol" style="color:{color}">{symbol}</div>
      <div>
        <div class="status-title" style="color:{color}">{_safe(status)}</div>
        <div class="status-summary">{summary}</div>
      </div>
    </div>
    """


def _report_html(report):
    detections = report.get("detections") or {}
    errors = report.get("errors") or []
    corrections = report.get("corrections") or []

    rows = []
    labels = [
        ("Motors detected", "motors"),
        ("Propellers detected", "propellers"),
        ("Clockwise (CW)", "cw"),
        ("Counter-clockwise (CCW)", "ccw"),
    ]
    for label, key in labels:
        value = detections.get(key, "—")
        rows.append(
            f"<tr><td>{_safe(label)}</td><td>{_safe(value)}</td></tr>"
        )

    if errors:
        error_items = []
        for item in errors:
            if isinstance(item, dict):
                motor = _safe(item.get("motor", "Unspecified position"))
                error = _safe(item.get("error", "Installation defect"))
                expected = _safe(item.get("expected", "—"))
                detected = _safe(item.get("detected", "—"))
                correction = _safe(item.get("correction", "Follow the official Pluto configuration."))
                error_items.append(
                    f"""<div class="error-item">
                    <strong>{motor}: {error}</strong>
                    <div>Expected: {expected} &nbsp;|&nbsp; Detected: {detected}</div>
                    <div class="correction">{correction}</div>
                    </div>"""
                )
            else:
                error_items.append(
                    f'<div class="error-item">{_safe(item)}</div>'
                )
        error_html = "".join(error_items)
    else:
        error_html = '<div class="muted">No verified defects to display.</div>'

    correction_html = ""
    if corrections:
        correction_html = (
            '<h3>Required corrections</h3><ul>'
            + "".join(f"<li>{_safe(item)}</li>" for item in corrections)
            + "</ul>"
        )

    return f"""
    <div class="report-card">
      <h3>Detection summary</h3>
      <table class="summary-table">{''.join(rows)}</table>
      <h3>Detected defects</h3>
      {error_html}
      {correction_html}
    </div>
    """


def verify_image(image):
    if image is None:
        report = {
            "status": "UNABLE TO VERIFY",
            "summary": "Upload a clear image of the Pluto drone to begin.",
            "detections": {},
            "errors": [],
        }
        return None, _status_card(report), _report_html(report)

    try:
        # Gradio supplies an RGB NumPy array. The pipeline contract
        # accepts RGB and must return an RGB annotated image.
        annotated_image, report = run_pipeline(image)

        if not isinstance(report, dict):
            raise TypeError(
                "run_pipeline() must return a report as a Python dictionary."
            )

        report.setdefault("status", "UNABLE TO VERIFY")
        report.setdefault(
            "summary",
            "The system could not establish a reliable result."
        )
        report.setdefault("detections", {})
        report.setdefault("errors", [])

        # Safety guard: only the verification engine may set PASS.
        allowed = {
            "PASS",
            "INCORRECT INSTALLATION",
            "UNABLE TO VERIFY",
        }
        if str(report["status"]).upper() not in allowed:
            report["status"] = "UNABLE TO VERIFY"
            report["summary"] = (
                "The verification engine returned an unsupported status."
            )

        return annotated_image, _status_card(report), _report_html(report)

    except Exception as exc:
        report = {
            "status": "UNABLE TO VERIFY",
            "summary": f"Image processing failed: {exc}",
            "detections": {},
            "errors": [],
        }
        return image, _status_card(report), _report_html(report)


def clear_all():
    report = {
        "status": "UNABLE TO VERIFY",
        "summary": "Upload a drone image to begin inspection.",
        "detections": {},
        "errors": [],
    }
    return None, None, _status_card(report), _report_html(report)


CSS = """
.gradio-container {
    max-width: 1180px !important;
    margin: auto !important;
    background: #F5F5F7 !important;
    color: #1D1D1F !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
}
.header {
    display:flex; justify-content:space-between; align-items:center;
    padding:22px 4px; border-bottom:1px solid #E5E5E7; margin-bottom:28px;
}
.brand {font-size:18px; font-weight:750; letter-spacing:-.4px;}
.brand span {color:#0878E8;}
.online {font-size:11px; color:#16834A; font-weight:700; letter-spacing:1px;}
.hero {text-align:center; padding:12px 8px 30px;}
.hero-label {font-size:11px; color:#0878E8; font-weight:750; letter-spacing:2px;}
.hero h1 {font-size:40px; letter-spacing:-1.5px; margin:10px 0;}
.hero p {color:#6E6E73; font-size:15px; line-height:1.6;}
.panel {
    background:#fff; border:1px solid #E8E8ED; border-radius:18px;
    padding:20px; box-shadow:0 4px 18px rgba(0,0,0,.025);
}
.panel-title {font-size:17px; font-weight:700; margin-bottom:5px;}
.panel-subtitle {font-size:13px; color:#86868B; margin-bottom:15px;}
.status-card {display:flex; gap:14px; padding:17px; border-radius:12px; margin:4px 0 14px;}
.status-symbol {font-size:22px; font-weight:800;}
.status-title {font-size:14px; font-weight:800; letter-spacing:.3px;}
.status-summary {font-size:13px; color:#55555A; margin-top:5px; line-height:1.5;}
.report-card {background:#fff; border:1px solid #E8E8ED; border-radius:16px; padding:18px;}
.report-card h3 {font-size:14px; margin:5px 0 12px;}
.summary-table {width:100%; border-collapse:collapse; font-size:13px;}
.summary-table td {padding:9px 5px; border-bottom:1px solid #EEE;}
.summary-table td:last-child {text-align:right; font-weight:650;}
.error-item {background:#FFF6F5; border:1px solid #F5D6D2; border-radius:10px; padding:12px; margin:8px 0; font-size:13px; line-height:1.6;}
.correction {color:#55555A; margin-top:4px;}
.muted {font-size:13px; color:#86868B;}
.safety {background:#EAF3FF; border:1px solid #D8E8FF; border-radius:12px;
    padding:15px 18px; color:#315A85; font-size:13px; line-height:1.6; margin-top:18px;}
.footer {text-align:center; padding:26px 8px 15px; color:#86868B; font-size:11px; line-height:1.8;}
.primary-button {background:#0878E8 !important; border:0 !important; border-radius:11px !important; min-height:46px !important; font-weight:650 !important;}
@media(max-width:700px) {.hero h1{font-size:31px}.panel{padding:14px}}
"""


with gr.Blocks() as demo:
    gr.HTML("""
    <div class="header">
      <div class="brand">PLUTO<span>.</span> / PROPULSION CHECK</div>
      <div class="online">● INTERFACE ONLINE</div>
    </div>
    <div class="hero">
      <div class="hero-label">PRE-FLIGHT SAFETY SYSTEM</div>
      <h1>Ready before takeoff.</h1>
      <p>Inspect your Pluto drone's propeller installation using computer vision.</p>
    </div>
    """)

    with gr.Row(equal_height=False):
        with gr.Column(scale=1, elem_classes=["panel"]):
            gr.HTML("""
            <div class="panel-title">Drone image</div>
            <div class="panel-subtitle">Upload a clear image of the drone.</div>
            """)
            input_image = gr.Image(
                label="Upload image",
                type="numpy",
                sources=["upload"],
                height=320,
            )
            with gr.Row():
                verify_button = gr.Button(
                    "Verify installation",
                    variant="primary",
                    elem_classes=["primary-button"],
                    scale=3,
                )
                clear_button = gr.Button("Clear", scale=1)

        with gr.Column(scale=1, elem_classes=["panel"]):
            gr.HTML("""
            <div class="panel-title">Annotated inspection image</div>
            <div class="panel-subtitle">YOLO detections and verification annotations.</div>
            """)
            output_image = gr.Image(
                label="Processed image",
                type="numpy",
                height=320,
                interactive=False,
            )

    with gr.Column(elem_classes=["panel"]):
        gr.HTML("""
        <div class="panel-title">Verification report</div>
        <div class="panel-subtitle">Detection summary, defects and correction guidance.</div>
        """)
        initial_report = {
            "status": "UNABLE TO VERIFY",
            "summary": "The backend engines have not been connected yet.",
            "detections": {},
            "errors": [],
        }
        status_output = gr.HTML(value=_status_card(initial_report))
        report_output = gr.HTML(value=_report_html(initial_report))

    gr.HTML("""
    <div class="safety">
      <strong>Safety reminder:</strong> Keep the drone disarmed and its motors stopped
      during inspection. An unclear image or uncertain detection must never produce PASS.
    </div>
    <div class="footer">
      <strong>PLUTO PROPULSION CHECK</strong><br>
      Computer Vision Based Propeller Installation Verification · Synergy 2026
    </div>
    """)

    verify_button.click(
        fn=verify_image,
        inputs=[input_image],
        outputs=[output_image, status_output, report_output],
    )
    clear_button.click(
        fn=clear_all,
        inputs=[],
        outputs=[input_image, output_image, status_output, report_output],
    )


if __name__ == "__main__":
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", "10000")),
        share=False,
        theme=gr.themes.Base(primary_hue="blue", neutral_hue="slate"),
        css=CSS,
    )
