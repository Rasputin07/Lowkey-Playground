"""Central configuration. Everything comes from environment variables / .env."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # python-dotenv is optional
    pass

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = os.getenv("LOWKEY_DB_PATH", str(BASE_DIR / "lowkey.db"))

# GenAI. The key lives ONLY on the backend. If it is empty the app still runs
# in a clearly labelled offline-demo mode (template answers, no LLM call).
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
GENAI_MODEL = os.getenv("GENAI_MODEL", "claude-sonnet-5-5")
GENAI_MAX_TOKENS = int(os.getenv("GENAI_MAX_TOKENS", "1200"))
GENAI_TIMEOUT_S = float(os.getenv("GENAI_TIMEOUT_S", "30"))

# Frontend origins allowed to call the API (comma separated).
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5500,http://localhost:5500",
    ).split(",")
    if o.strip()
]
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
