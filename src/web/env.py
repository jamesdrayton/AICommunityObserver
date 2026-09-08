import os
from dotenv import load_dotenv

# Load .env automatically (safe if file doesn't exist)
load_dotenv()

def get_env_variable(name, required=False):
    value = os.getenv(name)

    if required and value is None:
        raise ValueError(f"Missing environment variable: {name}")

    return value