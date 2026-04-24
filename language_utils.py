import html
import os

from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
from langdetect import detect


def _build_translate_client():
    key_path = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS",
        "C:/Users/Vrushali Gondhali/Desktop/keys/gcloud-key.json",
    )
    try:
        if os.path.exists(key_path):
            credentials = service_account.Credentials.from_service_account_file(key_path)
            return translate.Client(credentials=credentials)
        return translate.Client()
    except Exception:
        return None


translate_client = _build_translate_client()


def detect_language(text: str) -> str:
    try:
        return detect(text)
    except Exception:
        return "unknown"


def transliterate_text(text: str, lang: str) -> str:
    try:
        if lang in ["mr", "hi"]:
            return transliterate(text, sanscript.DEVANAGARI, sanscript.ITRANS)
        return text
    except Exception:
        return text


def translate_to_english(text: str) -> str:
    try:
        if translate_client is None:
            return text
        result = translate_client.translate(text, target_language="en")
        return html.unescape(result["translatedText"])
    except Exception:
        return text


def translate_back(text: str, target_lang: str) -> str:
    try:
        if translate_client is None:
            return text
        result = translate_client.translate(text, target_language=target_lang)
        return html.unescape(result["translatedText"])
    except Exception:
        return text


def process_input(text: str):
    lang = detect_language(text)
    transliterated = transliterate_text(text, lang)

    if lang != "en":
        english_text = translate_to_english(text)
    else:
        english_text = text

    return {
        "lang": lang,
        "transliterated": transliterated,
        "english": english_text,
    }


def process_output(response_text: str, lang: str):
    return response_text
