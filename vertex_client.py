import os

import vertexai
from vertexai.generative_models import GenerativeModel, Part


_MODEL = None


def get_model():
    global _MODEL
    if _MODEL is None:
        vertexai.init(
            project=os.getenv("VERTEX_PROJECT", "gramai2"),
            location=os.getenv("VERTEX_LOCATION", "asia-south1"),
        )
        _MODEL = GenerativeModel(os.getenv("VERTEX_MODEL", "gemini-1.5-flash"))
    return _MODEL


def generate_from_vertex(prompt: str):
    response = get_model().generate_content(prompt)
    return response.text


def analyze_image(image_bytes, mime_type="image/jpeg"):
    image_part = Part.from_data(
        mime_type=mime_type,
        data=image_bytes,
    )

    response = get_model().generate_content(
        [
            "You are a medical imaging AI. Analyze this image clinically.",
            image_part,
        ]
    )

    return response.text
