"""Settings read from environment variables (filled from the .env file by Docker Compose)."""

import os

# PostgreSQL connection string for the Supabase database
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# e.g. https://abcdefgh.supabase.co, used to check login tokens
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")

# Websites allowed to call this API from the browser, comma-separated
# (online the website and the API have different addresses, e.g. https://ear-training.onrender.com).
# Not needed in development, where Vite forwards /api to the backend.
FRONTEND_ORIGINS = [o.strip() for o in os.environ.get("FRONTEND_ORIGINS", "").split(",") if o.strip()]

# Folder with the original WAV piano samples (used to mix competition audio on the server)
SOUNDS_DIR = os.environ.get("SOUNDS_DIR", "/sounds")

# Only needed for older Supabase projects that still sign tokens with the "legacy JWT secret"
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")
