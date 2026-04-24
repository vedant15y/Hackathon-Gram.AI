from google.cloud import translate_v2 as translate

client = translate.Client()
print(client.translate("Hello", target_language="hi"))