from openai import OpenAI
client = OpenAI()

completion = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "user", "content": "What is the difference between Celsius and Fahrenheit?"}
  ]
)

print(completion)