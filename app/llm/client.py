from openai import AsyncOpenAI
from app.config import settings 
from app.core.models import LLMResponse

class LLMClient:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY or settings.OPENAI_API_KEY,
            base_url=settings.LLM_BASE_URL
        )

    async def process_user_message(self, history: list, system_prompt: str) -> LLMResponse:
        messages = [{"role": "system", "content": system_prompt}] + history

        try:
            response = await self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.0
            )
            
            content = response.choices[0].message.content
            return LLMResponse.model_validate_json(content)
        except Exception as e:
            print(f"LLM Error: {e}")
            return LLMResponse(
                action="clarify",
                message_to_user="I am having trouble connecting to the brain. Please try again."
            )