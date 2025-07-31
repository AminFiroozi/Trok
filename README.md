
# TROK
## A Telegram Conversational Search Agent

This project provides an intelligent chatbot system for Telegram that allows users to perform descriptive and semantic searches within their own chat history. The system consists of two main bots and a Retrieval-Augmented Generation (RAG) core powered by a multi-agent system.

## Architecture & How It Works

The workflow is divided into three main components:

1.  **User-Facing Telegram Bot (`telegram_bot.py`)**:
    This is the primary interface for the end-user, built with `python-telegram-bot`. It manages the conversation flow, user authentication, and relays queries to the RAG system.

2.  **Message Scraper (CLI Bot)**:
    A command-line interface (CLI) bot is responsible for logging into a user's Telegram account (with their consent and credentials) to read and save their message history into a structured format (e.g., `all_messages.json`). This component acts as the data pipeline and is a prerequisite for the search functionality.

3.  **RAG & Multi-Agent System (`telegram_rag.py`)**:
    This is the core of the project, built using **AutoGen**. It processes the scraped chat history to enable intelligent search:
    -   It uses a `SentenceTransformer` model to convert messages into vector embeddings.
    -   These embeddings are stored in a **ChromaDB** vector database for efficient similarity search.
    -   When a query is received, a multi-agent system handles the request:
        -   An **Assistant Agent** retrieves the most relevant information from the vector store.
        -   A **Reviewer Agent** double-checks the assistant's findings for correctness and relevance before the final answer is generated.

## Key Technologies

-   **Telegram Bot Framework**: `python-telegram-bot`
-   **Agentic AI Framework**: `pyautogen`
-   **Vector Database**: `ChromaDB`
-   **Embeddings Model**: `Sentence-Transformers`

## How to Use

### 1. Setup
-   Install all dependencies:
    ```bash
    pip install -r requirements.txt
    ```
-   Place your Telegram Bot Token in `telegram_bot.py`.
-   Create and configure a `config.json` file with your LLM API keys.

### 2. Data Collection
-   Run the CLI scraper bot to fetch the user's chat history and create the `all_messages.json` file.

### 3. Run the System
-   The `telegram_rag.py` script can be run to process the JSON file, create embeddings, and answer queries in a standalone mode.
-   To start the main user-facing bot, run:
    ```bash
    python telegram_bot.py
    ```
