# 1. Base Image: A lightweight Linux with Python 3.11 pre-installed
FROM python:3.11-slim

# 2. Setup Environment Variables
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files (useless in containers)
# PYTHONUNBUFFERED: Ensures logs show up immediately in your terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Create the working directory inside the container
WORKDIR /app

# 4. Install Dependencies
# We copy ONLY requirements first. This caches the layer.
# If you change your code but not your requirements, Docker won't re-download pip packages.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the application code
COPY . .

# 6. The "Main Guard" Command
CMD ["python", "discord_ai_bot.py"]
