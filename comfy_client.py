import websocket
import uuid
import json
import urllib.request
import urllib.parse
import random
import os

# Connect to Local ComfyUI
SERVER_ADDRESS = "127.0.0.1:8189"
CLIENT_ID = str(uuid.uuid4())

def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": CLIENT_ID}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"http://{SERVER_ADDRESS}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(f"http://{SERVER_ADDRESS}/view?{url_values}") as response:
        return response.read()

def get_history(prompt_id):
    with urllib.request.urlopen(f"http://{SERVER_ADDRESS}/history/{prompt_id}") as response:
        return json.loads(response.read())

def generate_image_from_text(user_prompt):
    """
    Loads the workflow, injects the user prompt + NSFW keywords,
    and returns the raw image bytes.
    """
    # 1. Load the JSON Workflow from the SAME folder as this script
    workflow_path = os.path.join(os.path.dirname(__file__), "workflow_api.json")

    if not os.path.exists(workflow_path):
        print(f"ERROR: workflow_api.json not found at {workflow_path}")
        return None

    with open(workflow_path, "r") as f:
        workflow = json.load(f)

# --- CHANGE 1: FLUX POSITIVE PROMPT ---
    # Flux prefers natural language. We add "photorealistic" and 8k.
    # We DO NOT force "uncensored" (let the user ask for it).
    full_prompt = (
        f"masterpiece, best quality, ultra high res, 8k uhd, photorealistic, "
        f"{user_prompt}"
    )
    workflow["6"]["inputs"]["text"] = full_prompt

    # --- CHANGE 2: FLUX NEGATIVE PROMPT (Minimalist) ---
    # Flux often ignores negatives, but we keep the Core Safety Blocklist.
    negative_prompt = (
        "child, underage, kid, baby, toddler, loli, teen, preteen, "
        "worst quality, bad anatomy, watermark"
    )
    workflow["7"]["inputs"]["text"] = negative_prompt

    # Randomize Seed (Node 3)
    workflow["3"]["inputs"]["seed"] = random.randint(1, 1000000000)

    # 3. Connect to WebSocket
    try:
        ws = websocket.WebSocket()
        ws.connect(f"ws://{SERVER_ADDRESS}/ws?clientId={CLIENT_ID}")
    except Exception as e:
        print(f"ComfyUI Connection Failed: {e}")
        return None

    # 4. Queue the Prompt
    try:
        prompt_response = queue_prompt(workflow)
        prompt_id = prompt_response['prompt_id']
    except Exception as e:
        print(f"Failed to queue prompt: {e}")
        return None

    # 5. Wait for Completion
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break # Execution is done
        else:
            continue

    # 6. Retrieve Image
    history = get_history(prompt_id)[prompt_id]
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        if 'images' in node_output:
            for image in node_output['images']:
                image_data = get_image(image['filename'], image['subfolder'], image['type'])
                return image_data
    return None
