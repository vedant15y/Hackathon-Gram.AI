from google.cloud import translate_v2 as translate

client = translate.Client.from_service_account_json("key.json")

result = client.translate("नमस्कार", target_language="en")
print(result["translatedText"])