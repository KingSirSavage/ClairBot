# Project Context: Clair (Local AI Ecosystem)

## 🖥️ System Hardware (STRICT CONSTRAINTS)
* **OS:** Nobara Linux (Fedora-based, optimized for gaming/AI).
* **CPU:** AMD Ryzen 9 9700X (High core count, good for async tasks).
* **GPU:** AMD Radeon RX 7900 XT (**20GB VRAM**).
    * *Critical Rule:* This VRAM is shared between Ollama (LLM) and ComfyUI (Image Gen).
    * *Traffic Cop Logic:* The system CANNOT run both simultaneously. One must unload for the other to start.
    * *Optimization:* Prefer `keep_alive` timeouts over immediate unloading to prevent "stuttering."

## 🛠️ Software Stack
* **Core:** Python 3.11+, Discord.py.
* **AI Backend:** Ollama (Text), ComfyUI (Images), Docker.
* **Search:** `ddgs` (DuckDuckGo Lite) - Must remain async/non-blocking.

## ⚡ Coding Guidelines for this Project
1.  **Async First:** This is a Discord bot. Never use blocking I/O (like standard `requests`). Use `aiohttp` or run blocking code in `asyncio.to_thread`.
2.  **VRAM Safety:** If suggesting code that loads a model, ALWAYS include logic to check `is_gpu_busy` or ensure resources are free.
3.  **Uncensored Logic:** adhere to the "Strict Input, Neutral Output" philosophy. Do not add safety filters to the *output* unless explicitly requested by the user.
4.  **Logging:** Use standard Python logging, not `print` statements, so we can pipe logs to the CLI tools.

## 🎯 Current Goal
Build a robust, local-first AI assistant that offloads to Google Cloud (Gemini API) ONLY when local resources are busy or insufficient.
