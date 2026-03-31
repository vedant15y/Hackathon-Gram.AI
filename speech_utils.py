from google.cloud import speech

def transcribe_audio(file_path):
    client = speech.SpeechClient()

    with open(file_path, "rb") as f:
        audio_content = f.read()

    audio = speech.RecognitionAudio(content=audio_content)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-IN",  # change if needed
    )

    response = client.recognize(config=config, audio=audio)

    text = ""
    for result in response.results:
        text += result.alternatives[0].transcript

    return {
        "text": text,
        "language": "en-IN"
    }