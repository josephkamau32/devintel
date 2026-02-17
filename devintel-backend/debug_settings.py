import os
import traceback
import sys
from dotenv import load_dotenv

# Redirect heavy output to a file
with open("debug_log.txt", "w", encoding="utf-8") as f:
    sys.stdout = f
    sys.stderr = f

    load_dotenv()

    print(f"DATABASE_URL in env: {os.environ.get('DATABASE_URL')}")
    print(f"Current working directory: {os.getcwd()}")

    try:
        from app.core.config import settings
        print(settings.model_dump())
        print("Settings loaded successfully")
    except Exception as e:
        print("Error loading settings:")
        traceback.print_exc()
