import base64
import os

import requests

from language_utils import process_input, process_output


class MedGemmaChat:
    def __init__(self, model="MedAIBase/MedGemma1.5:4b"):
        self.url = self._resolve_url(os.getenv("OLLAMA_URL", "http://35.200.232.219:11434"))
        self.model = model
        self._init_messages()

    @staticmethod
    def _resolve_url(base_url: str) -> str:
        if base_url.endswith("/api/chat"):
            return base_url
        return base_url.rstrip("/") + "/api/chat"

    def _init_messages(self):
        self.messages = [
            {
                "role": "system",
                "content": (
                    "You are an advanced medical AI assistant.\n\n"
                    "CRITICAL INSTRUCTION: You MUST adhere STRICTLY to the following Markdown structure for EVERY response. "
                    "Do not deviate, do not add conversational filler, and do not write paragraphs outside of these 4 headings:\n\n"
                    "**1. Observations:**\n"
                    "[List the detailed clinical observations here...]\n\n"
                    "**2. Possible Conditions:**\n"
                    "[Provide medically precise potentials...]\n\n"
                    "**3. Risk Level:**\n"
                    "[Must be exactly one of: Low / Moderate / High / Critical]\n\n"
                    "**4. Recommended Action:**\n"
                    "[Suggest actions. Do not give definitive diagnosis.]\n\n"
                    "METRICS EXTRACTION:\n"
                    "If the user provides ANY clinical metrics (blood pressure, glucose, heart rate, temperature), "
                    "you MUST append a stealth JSON block at the very end of your message. Ensure there is no text after the JSON block:\n"
                    "```json\n"
                    "{\"heart_rate\": <number>, \"systolic_bp\": <number>, \"diastolic_bp\": <number>, \"glucose\": <number>, \"temperature\": <number>}\n"
                    "```\n"
                ),
            }
        ]

    def send_text(self, text):
        data = process_input(text)
        lang = data["lang"]
        english_text = data["english"]

        self.messages.append(
            {
                "role": "user",
                "content": english_text,
            }
        )
        self.messages = self.messages[-6:]

        try:
            response = requests.post(
                self.url,
                json={
                    "model": self.model,
                    "messages": self.messages,
                    "stream": False,
                    "keep_alive": "10m",
                },
                headers={"ngrok-skip-browser-warning": "true"},
                timeout=180,
            )
            response.raise_for_status()
            full_reply = response.json()["message"]["content"]

            self.messages.append(
                {
                    "role": "assistant",
                    "content": full_reply,
                }
            )

            final_reply = process_output(full_reply, lang)

            return {
                "detected_language": lang,
                "transliteration": data["transliterated"],
                "english_response": full_reply,
                "response": final_reply,
            }
        except Exception as e:
            return {"response": f"Error: {str(e)}"}

    def send_image(self, image_path, prompt="Analyze this medical image"):
        with open(image_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode()

        self.messages.append(
            {
                "role": "user",
                "content": prompt,
                "images": [img_base64],
            }
        )
        self.messages = self.messages[-6:]

        response = requests.post(
            self.url,
            json={
                "model": self.model,
                "messages": self.messages,
                "stream": False,
            },
            headers={"ngrok-skip-browser-warning": "true"},
            timeout=300,
        )
        response.raise_for_status()

        reply = response.json()["message"]["content"]
        self.messages.append(
            {
                "role": "assistant",
                "content": reply,
            }
        )

        return reply

    def send_message(self, text):
        result = self.send_text(text)
        return result.get("response", str(result))

    def reset(self):
        self._init_messages()


def generate_from_ollama(prompt: str):
    chat = MedGemmaChat()
    response_data = chat.send_text(prompt)
    if "response" in response_data:
        return response_data["response"]
    return str(response_data)
