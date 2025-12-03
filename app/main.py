import os
from dotenv import load_dotenv

load_dotenv()

from app.core.chat_engine import ChatEngine

def main():
    engine = ChatEngine()
    engine.start()

if __name__ == "__main__":
    main()
