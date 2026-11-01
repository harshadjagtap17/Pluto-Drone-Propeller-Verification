
import os
import gradio as gr
import cv2
import numpy as np


def verify_installation(image):

    if image is None:
        return (
            None,
            "### UNABLE TO VERIFY",
            "Please upload a drone image."
        )

    # Placeholder until Member 1 and Member 3
    # provide their actual functions.

    annotated_image = image.copy()

    result = """
    ### UNABLE TO VERIFY

    Detection and verification modules
    are not integrated yet.
    """

    instructions = """
    Please wait for the verification
    modules to be integrated.
    """

    return annotated_image, result, instructions


with gr.Blocks(
    title="Pluto Drone Verification"
) as app:

    gr.Markdown(
        """
        # Pluto Drone Propeller Verification

        Upload an image to verify propeller installation.
        """
    )

    with gr.Row():

        input_image = gr.Image(
            label="Upload Drone Image",
            type="numpy"
        )

        output_image = gr.Image(
            label="Annotated Image",
            type="numpy"
        )

    verify_button = gr.Button(
        "Verify Installation",
        variant="primary"
    )

    result_output = gr.Markdown(
        "Waiting for image..."
    )

    instructions_output = gr.Markdown()

    verify_button.click(
        fn=verify_installation,
        inputs=input_image,
        outputs=[
            output_image,
            result_output,
            instructions_output
        ]
    )


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 7860))

    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False
    )

