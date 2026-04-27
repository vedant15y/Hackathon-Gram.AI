import os

import vertexai
from vertexai.generative_models import GenerativeModel, Part


_MODEL = None
_MODEL_NAME = None


def _candidate_models():
    preferred = os.getenv("VERTEX_MODEL", "gemini-2.5-flash")
    fallbacks = [
        "gemini-2.5-flash",
        "gemini-2.0-flash-001",
        "gemini-1.5-flash-002",
        "gemini-1.5-pro-002",
    ]
    ordered = [preferred] + [name for name in fallbacks if name != preferred]
    return ordered


def _init_vertex():
    vertexai.init(
        project=os.getenv("VERTEX_PROJECT", "gramai2"),
        location=os.getenv("VERTEX_LOCATION", "asia-south1"),
    )


def _generate_with_candidate(model_name: str, contents):
    model = GenerativeModel(model_name)
    response = model.generate_content(contents)
    return model, response


def get_model():
    global _MODEL, _MODEL_NAME
    if _MODEL is not None:
        return _MODEL

    _init_vertex()

    last_error = None
    for model_name in _candidate_models():
        try:
            model, _ = _generate_with_candidate(model_name, "Reply with only OK")
            _MODEL = model
            _MODEL_NAME = model_name
            print(f"Using Vertex model: {_MODEL_NAME}")
            return _MODEL
        except Exception as exc:
            last_error = exc
            print(f"Vertex model unavailable: {model_name}: {exc}")

    raise RuntimeError(f"No usable Vertex model found. Last error: {last_error}")


def generate_from_vertex(prompt: str):
    model = get_model()
    response = model.generate_content(prompt)
    return response.text


def analyze_image(image_bytes, mime_type="image/jpeg"):
    model = get_model()
    image_part = Part.from_data(
        mime_type=mime_type,
        data=image_bytes,
    )

    response = model.generate_content(
        [
            "You are a medical imaging AI. Analyze this image clinically.",
            image_part,
        ]
    )

    return response.text
