"""Settings read from environment variables (filled from the .env file by Docker Compose)."""

import os

# PostgreSQL connection string for the Supabase database
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# e.g. https://abcdefgh.supabase.co, used to check login tokens
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")

# Only needed for older Supabase projects that still sign tokens with the "legacy JWT secret"
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")
