from ollama_client import MedGemmaChat

bot = MedGemmaChat()

print("MedGemma Chatbot Ready (type 'exit' to quit)\n")

while True:
    user = input("You: ")

    if user.lower() == "exit":
        break

    reply = bot.send_message(user)
    print("Bot:", reply, "\n")