import websocket
import uuid
import json
import urllib.request
import urllib.parse
import random
import time

SERVER_ADDRESS = "127.0.0.1:8189"
CLIENT_ID = str(uuid.uuid4())

def queue_prompt(prompt_workflow):
    p = {"prompt": prompt_workflow, "client_id": CLIENT_ID}
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

def generate_image(positive_text, negative_text=""):
    try:
        # JUGGERNAUT LIGHTNING WORKFLOW (Speed + Quality)
        workflow = {
            "3": {
                "inputs": {
                    "seed": random.randint(1, 1000000000000),
                    "steps": 6,            # Lightning needs only 4-8 steps
                    "cfg": 2.0,            # Low CFG is critical for Lightning (1.5 - 2.0)
                    "sampler_name": "dpmpp_sde", # SDE is best for Lightning
                    "scheduler": "karras",
                    "denoise": 1.0,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0]
                },
                "class_type": "KSampler",
                "_meta": {"title": "KSampler"}
            },
            "4": {
                "inputs": {
                    "ckpt_name": "juggernaut_lightning.safetensors"
                },
                "class_type": "CheckpointLoaderSimple",
                "_meta": {"title": "Load Checkpoint"}
            },
            "5": {
                "inputs": {
                    "width": 1024,
                    "height": 1024,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage",
                "_meta": {"title": "Empty Latent Image"}
            },
            "6": {
                "inputs": {
                    "text": positive_text + ", masterpiece, cinematic lighting, 8k, highly detailed",
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Positive)"}
            },
            "7": {
                "inputs": {
                    "text": "worst quality, low quality, bad anatomy, blur, noisy, distorted", 
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Negative)"}
            },
            "8": {
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2]
                },
                "class_type": "VAEDecode",
                "_meta": {"title": "VAE Decode"}
            },
            "9": {
                "inputs": {
                    "filename_prefix": "Clair_Lightning",
                    "images": ["8", 0]
                },
                "class_type": "SaveImage",
                "_meta": {"title": "Save Image"}
            }
        }

        ws = websocket.WebSocket()
        ws.connect(f"ws://{SERVER_ADDRESS}/ws?clientId={CLIENT_ID}")
        
        prompt_id = queue_prompt(workflow)['prompt_id']
        
        while True:
            out = ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'executing':
                    data = message['data']
                    if data['node'] is None and data['prompt_id'] == prompt_id:
                        break 
        
        history = get_history(prompt_id)[prompt_id]
        for node_id in history['outputs']:
            node_output = history['outputs'][node_id]
            if 'images' in node_output:
                for image in node_output['images']:
                    return get_image(image['filename'], image['subfolder'], image['type'])

    except Exception as e:
        print(f"Generate Error: {e}")
        return None
    return None
