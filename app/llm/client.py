import os
import json
from openai import OpenAI

class LLMClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("GROQ_API_KEY"), 
            base_url="https://api.groq.com/openai/v1"
        )

    def process_user_message(self, history: list, system_prompt: str):
        messages = [{"role": "system", "content": system_prompt}] + history

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile", 
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.0
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"LLM Error: {e}")
            return {
                "action": "clarify", 
                "items": [], 
                "message_to_user": "I am having trouble connecting to the brain. Please try again."
            }