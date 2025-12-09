McDonald's AI Ordering Simulator

A CLI-based ordering simulator using OpenAI/Groq LLM APIs via FastAPI.

Overview

This application simulates a McDonald's ordering kiosk in the command line. It uses a Large Language Model (LLM) to process natural language requests, manage the order state, handle complex logic like "Double Deals" and upsells, and generate a final receipt.

Features

Natural Language Processing: Order items using free text (e.g., "I want a Big Mac without onions").

Dynamic Menu Validation: All items are validated against a YAML-based menu structure.

Business Logic:

Combos/Meals: Automatically handles upgrades to meals.

Upsells: Smart logic to offer drinks, sides, or desserts based on current cart content.

Double Deals: Automatically applies 20% discount when specific pairs of burgers are ordered.

Client-Server Architecture: - Server: FastAPI (REST API)

Client: Asynchronous Python CLI app

Prerequisites

Python 3.12+

Poetry (Dependency Manager)

Docker (Optional, for containerized execution)

Configuration

Create a .env file in the app/ directory (or use the provided example):

touch app/.env


Add your LLM API Key to app/.env:

For Groq (Recommended for speed)
GROQ_API_KEY=gsk_...

OR for OpenAI
OPENAI_API_KEY=sk-...


Installation & Running (Local)

Install Dependencies:

poetry install


Run the Application:
We provide a launcher script that handles both the server and client processes automatically.

poetry run python launcher.py


Installation & Running (Docker)

Build and Start the Server:

docker-compose up --build


You should see 🚀 Server running on http://0.0.0.0:8000.

Run the Client:
Open a new terminal window and run the client locally (it will connect to the Docker container):

python -m app.client_app


