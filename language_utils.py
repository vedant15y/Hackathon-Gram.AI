from langdetect import detect
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

# Load credentials
credentials = service_account.Credentials.from_service_account_file(
    "translation_key.json"
)

translate_client = translate.Client(credentials=credentials)


def detect_language(text: str) -> str:
    try:
        return detect(text)
    except:
        return "unknown"


def transliterate_text(text: str, lang: str) -> str:
    try:
        if lang in ["mr", "hi"]:
            return transliterate(text, sanscript.DEVANAGARI, sanscript.ITRANS)
        return text
    except:
        return text


def translate_to_english(text: str) -> str:
    try:
        result = translate_client.translate(text, target_language="en")
        return result["translatedText"]
    except:
        return text


def translate_back(text: str, target_lang: str) -> str:
    try:
        result = translate_client.translate(text, target_language=target_lang)
        return result["translatedText"]
    except:
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
        "english": english_text
    }


def process_output(response_text: str, lang: str):
    if lang not in ["en", "unknown"]:
        return translate_back(response_text, lang)
    return response_text