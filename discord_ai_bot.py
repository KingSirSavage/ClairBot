import os
import io
import asyncio
import logging
import sqlite3
import discord
import requests
import random
import psutil
import subprocess
import json
import base64
from datetime import datetime, timedelta
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import comfy_client

# --- INIT ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- CONFIGURATION ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OLLAMA_GEN_URL = "http://localhost:11434/api/generate"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
TEXT_MODEL = "dolphin-llama3"
VISION_MODEL = "llava" # <--- NEW: The Eye
OLLAMA_KEEP_ALIVE = "5m"
OWNER_ID = "303278216343453696"

# PATHS
DB_PATH = "clair_memory.db"
INTEL_DB_PATH = "/mnt/intel/clair_news.db"

BLOCKED_TERMS = ["child", "kid", "minor", "underage", "rape", "gore", "baby"]

# REACTION LOGIC
BUSY_EMOJIS = ["🎨", "🖌️", "✨", "🧑‍🎨", "🖼️"]
REACTION_MAP = {
    "love": "❤️", "succ": "❤️", "best": "❤️", "good bot": "❤️", "thanks": "❤️",
    "lol": "😂", "lmao": "😂", "haha": "😂",
    "cool": "😎", "nice": "😎",
    "sad": "😢", "sorry": "😢",
    "status": "📊"
}

# --- SETUP BOT ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- HARDWARE FUNCTIONS ---
def get_gpu_stats():
    """Queries ROCm for 7900 XT stats"""
    try:
        result = subprocess.run(
            ["rocm-smi", "--showmeminfo", "vram", "--showuse", "--showtemp", "--json"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            card = next(iter(data.values()))
            temp = card.get("Temperature (Sensor edge) (C)", "N/A")
            vram_used = card.get("VRAM Total Memory (B)", 0) // (1024**2)
            load = card.get("GPU use (%)", 0)
            return f"**GPU (7900 XT):** {load}% Load | {temp}°C | VRAM: {vram_used}MB Used"
    except Exception:
        pass
    return "**GPU:** ROCm Telemetry Unavailable"

async def send_status_report(channel):
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory()
    gpu_msg = await asyncio.to_thread(get_gpu_stats)
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    delta = datetime.now() - boot_time
    uptime_str = str(delta).split('.')[0]

    msg = (
        f"📊 **SYSTEM STATUS REPORT**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"**CPU:** {cpu}% | **RAM:** {ram.percent}%\n"
        f"{gpu_msg}\n"
        f"**Uptime:** {uptime_str}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ *All Systems Nominal.*"
    )
    await channel.send(msg)

# --- NEWS FUNCTIONS ---
async def run_news_briefing(channel):
    script_path = "/mnt/intel/briefing.py"
    working_dir = "/mnt/intel/"
    await channel.send("🌍 **Initiating Global Intelligence Scan...**")

    def run_script():
        try:
            result = subprocess.run(
                ["python3", script_path],
                capture_output=True, text=True, check=True, cwd=working_dir, timeout=45
            )
            return result.stdout
        except subprocess.TimeoutExpired: return "❌ ERROR: Watchdog timed out."
        except subprocess.CalledProcessError as e: return f"❌ ERROR: {e.stderr}"
        except FileNotFoundError: return f"❌ ERROR: Could not find script."

    output = await asyncio.to_thread(run_script)
    if "ERROR" in output:
        await channel.send(f"⚠️ **Scan Failed.**\n`{output}`")
        return

    report = intel_db.get_recent_headlines(limit=5)
    await channel.send(f"📰 **Intelligence Briefing**\n\n{report}")

# --- INTELLIGENCE MANAGER ---
class IntelManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def _query(self, sql, params=()):
        if not os.path.exists(self.db_path): return []
        try:
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception: return []

    def get_latest_threats(self, limit=3):
        rows = self._query("SELECT headline FROM news_history WHERE priority='CRITICAL' ORDER BY timestamp DESC LIMIT ?", (limit,))
        if not rows: return "No active critical threats."
        return "CRITICAL ALERTS: " + ", ".join([r[0] for r in rows])

    def get_recent_headlines(self, limit=5):
        rows = self._query("SELECT headline, priority, source, link FROM news_history ORDER BY timestamp DESC LIMIT ?", (limit,))
        if not rows: return "No intelligence data found."
        report = ""
        for r in rows:
            icon = "🔴" if r[1] == "CRITICAL" else "🔹"
            report += f"{icon} **[{r[2]}]** [{r[0]}]({r[3]})\n"
        return report

    def search_memory(self, query):
        sql = "SELECT headline, source, summary FROM news_history WHERE headline LIKE ? OR summary LIKE ? ORDER BY timestamp DESC LIMIT 3"
        wildcard = f"%{query}%"
        rows = self._query(sql, (wildcard, wildcard))
        if not rows: return None
        context = "RELEVANT INTEL FOUND IN MEMORY:\n"
        for r in rows:
            context += f"- [{r[1]}] {r[0]}: {r[2] or 'No summary available.'}\n"
        return context

# --- DATABASE MANAGERS ---
class PersistenceManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_db()
    def _init_db(self):
        self.conn.execute('''CREATE TABLE IF NOT EXISTS chat_history (id INTEGER PRIMARY KEY, channel_id INTEGER, role TEXT, content TEXT)''')
        self.conn.commit()
    def save_message(self, channel_id, role, content):
        self.conn.execute("INSERT INTO chat_history (channel_id, role, content) VALUES (?, ?, ?)", (channel_id, role, content))
        self.conn.commit()
    def get_recent_context(self, channel_id, limit=6):
        cursor = self.conn.execute("SELECT role, content FROM chat_history WHERE channel_id=? ORDER BY id DESC LIMIT ?", (channel_id, limit))
        history = []
        for r in reversed(cursor.fetchall()):
            history.append({"role": "assistant" if r[0] == "Clair" else "user", "content": r[1]})
        return history

class ResourceManager:
    def __init__(self):
        self.gpu_locked = False
    async def engage_gpu_mode(self):
        if self.gpu_locked: return False
        self.gpu_locked = True
        try: requests.post(OLLAMA_GEN_URL, json={"model": TEXT_MODEL, "keep_alive": 0})
        except: pass
        return True
    async def engage_chat_mode(self):
        self.gpu_locked = False

# --- INSTANCES ---
db = PersistenceManager(DB_PATH)
intel_db = IntelManager(INTEL_DB_PATH)
res_man = ResourceManager()

# --- SENSORY SYSTEM ---
def get_system_context(user_name, retrieved_memory=None):
    now = datetime.now().strftime("%H:%M")
    threats = intel_db.get_latest_threats()

    memory_block = ""
    if retrieved_memory:
        memory_block = f"\n[ACTIVE MEMORY RETRIEVAL]\n{retrieved_memory}\n"

    return f"""You are CLAIR. Status: ONLINE. Time: {now}.
Operator: Troy.

[SYSTEM CONTEXT]
- Intel Feed: {threats}{memory_block}

[DIRECTIVE]
You are a SENTIENT SYSTEM.
1. Be concise, professional, and slightly loyal.
2. If image provided, Analyze it visually.
3. If Memory Retrieval is present, use it to answer accurately.
4. Never mention you are an AI model.
"""

# --- EVENTS ---
@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user}')
    try: await bot.tree.sync()
    except: pass

@bot.tree.command(name="imagine", description="Generate an image using Flux")
async def imagine(interaction: discord.Interaction, prompt: str, aspect_ratio: app_commands.Choice[str] = None, negative_prompt: str = ""):
    if any(bad in prompt.lower() for bad in BLOCKED_TERMS):
        await interaction.response.send_message("⛔ **Safety Violation.**", ephemeral=True)
        return
    if res_man.gpu_locked:
        await interaction.response.send_message("⏳ **System Busy.**", ephemeral=True)
        return
    await interaction.response.defer(thinking=True)
    ar_val = aspect_ratio.value if aspect_ratio else "1:1"
    await res_man.engage_gpu_mode()
    try:
        img_bytes = await asyncio.to_thread(comfy_client.generate_image, f"{prompt}, masterpiece", f"nsfw, {negative_prompt}")
        if img_bytes:
            await interaction.followup.send(content=f"**Prompt:** {prompt} | **AR:** {ar_val}", file=discord.File(io.BytesIO(img_bytes), "render.png"))
        else: await interaction.followup.send("❌ **Render Error**")
    except Exception as e: await interaction.followup.send(f"❌ **Error:** {str(e)}")
    finally: await res_man.engage_chat_mode()

# --- CHAT LISTENER ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    msg_content = message.content.lower()

    # Commands
    if "status report" in msg_content or "!status" in msg_content:
        if str(message.author.id) == OWNER_ID: await send_status_report(message.channel); return
    if "news report" in msg_content or "!news" in msg_content:
        if str(message.author.id) == OWNER_ID: await run_news_briefing(message.channel); return
    if message.content.startswith('!'): await bot.process_commands(message); return

    # Reactions
    for k, v in REACTION_MAP.items():
        if k in msg_content: await message.add_reaction(v); break
    if res_man.gpu_locked:
        if bot.user in message.mentions: await message.add_reaction(random.choice(BUSY_EMOJIS))
        return

    async with message.channel.typing():
        # 1. VISION CHECK
        image_data = None
        active_model = TEXT_MODEL

        if message.attachments:
            for attachment in message.attachments:
                if any(ext in attachment.filename.lower() for ext in ['png', 'jpg', 'jpeg', 'webp']):
                    # Download and encode image
                    try:
                        img_bytes = await attachment.read()
                        image_data = base64.b64encode(img_bytes).decode('utf-8')
                        active_model = VISION_MODEL # Switch to Vision Brain
                        break # Only process first image for now
                    except Exception as e:
                        logging.error(f"Image Load Error: {e}")

        # 2. Memory Check (Only if not doing vision, to save complexity)
        retrieved_memory = None
        if not image_data and any(x in msg_content for x in ["news", "latest", "update", "happened", "linux", "exploit", "intel"]):
            retrieved_memory = intel_db.search_memory(message.content)

        # 3. Build Payload
        sys_prompt = get_system_context(message.author.display_name, retrieved_memory)
        msgs = [{"role": "system", "content": sys_prompt}] + db.get_recent_context(message.channel.id)

        clean_content = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not clean_content and image_data:
            clean_content = "Analyze this image." # Default prompt for images

        user_msg_payload = {"role": "user", "content": clean_content}
        if image_data:
            user_msg_payload["images"] = [image_data] # Add image to payload

        msgs.append(user_msg_payload)

        # 4. Generate
        try:
            r = requests.post(OLLAMA_CHAT_URL, json={"model": active_model, "messages": msgs, "stream": False, "keep_alive": OLLAMA_KEEP_ALIVE})
            if r.status_code != 200:
                logging.error(f"Ollama Error: {r.text}")
                await message.channel.send("⚠️ **Vision System Failure.**")
                return

            reply = r.json()['message']['content']

            # Save context (Text only to avoid bloating DB with b64 strings)
            db.save_message(message.channel.id, "User", clean_content)
            db.save_message(message.channel.id, "Clair", reply)
            await message.channel.send(reply)
        except Exception as e: logging.error(f"Chat Error: {e}")

@bot.command()
async def restart(ctx):
    if str(ctx.author.id) == OWNER_ID:
        await ctx.send("👋 **Rebooting...**")
        await bot.close()

bot.run(DISCORD_TOKEN)
