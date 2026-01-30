# ClairBot

ClairBot is a powerful, local-first AI assistant designed for Discord, leveraging cutting-edge AI models and sophisticated resource management. It provides advanced text generation, image creation, and integrated web search capabilities, all while optimizing local hardware.

## Badges

[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-enabled-0db7ed.svg)](https://www.docker.com/)

## System Architecture

ClairBot is architected for efficient operation on local hardware, with a strong emphasis on VRAM management for GPU-intensive AI tasks.

*   **Hardware:** Designed to run on Linux-based systems (e.g., Nobara Linux) utilizing a powerful AMD Ryzen CPU and an AMD Radeon RX 7900 XT GPU with 20GB of VRAM.
*   **AI Backends:**
    *   **Ollama:** Powers text generation, running models like `dolphin-llama3`.
    *   **ComfyUI:** Handles image generation tasks.
*   **VRAM Traffic Cop:** A critical component manages the shared 20GB VRAM between Ollama and ComfyUI. The system ensures only one AI backend utilizes the GPU at a time, switching between modes to prevent conflicts and optimize performance. Ollama models are pre-loaded with `keep_alive` timeouts to minimize stuttering during transitions, while image generation tasks trigger an immediate unload of the text model to free VRAM.
*   **Search Integration:** Utilizes `ddgs` (DuckDuckGo Lite) for asynchronous, non-blocking web searches.
*   **Persistence:** Employs SQLite for chat history and user usage tracking.
*   **Payments & Roles:** Integrated with Stripe for handling subscriptions and one-time purchases, managing user roles within Discord.

## Installation

ClairBot is containerized using Docker, ensuring a consistent and isolated environment.

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd ClairBot
    ```

2.  **Create a `.env` file:**
    Create a file named `.env` in the root directory of the project and populate it with your sensitive credentials and configuration:

    ```dotenv
    DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN
    STRIPE_API_KEY=YOUR_STRIPE_SECRET_KEY
    STRIPE_WEBHOOK_SECRET=YOUR_STRIPE_WEBHOOK_SECRET
    # Add any other necessary environment variables here
    ```
    *Note: For Stripe, ensure you use test keys during development and set up a webhook endpoint.*

3.  **Build the Docker image:**
    ```bash
    docker build -t clairbot .
    ```

4.  **Run the Docker container:**
    ```bash
    docker run -d \
      --name clairbot \
      --env-file .env \
      -p 8080:8080 \
      -v $(pwd)/clair_memory.db:/app/clair_memory.db \
      clairbot
    ```
    *   `-d`: Run in detached mode.
    *   `--name clairbot`: Assign a name to the container.
    *   `--env-file .env`: Load environment variables from your `.env` file.
    *   `-p 8080:8080`: Map port 8080 for the Stripe webhook listener.
    *   `-v $(pwd)/clair_memory.db:/app/clair_memory.db`: Mount the SQLite database file to persist data.

## Features

*   **Advanced Chatbot:** Powered by Ollama, providing intelligent and uncensored conversational AI.
*   **High-Quality Image Generation:** Leverages ComfyUI for generating stunning visuals from text prompts.
*   **Real-time Web Search:** Integrates with DuckDuckGo for up-to-date information retrieval.
*   **VRAM Optimization:** Intelligent traffic cop logic for seamless switching between text and image AI models on your GPU.
*   **Subscription Management:** Integrated Stripe payment gateway for user upgrades and role management.
*   **Usage Limits:** Daily quotas for image generation and chat sessions, with VIP tiers offering higher limits.
*   **Persistent Memory:** Stores chat history and user data using SQLite.
*   **Discord Integration:** Native Discord bot functionality.
