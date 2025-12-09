from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from uuid import uuid4
from typing import Dict

from app.config import settings
from app.core.chat_engine import ChatEngine
from app.core.models import ChatRequest, ChatResponse, StartSessionResponse

sessions: Dict[str, ChatEngine] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Server starting...")
    yield
    sessions.clear()
    print("🛑 Server shutting down...")

app = FastAPI(title="McDonald's AI Simulator", lifespan=lifespan)

@app.post("/start", response_model=StartSessionResponse)
async def start_session():
    session_id = str(uuid4())
    engine = ChatEngine()
    greeting = engine.start_session()
    sessions[session_id] = engine
    return StartSessionResponse(session_id=session_id, message=greeting)

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id
    if session_id not in sessions:
        return ChatResponse(
            response_text="Session has ended. Please restart the client to order again.",
            is_finished=True
        )
    
    engine = sessions[session_id]
    response = await engine.process_message(request.message)
    
    if response.is_finished:
        sessions.pop(session_id, None)
        
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.server:app", host=settings.HOST, port=settings.PORT, reload=True)