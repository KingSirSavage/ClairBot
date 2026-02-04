FROM python:3.11-slim

# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Add the SRE sensory library
RUN pip install discord.py python-dotenv requests aiohttp psutil

# Copy the app
COPY . .

# Run the SRE Bot
CMD ["python", "discord_ai_bot.py"]
