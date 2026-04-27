import os
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


TEST_DB_PATH = Path(__file__).with_name("test_smoke.db")
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"

import server_fastapi
import database


class SmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_cm = TestClient(server_fastapi.app)
        cls.client = cls.client_cm.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_cm.__exit__(None, None, None)
        database.engine.dispose()
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()

    def test_health_and_home(self):
        health = self.client.get("/health")
        home = self.client.get("/")

        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json(), {"status": "ok"})
        self.assertEqual(home.status_code, 200)
        self.assertIn("text/html", home.headers.get("content-type", ""))

    def test_signup_and_login(self):
        email = f"test-{uuid.uuid4().hex[:8]}@example.com"
        password = "secret123"

        signup = self.client.post("/signup", json={"email": email, "password": password})
        login = self.client.post("/login", json={"email": email, "password": password})
        session_check = self.client.post(
            "/session",
            json={"token": login.json()["session_token"]},
        )

        self.assertEqual(signup.status_code, 200)
        self.assertEqual(signup.json()["status"], "success")
        self.assertIn("session_token", signup.json())
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.json()["status"], "success")
        self.assertIn("session_token", login.json())
        self.assertEqual(session_check.status_code, 200)
        self.assertEqual(session_check.json()["status"], "success")

    def test_stt_text(self):
        response = self.client.post("/stt-text", json={"text": "Hello doctor"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["english"], "Hello doctor")

    def test_chat_route(self):
        with patch("routers.chat.bot.send_text", return_value={"response": "ok reply"}):
            response = self.client.post(
                "/chat",
                json={"message": "hello", "user_id": 1, "patient_id": 1},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["response"], "ok reply")

    def test_chat_route_falls_back_to_vertex(self):
        with (
            patch("routers.chat.bot.send_text", side_effect=RuntimeError("vm timeout")),
            patch("routers.chat.generate_from_vertex", return_value="vertex fallback reply"),
        ):
            response = self.client.post(
                "/chat",
                json={"message": "hello", "user_id": 1, "patient_id": 1},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["response"], "vertex fallback reply")

    def test_metrics_stats(self):
        response = self.client.get("/metrics/stats")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("patients", payload)
        self.assertIn("interactions", payload)

    def test_tts_plain_text(self):
        with patch("routers.chat.text_to_speech", return_value="out.mp3"):
            response = self.client.post(
                "/tts",
                content="hello there",
                headers={"Content-Type": "text/plain"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("content-type"), "audio/mpeg")

    def test_analyze_image_with_mocks(self):
        with (
            patch("server_fastapi.analyze_image", return_value="safe image summary"),
            patch("server_fastapi.generate_from_ollama", return_value="structured response"),
        ):
            response = self.client.post(
                "/analyze-image",
                files={"file": ("scan.jpg", b"fake-image", "image/jpeg")},
                data={"text": "check this", "user_id": "1", "patient_id": "1"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["vertex_analysis"], "safe image summary")
        self.assertEqual(payload["final_response"], "structured response")

    def test_analyze_image_falls_back_to_vertex_when_ollama_down(self):
        with (
            patch("server_fastapi.analyze_image", return_value="safe image summary"),
            patch("server_fastapi.generate_from_ollama", side_effect=RuntimeError("vm timeout")),
            patch("server_fastapi.generate_from_vertex", return_value="vertex medical fallback"),
        ):
            response = self.client.post(
                "/analyze-image",
                files={"file": ("scan.jpg", b"fake-image", "image/jpeg")},
                data={"text": "check this", "user_id": "1", "patient_id": "1"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["vertex_analysis"], "safe image summary")
        self.assertEqual(payload["final_response"], "vertex medical fallback")


if __name__ == "__main__":
    unittest.main()
