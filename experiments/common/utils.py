import time
import yaml
import os

def load_config(file_path):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

def wait_for_recycle(minutes=30):
    """
    Wait for Lambda instances to be recycled.
    """
    print(f"Waiting for {minutes} minutes for instances to be recycled...")
    time.sleep(minutes * 60)
