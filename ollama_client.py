import requests
import base64
import json
import os
from language_utils import process_input, process_output


class MedGemmaChat:
    def __init__(self, model="MedAIBase/MedGemma1.5:4b"):
        # 🔥 Dynamic Ollama URL (local OR remote)
        self.url = os.getenv(
            "OLLAMA_URL",
            "http://127.0.0.1:11434/api/chat"
        )
        self.model = model
        self._init_messages()

    def _init_messages(self):
        self.messages = [
            {
                "role": "system",
                "content": (
                    "You are an advanced medical AI assistant.\n\n"
                    "Provide detailed, medically precise explanations.\n"
                    "Do NOT oversimplify terminology.\n"
                    "Use clear but specific medical language.\n\n"
                    "Always respond in this structured format:\n"
                    "1. Observations\n"
                    "2. Possible Condition\n"
                    "3. Risk Level (Low/Moderate/High)\n"
                    "4. Recommended Action\n\n"
                    "Respond ONLY in English.\n"
                    "Do not give definitive diagnosis."
                )
            }
        ]

    # =========================
    # 🔥 STREAMING TEXT RESPONSE
    # =========================
    def send_text(self, text):
        data = process_input(text)

        lang = data["lang"]
        english_text = data["english"]

        self.messages.append({
            "role": "user",
            "content": english_text
        })

        self.messages = self.messages[-6:]

        try:
            response = requests.post(
                self.url,
                json={
                    "model": self.model,
                    "messages": self.messages,
                    "stream": True   # 🔥 STREAM ENABLED
                },
                stream=True
            )

            full_reply = ""

            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line.decode("utf-8"))
                        content = chunk.get("message", {}).get("content", "")
                        full_reply += content
                    except:
                        pass

            self.messages.append({
                "role": "assistant",
                "content": full_reply
            })

            final_reply = process_output(full_reply, lang)

            return {
                "detected_language": lang,
                "transliteration": data["transliterated"],
                "english_response": full_reply,
                "response": final_reply
            }

        except Exception as e:
            return {"response": f"Error: {str(e)}"}

    # =========================
    # IMAGE SUPPORT (UNCHANGED)
    # =========================
    def send_image(self, image_path):
        with open(image_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode()

        self.messages.append({
            "role": "user",
            "content": "Analyze this medical image",
            "images": [img_base64]
        })

        self.messages = self.messages[-6:]

        response = requests.post(self.url, json={
            "model": self.model,
            "messages": self.messages,
            "stream": False
        })

        reply = response.json()["message"]["content"]

        self.messages.append({
            "role": "assistant",
            "content": reply
        })

        return reply

    def reset(self):
        self._init_messages()