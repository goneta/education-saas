import sys
import os

# Add current CWD to sys.path explicitly just in case
sys.path.append(os.getcwd())

print("Sys Path:", sys.path)

try:
    print("Attempting to import backend.main...")
    from backend.main import app
    print("Success importing backend.main")
except Exception as e:
    import traceback
    traceback.print_exc()
