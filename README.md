McDonald's AI Ordering Simulator
A CLI-based ordering simulator using OpenAI/Groq LLM APIs via FastAPI.
Prerequisites
Python 3.12+
Poetry
Docker
Setup (Local)
1. Install Dependencies:
poetry install
2. Environment: Create app/.env file and add your API Key:
GROQ_API_KEY=gsk_...
# or
OPENAI_API_KEY=sk-...
3. Run: Use the launcher script to run both Server and Client:
poetry run python launcher.py
Setup (Docker)
1. Build and Run Server:
docker-compose up --build
2. Run Client (in a separate terminal): Since the client is interactive, run it locally
connecting to the Docker server:
# Make sure you have python installed locally for the client
python -m app.client_app
Alternatively, to run client inside docker:
docker run -it --network host mcdonalds-ai-simulator-server python -m app
