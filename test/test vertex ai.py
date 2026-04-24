import vertexai
from vertexai.generative_models import GenerativeModel

vertexai.init(project="GramAi2", location="asia-south1")

model = GenerativeModel("gemini-1.5-flash")
print(model.generate_content("Hello").text)