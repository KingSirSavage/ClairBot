# Clair: Autonomous Local AI Orchestrator

**Clair** is a self-hosted, multi-modal AI agent designed to run on consumer hardware with strict resource constraints. It integrates Large Language Models (Ollama) and Image Generation (ComfyUI/Flux) into a unified Discord interface.

## 🚀 The Engineering Challenge
Running **Flux (16GB VRAM)** and **Llama 3 (6GB VRAM)** simultaneously on a single 20GB GPU causes immediate Out-Of-Memory (OOM) crashes. 

## 🛠️ The Solution: "Traffic Cop" Protocol
I engineered a custom arbitration layer in Python (`discord_ai_bot.py`) that manages the GPU as a critical resource:

1.  **Global Locking:** Serializes requests to prevent race conditions.
2.  **Dynamic Unloading:** Before an image generation task starts, the system hits the Ollama API with `keep_alive: 0` to force an immediate VRAM flush.
3.  **System Priority:** The service runs with a `Nice=-10` value via systemd to prioritize inference over OS background tasks.

## 💻 Tech Stack
* **Language:** Python 3.12+ (AsyncIO, Aiohttp)
* **LLM Backend:** Ollama (Dolphin-Llama3)
* **Image Backend:** ComfyUI (Flux Dev)
* **Interface:** Discord API (`discord.py`)
* **OS:** Nobara Linux (Fedora-based)

## 🔧 Setup
*Secrets are managed via `.env` (excluded from repo).*
