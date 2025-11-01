from composio import Composio
from composio_openai import OpenAIProvider
from openai import OpenAI
from datetime import datetime

#composio use chat completion
# Use a unique identifier for each user in your application
user_id = "user-k7334" 

# Create composio client
composio = Composio(provider=OpenAIProvider(), api_key="your_composio_api_key")

# Create openai client
openai = OpenAI()

# Get Gmail tools for this user
tools = composio.tools.get(
  user_id=user_id,
  tools=["GMAIL_SEND_EMAIL"]
)

# Ask the LLM to send an email
result = openai.chat.completions.create(
  model="gpt-4o-mini",
  tools=tools,
  messages=[
      {"role": "system", "content": "You are a helpful email assistant. Send professional emails as requested."},
      {"role": "user", "content": "Send an email to recipient@example.com with subject 'Test Email from Composio' and body 'Hello, this is a test email sent using Composio and OpenAI integration. Best regards!'"}
  ]
)


# Handle tool calls
result = composio.provider.handle_tool_calls(user_id=user_id, response=result)
print(result)
