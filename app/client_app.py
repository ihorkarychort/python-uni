import asyncio
import httpx
import sys
from aioconsole import ainput, aprint
from app.config import settings

SERVER_URL = f"http://{settings.HOST}:{settings.PORT}"

async def send_message_task(client: httpx.AsyncClient, session_id: str, text: str):
    try:
        response = await client.post(
            f"{SERVER_URL}/chat",
            json={"session_id": session_id, "message": text}
        )
        response.raise_for_status()
        result = response.json()
        
        reply = result.get("response_text", "").strip()
      
        if not reply and not result.get("is_finished"):
            return False
        
        await aprint(f"\n🤖 System: {reply}")
        
        if result.get("is_finished"):
            await aprint("\n🧾 Final Receipt:")
            await aprint(result.get("order_summary"))
            await aprint(f"💰 Total: ${result.get('total_price', 0.0):.2f}")
            await aprint("\n(Press Enter to exit)")
            return True

    except httpx.HTTPError as e:
        await aprint(f"\n❌ Server Error: {e}")
    except Exception as e:
        await aprint(f"\n❌ Connection Error: {e}")
    
    return False

async def run_client():
    print("Connecting to server...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(f"{SERVER_URL}/start")
            resp.raise_for_status()
            data = resp.json()
            session_id = data["session_id"]
            print(f"🤖 System: {data['message']}")
        except Exception as e:
            print(f"❌ Error connecting to server: {e}")
            return

        print("\n💡 Tip: You can type freely. Status '⏳' means we are working on it.")
        print("   Type 'exit' to quit.\n")

        while True:
            try:
                user_text = await ainput("You: ")
                
                if not user_text.strip():
                    continue
                
                if user_text.lower() in ["exit", "quit"]:
                    print("Bye!")
                    break

                print(f"   ⏳ Processing '{user_text[:15]}...'") 

                asyncio.create_task(
                    send_message_task(client, session_id, user_text)
                )

            except KeyboardInterrupt:
                print("\nBye!")
                break
            except Exception as e:
                print(f"Error: {e}")
                break

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(run_client())
    except KeyboardInterrupt:
        pass